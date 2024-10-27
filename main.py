import tkinter as tk
from tkinter import font as tkfont
from PIL import Image, ImageTk, ImageDraw
import pygame
from generations import mapped_words, PAGE_NUMBER, output_dir, output_name

class TextHighlighter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EAG ReadToMe - Learn English with Fun!")
        self.root.geometry("900x700")

        # Set a fun background color or an image for the window
        self.root.configure(bg='#ADD8E6')

        # Add a title label with a playful font
        self.title_font = tkfont.Font(family="Comic Sans MS", size=24, weight="bold")
        self.title_label = tk.Label(
            self.root, 
            text="Welcome to ReadToMe!", 
            font=self.title_font, 
            bg='#FFD700',
            fg='#1E90FF',
            pady=10
        )
        self.title_label.pack(fill=tk.X)

        # Add a button to play audio with a playful style
        self.play_button = tk.Button(
            self.root, 
            text="Start Reading", 
            command=self.start_reading, 
            font=self.title_font, 
            bg='#32CD32',
            fg='white', 
            activebackground='#228B22',
            padx=10, pady=5
        )
        self.play_button.pack(pady=10)

        # Load and display the image
        self.page_image = Image.open(f"{output_dir}/{output_name}_page_{PAGE_NUMBER}.png")
        self.photo = ImageTk.PhotoImage(self.page_image)

        # Create a frame to hold the canvas and give it a colorful border
        self.canvas_frame = tk.Frame(self.root, bg='#FFD700', bd=5)
        self.canvas_frame.pack(pady=20)
        
        self.canvas = tk.Canvas(self.canvas_frame, width=self.page_image.width, height=self.page_image.height)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Initialize audio
        pygame.mixer.init()
        pygame.mixer.music.load(f'{output_dir}/{output_name}_page_{PAGE_NUMBER}_audio.mp3')
        pygame.mixer.music.set_volume(1.0)

        self.current_index = 0

    def start_reading(self):
        """Starts the audio playback and begins the highlighting process."""
        self.play_audio()
        self.update_highlighting()

    def play_audio(self):
        """Plays the audio."""
        pygame.mixer.music.play()

    def highlight_word(self, bbox):
        self.canvas.delete('highlight')
        x0, y0, x1, y1 = bbox

        # Create an overlay image with a translucent yellow rectangle
        overlay = Image.new('RGBA', (self.page_image.width, self.page_image.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 0, 128), outline="black", width=2)

        # Convert the overlay to a PhotoImage and draw it on the canvas
        overlay_photo = ImageTk.PhotoImage(overlay)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=overlay_photo, tags='highlight')
        self.canvas.overlay_image = overlay_photo

    def update_highlighting(self):
        """Updates the highlighted text based on the current playback time."""
        current_time_ms = pygame.mixer.music.get_pos()

        while (self.current_index < len(mapped_words) and
               current_time_ms >= mapped_words[self.current_index]['time_ms']):
            bbox = mapped_words[self.current_index]['bbox']
            self.highlight_word(bbox)
            self.current_index += 1

        if pygame.mixer.music.get_busy():
            self.root.after(20, self.update_highlighting)
        else:
            self.canvas.delete('highlight')

    def run(self):
        """Runs the main Tkinter loop."""
        self.root.mainloop()

if __name__ == "__main__":
    app = TextHighlighter()
    app.run()
