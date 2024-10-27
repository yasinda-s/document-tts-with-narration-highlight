import PyPDF2
from IPython.display import Audio, display, clear_output, HTML
from time import sleep
import boto3
import base64
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
import fitz
from PIL import Image, ImageDraw, ImageFont
import random
import os
import re
from vertex_functions import generate, remove_code_blocks
from difflib import SequenceMatcher

# Note: index starts from zero for page numbers
PAGE_NUMBER = 21
pdf_file_path = 'data/grade_3_english_book.pdf'
random.seed(42)
session = boto3.Session(profile_name='123233845129_DevOpsUser', region_name='us-east-1')
polly_client = session.client('polly')

# EXTRACT PDF TEXT
with open(pdf_file_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    page_number = PAGE_NUMBER
    page = pdf_reader.pages[page_number]
    text = page.extract_text()
    print(text)

print(f"Extracted text from page {PAGE_NUMBER}.")

# CONVERT PDF PAGE TO IMAGE
pdf_document = fitz.open(pdf_file_path)
page = pdf_document.load_page(PAGE_NUMBER)
pix = page.get_pixmap()

image_path = f"output/grade_3_english_book_page_{PAGE_NUMBER}.png"
pix.save(image_path)

print(f"Page {PAGE_NUMBER} saved as {image_path}")

# VISUALIZE THE BLOCKS ASSIGNED TO THE PAGES
words = page.get_text("words")
pix = page.get_pixmap()

image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
draw = ImageDraw.Draw(image)

block_numbers = set(w[5] for w in words)
color_palette = {}
for block_no in block_numbers:
    color = tuple(random.randint(0, 255) for _ in range(3))
    color_palette[block_no] = color

try:
    font = ImageFont.truetype("arial.ttf", size=14)
except IOError:
    font = ImageFont.load_default()

for word_info in words:
    x0, y0, x1, y1, word, block_no, line_no, word_no = word_info
    rect = [(x0, y0), (x1, y1)]
    color = color_palette[block_no]
    draw.rectangle(rect, outline=color, width=2)
    if word_no == 0 and line_no == 0:
        label_position = (x0, y0 - 15)
        draw.text(label_position, f"Block {block_no}", fill=color, font=font)

image_path = f"output/annotated_page_{PAGE_NUMBER}_blocks.png"
image.save(image_path)
print(f"Annotated page saved as {image_path}")

# UNDERSTAND THE WORDS, COORDINATES, BLOCKS, LINES & WORD NUMBERS
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

for word_info in words_with_coords:
    print(f"Word: {word_info['text']}")
    print(f"Coordinates: {word_info['bbox']}")
    print(f"Block: {word_info['block_no']}, Line: {word_info['line_no']}, Word No: {word_info['word_no']}")
    print("---")

# CLEAN TEXT (REMOVE NOISE) AND APPLY SSML TAGS
ssml_output = generate(text)
ssml_text = remove_code_blocks(ssml_output)
print(ssml_text)

# CREATE AUDIO (.mp3) & SPEECH MARKETS (.json)
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

response = polly_client.synthesize_speech(
    Engine='standard',
    OutputFormat='mp3',
    Text=ssml_text,
    TextType='ssml',
    VoiceId='Joanna'
)

audio_stream = response.get('AudioStream')
audio_file_path = os.path.join(output_dir, f"page_{PAGE_NUMBER}_audio.mp3")
with open(audio_file_path, 'wb') as audio_file:
    audio_file.write(audio_stream.read())

speech_marks_response = polly_client.synthesize_speech(
    Engine='standard',
    OutputFormat='json',
    Text=ssml_text,
    TextType='ssml',
    VoiceId='Joanna',
    SpeechMarkTypes=['word']
)

speech_marks_stream = speech_marks_response.get('AudioStream').read().decode('utf-8')
speech_marks = [json.loads(line) for line in speech_marks_stream.strip().split('\n') if line]

speech_marks_file_path = os.path.join(output_dir, f"page_{PAGE_NUMBER}_speech_marks.json")
with open(speech_marks_file_path, 'w') as json_file:
    json.dump(speech_marks, json_file, indent=2)

print(f"Audio and speech markers generated for page number {PAGE_NUMBER}")

# SYNCING TOGETHER & CREATING MAPPED WORDS
with open(f"output/page_{PAGE_NUMBER}_speech_marks.json", 'r') as json_file:
    speech_marks = json.load(json_file)

def is_valid_word(mark):
    word = mark['value']
    if word.startswith('<') and word.endswith('/>'):
        return False
    return True

speech_marks_filtered = [mark for mark in speech_marks if is_valid_word(mark)]

def normalize_word(word):
    word = word.lower()
    word = re.sub(r'[^\w\s]', '', word)
    return word

for mark in speech_marks_filtered:
    mark['normalized_value'] = normalize_word(mark['value'])
    
for word_info in words_with_coords:
    word_info['normalized_text'] = normalize_word(word_info['text'])

speech_normalized_words = [mark['normalized_value'] for mark in speech_marks_filtered]
pdf_normalized_words = [info['normalized_text'] for info in words_with_coords]

matcher = SequenceMatcher(None, speech_normalized_words, pdf_normalized_words)
matching_blocks = matcher.get_matching_blocks()

word_mappings = []
for block in matching_blocks:
    i, j, n = block
    for k in range(n):
        speech_index = i + k
        pdf_index = j + k
        word_mappings.append({
            'speech_mark': speech_marks_filtered[speech_index],
            'pdf_word_info': words_with_coords[pdf_index]
        })

mapped_words = []
for mapping in word_mappings:
    time_ms = mapping['speech_mark']['time']
    bbox = mapping['pdf_word_info']['bbox']
    mapped_words.append({
        'time_ms': time_ms,
        'bbox': bbox
    })
    
print(mapped_words)