import tkinter as tk
from PIL import ImageTk, Image
import os
from datetime import date


# Represents each instance of an image that can be edited
class EditableImage:
    def __init__(self, image_path, canvas: tk.Canvas):
        self.image_path = image_path
        self.canvas = canvas

        self.image = Image.open(image_path)
        self.image_render = ImageTk.PhotoImage(self.image)

        self.undo_stack = []
        self.redo_stack = []

        self.width = self.image.width
        self.height = self.image.height
        self.file_name = os.path.basename(image_path)
        self.date_captured = self.get_date_captured()

    def get_date_captured(self):
        exif_data = self.image.getexif()
        for tag_id in exif_data:
            if tag_id == 36867:
                return exif_data.get(tag_id)

        print(f"Date_created could not be found for {self.file_name}, defaulting to {date.today()}")
        return date.today()

    # Undo / redo stack actions
    def pop_undo(self):
        return self.undo_stack.pop()

    def pop_redo(self):
        return self.redo_stack.pop()

    def append_undo(self, undo: tuple):
        self.undo_stack.append(undo)

    def append_redo(self, redo: tuple):
        self.redo_stack.append(redo)

    # Image changes
    def activate_image(self):
        self.canvas.configure(width=self.width, height=self.height)
        self.canvas.create_image(0, 0, image=self.image_render, anchor=tk.NW)
        for undo in self.undo_stack:
            self.canvas.create_rectangle(undo[0][0], undo[0][1], undo[0][2], undo[0][3], width=4, outline=undo[2])
            self.canvas.create_text((undo[0][0]+undo[0][2])/2, undo[0][3]+15, text=undo[1], fill=undo[2],
                                    font="Helvetica 15 bold")

    def deactivate_image(self):
        self.canvas.delete("all")
