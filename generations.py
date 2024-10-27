import PyPDF2
import boto3
import json
import fitz
from PIL import Image, ImageDraw, ImageFont
import random
import os
import re
from vertex_functions import generate, remove_code_blocks
from difflib import SequenceMatcher
from datetime import datetime

# Constants and initial setup
PAGE_NUMBER = 21  # Note: index starts from zero for page numbers
pdf_file_path = 'data/grade_3_english_book.pdf'
random.seed(42)

# Extract the book name from the PDF file path
book_name_with_ext = os.path.basename(pdf_file_path)
book_name = os.path.splitext(book_name_with_ext)[0]

# Initialize AWS Polly client
session = boto3.Session(profile_name='123233845129_DevOpsUser', region_name='us-east-1')
polly_client = session.client('polly')

# Set up output directory with timestamp
current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime("%Y-%m-%d-%H-%M-%S")
output_dir = f'output/{book_name}-page-{PAGE_NUMBER}-{formatted_datetime}'
os.makedirs(output_dir, exist_ok=True)
output_name = book_name

# --- EXTRACT PDF TEXT ---
# Extract text from the specified PDF page
with open(pdf_file_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    page = pdf_reader.pages[PAGE_NUMBER]
    text = page.extract_text()
    print(text)
print(f"Extracted text from page {PAGE_NUMBER}.")

# --- CONVERT PDF PAGE TO IMAGE ---
# Convert the specified PDF page to an image
pdf_document = fitz.open(pdf_file_path)
page = pdf_document.load_page(PAGE_NUMBER)
pix = page.get_pixmap()

# Save the image
image_path = f"{output_dir}/{output_name}_page_{PAGE_NUMBER}.png"
pix.save(image_path)
print(f"Page {PAGE_NUMBER} saved as {image_path}")

# --- VISUALIZE THE BLOCKS ASSIGNED TO THE PAGES ---
# Visualize the text blocks on the page by drawing rectangles around words
words = page.get_text("words")  # Extract words along with their coordinates and other info
pix = page.get_pixmap()

# Create an image from the pixmap
image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
draw = ImageDraw.Draw(image)

# Generate a color palette for each block
block_numbers = set(w[5] for w in words)  # Get unique block numbers
color_palette = {}
for block_no in block_numbers:
    color = tuple(random.randint(0, 255) for _ in range(3))
    color_palette[block_no] = color

# Load font for text labels
try:
    font = ImageFont.truetype("arial.ttf", size=14)
except IOError:
    font = ImageFont.load_default()

# Draw rectangles around words and label blocks
for word_info in words:
    x0, y0, x1, y1, word, block_no, line_no, word_no = word_info
    rect = [(x0, y0), (x1, y1)]
    color = color_palette[block_no]
    draw.rectangle(rect, outline=color, width=2)
    # Label the block
    if word_no == 0 and line_no == 0:
        label_position = (x0, y0 - 15)
        draw.text(label_position, f"Block {block_no}", fill=color, font=font)

# Save the annotated image
annotated_image_path = f"{output_dir}/{output_name}_annotated_page_{PAGE_NUMBER}_blocks.png"
image.save(annotated_image_path)
print(f"Annotated page saved as {annotated_image_path}")

# --- UNDERSTAND THE WORDS, COORDINATES, BLOCKS, LINES & WORD NUMBERS ---
# Extract words with their coordinates and other details
words_with_coords = []
for w in words:
    x0, y0, x1, y1, word, block_no, line_no, word_no = w
    word_info = {
        'text': word,
        'bbox': (x0, y0, x1, y1),
        'block_no': block_no,
        'line_no': line_no,
        'word_no': word_no
    }
    words_with_coords.append(word_info)

# Print word details (optional)
for word_info in words_with_coords:
    print(f"Word: {word_info['text']}")
    print(f"Coordinates: {word_info['bbox']}")
    print(f"Block: {word_info['block_no']}, Line: {word_info['line_no']}, Word No: {word_info['word_no']}")
    print("---")

# Save the word details to a JSON file
words_output_path = f"{output_dir}/{output_name}_words_with_coords_page_{PAGE_NUMBER}.json"
with open(words_output_path, 'w') as json_file:
    json.dump(words_with_coords, json_file, indent=2)
print(f"Word coordinates and details saved to {words_output_path}")

# --- CLEAN TEXT (REMOVE NOISE) AND APPLY SSML TAGS ---
# Clean the extracted text and apply SSML tags
ssml_output = generate(text)
ssml_text = remove_code_blocks(ssml_output)
print(ssml_text)

# --- CREATE AUDIO (.mp3) & SPEECH MARKERS (.json) ---
# Synthesize speech (audio) from the SSML text
response = polly_client.synthesize_speech(
    Engine='standard',
    OutputFormat='mp3',
    Text=ssml_text,
    TextType='ssml',
    VoiceId='Joanna'
)

# Save the audio stream to a file
audio_stream = response.get('AudioStream')
audio_file_path = os.path.join(output_dir, f"{output_name}_page_{PAGE_NUMBER}_audio.mp3")
with open(audio_file_path, 'wb') as audio_file:
    audio_file.write(audio_stream.read())

# Generate speech marks (word-level timing data)
speech_marks_response = polly_client.synthesize_speech(
    Engine='standard',
    OutputFormat='json',
    Text=ssml_text,
    TextType='ssml',
    VoiceId='Joanna',
    SpeechMarkTypes=['word']
)

# Read and parse the speech marks
speech_marks_stream = speech_marks_response.get('AudioStream').read().decode('utf-8')
speech_marks = [json.loads(line) for line in speech_marks_stream.strip().split('\n') if line]

# Save the speech marks to a JSON file
speech_marks_file_path = os.path.join(output_dir, f"{output_name}_page_{PAGE_NUMBER}_speech_marks.json")
with open(speech_marks_file_path, 'w') as json_file:
    json.dump(speech_marks, json_file, indent=2)
print(f"Audio and speech markers generated for page number {PAGE_NUMBER}")

# --- NORMALIZE DATA ---
# Load the speech marks JSON data
with open(speech_marks_file_path, 'r') as json_file:
    speech_marks = json.load(json_file)

# Load the words with coordinates JSON data
with open(words_output_path, 'r') as json_file:
    words_with_coords = json.load(json_file)

def is_valid_word(mark):
    word = mark['value']
    # Exclude SSML tags (self-closing tags)
    if word.startswith('<') and word.endswith('/>'):
        return False
    return True

def normalize_word(word):
    # Convert to lowercase and remove punctuation
    word = word.lower()
    word = re.sub(r'[^\w\s]', '', word)
    return word

# Filter out any non-word entries from the speech marks
speech_marks_filtered = [mark for mark in speech_marks if is_valid_word(mark)]

# Normalize the words in speech marks
for mark in speech_marks_filtered:
    mark['normalized_value'] = normalize_word(mark['value'])

# Normalize the words in words_with_coords
for word_info in words_with_coords:
    word_info['normalized_text'] = normalize_word(word_info['text'])

# Create lists of normalized words
speech_normalized_words = [mark['normalized_value'] for mark in speech_marks_filtered]
pdf_normalized_words = [info['normalized_text'] for info in words_with_coords]

# Find matching sequences between the speech marks and PDF words
matcher = SequenceMatcher(None, speech_normalized_words, pdf_normalized_words)
matching_blocks = matcher.get_matching_blocks()

# Map the speech marks to the PDF words
word_mappings = []
for block in matching_blocks:
    i, j, n = block
    for k in range(n):
        speech_index = i + k
        pdf_index = j + k
        if speech_index < len(speech_marks_filtered) and pdf_index < len(words_with_coords):
            word_mappings.append({
                'speech_mark': speech_marks_filtered[speech_index],
                'pdf_word_info': words_with_coords[pdf_index]
            })

# Create a list of mapped words with time and bounding box
mapped_words = []
for mapping in word_mappings:
    time_ms = mapping['speech_mark']['time']
    bbox = mapping['pdf_word_info']['bbox']
    mapped_words.append({
        'time_ms': time_ms,
        'bbox': bbox
    })

# Save the mapped words to a JSON file
mapped_words_output_path = f"{output_dir}/{output_name}_mapped_words_page_{PAGE_NUMBER}.json"
with open(mapped_words_output_path, 'w') as json_file:
    json.dump(mapped_words, json_file, indent=2)

print(f"Mapped words saved to {mapped_words_output_path}")
print(mapped_words)
