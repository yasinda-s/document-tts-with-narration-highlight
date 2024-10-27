import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting

def generate(raw_page_text):
    prompt = f"""You are professional text to speech transcriber.
    Your goal is to add SSML tags to make plain text more human-like whilst ensuring it is easy for students to understand.

    Consider the following steps when transforming plain text.

    STEP 1: Read the plain text and remove any unnecessary text that is not part of the story (page numbers, publication names, etc). Do not change the text that is part of the story.
    STEP 2: Identify the best way to make the story natural & human-like.
    STEP 3: Include the necessary SSML tags to make the story natural and have a nicer flow.
    STEP 4: Ensure the output is ready to be loaded in with AWS Polly.

    Plain text input:
    Hello! Today, we are going to learn a new story. Are you ready?
    Once upon a time, there was a little cat who loved to play. The cat’s name was Whiskers.
    Whiskers had a best friend, a big, brown dog named Buddy.
    One day, Whiskers and Buddy decided to go on an adventure. They wanted to find a hidden treasure!
    First, they went to the forest. The forest was big and quiet, and Whiskers felt a little scared.
    But Buddy said, “Don’t worry, Whiskers! I’m here with you.” And Whiskers felt brave.
    Let’s stop here. Did you understand the story? Let’s say the words together: Whiskers and Buddy.
    Great job! Let’s continue the story next time.

    SSML Output:
    <speak>
        <prosody rate="medium">
            Hello! Today, we are going to learn a new story. Are you ready?
        </prosody>
        <break time="1s"/>
        Once upon a time, there was a little cat who loved to play. The cat’s name was Whiskers.
        <break time="500ms"/>
        Whiskers had a best friend, a big, brown dog named Buddy.
        <break time="1s"/>
        One day, Whiskers and Buddy decided to go on an adventure. They wanted to find a hidden treasure!
        <break time="1s"/>
        First, they went to the forest. The forest was big and quiet, and Whiskers felt a little scared.
        <break time="1s"/>
        But Buddy said, “Don’t worry, Whiskers! I’m here with you.” And Whiskers felt brave.
        <break time="1.5s"/>
        Let’s stop here. Did you understand the story? Let’s say the words together: 
        <break time="500ms"/> Whiskers and Buddy.
        <break time="500ms"/>
        Great job! Let’s continue the story next time.
    </speak>

    Plain text input: {raw_page_text}

    SSML Output:"""

    vertexai.init(project="syy-eag-np-61cd", location="us-central1")
    model = GenerativeModel(
        "gemini-1.5-flash-002",
    )
    responses = model.generate_content(
        [prompt],
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=False,
    )
    
    return responses.text

def remove_code_blocks(text):
    lines = text.splitlines()
    cleaned_lines = [line for line in lines if not line.startswith('```') and 'xml' not in line]
    
    cleaned_text = "\n".join(cleaned_lines)
    
    return cleaned_text

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 0.1,
    "top_p": 0.95,
}

safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
]