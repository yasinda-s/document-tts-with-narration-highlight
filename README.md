**Overview**

The goal of this project is to create a more engaging way for students to learn English by transforming text from a book into speech, while visually highlighting the corresponding words in the PDF as they are spoken. It helps learners follow along with the text as they listen, providing a rich learning experience.

**Key technologies**

Python for scripting.
AWS Polly for text-to-speech conversion.
Tkinter for the GUI.
PIL (Python Imaging Library) for image processing.
PyPDF2 and fitz for PDF handling.
Vertex AI for generating SSML tags for enhanced speech.

**Features**

Text Extraction: Extracts text from a specified page in a PDF book.
SSML Generation: Uses AI to generate SSML tags, making the speech sound more natural.
Text-to-Speech: Converts text into speech using AWS Polly, with speech markers for precise synchronization.
Text Highlighting: Displays the PDF page in a GUI and highlights text as it is read aloud.
Interactive Learning: Allows users to follow along with the spoken text, enhancing comprehension.
