import tkinter as tk
from PIL import Image, ImageTk
import pygame
import time
from generations_v2 import mapped_words, PAGE_NUMBER

root = tk.Tk()
root.title("Text Highlighting Demo")

page_image = Image.open(f"output/grade_3_english_book_page_{PAGE_NUMBER}.png")
photo = ImageTk.PhotoImage(page_image)

canvas = tk.Canvas(root, width=page_image.width, height=page_image.height)
canvas.pack()

canvas_image = canvas.create_image(0, 0, anchor=tk.NW, image=photo)

pygame.mixer.init()
pygame.mixer.music.load(f'output/page_{PAGE_NUMBER}_audio.mp3')

def play_audio():
    pygame.mixer.music.play()

def highlight_word(bbox):
    canvas.delete('highlight')
    x0, y0, x1, y1 = bbox
    canvas.create_rectangle(x0, y0, x1, y1, outline='red', width=2, tags='highlight')

play_audio()

start_time = time.time()
current_index = 0

def update_highlighting():
    global current_index
    current_time_ms = pygame.mixer.music.get_pos()

    while current_index < len(mapped_words) and current_time_ms >= mapped_words[current_index]['time_ms']:
        bbox = mapped_words[current_index]['bbox']
        highlight_word(bbox)
        current_index += 1

    if pygame.mixer.music.get_busy():
        root.after(20, update_highlighting)
    else:
        canvas.delete('highlight')

root.after(0, update_highlighting)
root.mainloop()