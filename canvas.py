import tkinter as tk
from PIL import ImageTk, Image
import os
from datetime import date


def find_object_ref(canvas: tk.Canvas, coords: list):
    for object_ref in canvas.find_all():
        if canvas.coords(object_ref) == coords:
            return object_ref

    return None


def find_label_refs(canvas: tk.Canvas, label: str):
    ref_list = []
    for object_ref in canvas.find_all():
        if canvas.type(object_ref) == "text":
            if canvas.itemcget(object_ref, "text") == label:
                ref_list.append(object_ref)

    return ref_list


# Represents each instance of an image that can be edited
class EditableImage:
    def __init__(self, image_path, canvas: tk.Canvas):
        self.image_path = image_path
        self.canvas = canvas

        self.image = Image.open(image_path)
        self.image_render = ImageTk.PhotoImage(self.image)
        self.image_object = None

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
        self.image_object = self.canvas.create_image(self.width/2, self.height/2, image=self.image_render,
                                                     anchor=tk.CENTER)
        for undo in self.undo_stack:
            undo.draw()

    def deactivate_image(self):
        self.canvas.delete("all")


# Represents a box-label pair on the canvas
class BoundingBox:
    def __init__(self, canvas: tk.Canvas, coords: list, label: str, colour: str):
        self.canvas = canvas

        self.start_x: int = coords[0]
        self.start_y: int = coords[1]
        self.end_x: int = coords[2]
        self.end_y: int = coords[3]

        self.label: str = label
        self.colour: str = colour

        self.box_object = None
        self.label_object = None

    def draw(self):
        self.box_object = self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, width=3,
                                                       outline=self.colour)
        self.label_object = self.canvas.create_text((self.start_x + self.end_x) / 2, self.end_y + 15, text=self.label,
                                                    fill=self.colour, font="Helvetica 15 bold")

    def adjust(self, x: int, y: int):
        self.end_x = x
        self.end_y = y

        self.canvas.coords(self.box_object, self.start_x, self.start_y, x, y)
        self.canvas.coords(self.label_object, (self.start_x + x)/2, y+15)

    def delete(self):
        self.canvas.delete(self.box_object)
        self.canvas.delete(self.label_object)
        self.box_object = None
        self.label_object = None

    def change_label(self, label: str):
        self.label = label
        if self.label_object:
            self.canvas.itemconfigure(self.label_object, text=label)

    def get_coords(self) -> list:
        return [self.start_x, self.start_y, self.end_x, self.end_y]

    def get_label(self) -> str:
        return self.label


class Segment:
    def __init__(self, canvas: tk.Canvas, colour: str, x: int, y: int):
        self.canvas = canvas
        self.colour = colour

        self.start_x: int = x
        self.start_y: int = y
        self.end_x: int = x
        self.end_y: int = y

        self.line_object = None

    def draw(self):
        self.line_object = self.canvas.create_line(self.start_x, self.start_y, self.end_x, self.end_y, width=3,
                                                   fill=self.colour)

    def adjust(self, x: int, y: int):
        self.end_x = x
        self.end_y = y

        self.canvas.coords(self.line_object, self.start_x, self.start_y, self.end_x, self.end_y)

    def delete(self):
        self.canvas.delete(self.line_object)

    def get_coords(self) -> list:
        return [self.end_x, self.end_y]


def distance(x_1, y_1, x_2, y_2):
    delta_x = x_2 - x_1
    delta_y = y_2 - y_1

    return ((delta_x ** 2) + (delta_y ** 2)) ** 0.5


class Polygon:
    def __init__(self, canvas: tk.Canvas, colour: str, x: int, y: int):
        self.canvas = canvas
        self.colour = colour

        self.segments = []
        self.vertices = []
        self.vertices.append([x, y])

        self.segment = Segment(canvas, colour, x, y)

    def draw(self):
        self.segment.draw()

    def adjust(self, x: int, y: int):
        self.segment.adjust(x, y)

    def end_segment(self) -> bool:
        coords = self.segment.get_coords()

        if len(self.vertices) >= 3 and distance(coords[0], coords[1], self.vertices[0][0], self.vertices[0][1]) <= 5:
            for segment in self.segments:
                segment.delete()
            self.canvas.create_polygon(self.vertices, outline=self.colour, width=3, fill="")

            return True
        else:
            self.segments.append(self.segment)
            self.vertices.append(coords)
            self.segment = Segment(self.canvas, self.colour, coords[0], coords[1])
            self.draw()

            return False
