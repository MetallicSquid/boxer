import tkinter as tk
from PIL import ImageTk, Image
import os
from datetime import date
from time import sleep


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


# Represents an edge of a segmentation polygon (a line) on the canvas
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

    def get_start(self) -> list:
        return [self.start_x, self.start_y]

    def get_coords(self) -> list:
        return [self.end_x, self.end_y]


def distance(x_1, y_1, x_2, y_2):
    delta_x = x_2 - x_1
    delta_y = y_2 - y_1

    return ((delta_x ** 2) + (delta_y ** 2)) ** 0.5


# Represents a segmentation polygon on the canvas
class Polygon:
    def __init__(self, canvas: tk.Canvas, colour: str, x: int, y: int):
        self.canvas = canvas
        self.colour = colour

        self.segments = []
        self.redo = []
        self.segment = Segment(canvas, colour, x, y)

        self.vertices = []
        self.vertices.append([x, y])

    def draw_segment(self):
        self.segment.draw()

    def adjust_segment(self, x: int, y: int):
        self.segment.adjust(x, y)

    def end_segment(self) -> bool:
        coords = self.segment.get_coords()

        if len(self.vertices) >= 3 and distance(coords[0], coords[1], self.vertices[0][0], self.vertices[0][1]) <= 8:
            self.segment.adjust(self.vertices[0][0], self.vertices[0][1])
            self.segments.append(self.segment)
            self.vertices.append([self.vertices[0][0], self.vertices[0][1]])
            self.segment = None

            return True
        else:
            self.segments.append(self.segment)
            self.vertices.append(coords)
            self.segment = Segment(self.canvas, self.colour, coords[0], coords[1])
            self.draw_segment()

            return False

    def undo_segment(self):
        if self.segment:
            print("There is a segment")
            self.redo.append(self.segment)
            self.segment.delete()
            self.segment = self.segments.pop()
            coords = self.segment.get_start()
            self.adjust_segment(coords[0], coords[1])
            self.vertices.pop()
        else:
            print("There isn't a segment")
            self.segment = self.segments.pop()
            self.redo.append(self.segment)
            coords = self.segment.get_start()
            self.adjust_segment(coords[0], coords[1])
            self.vertices.pop()

    def redo_segment(self):
        self.segment = self.redo.pop()
        self.segment.draw()

    def get_coords(self) -> list:
        return self.vertices


class Annotation:
    def __init__(self, canvas: tk.Canvas, state_manager, label: str, colour: str):
        self.canvas = canvas
        self.state_manager = state_manager
        self.label = label
        self.colour = colour

        self.bbox = None
        self.poly = None
        self.polygons = []
        self.redo = []

    # Bounding box specific methods
    def set_bbox(self, bbox: BoundingBox):
        self.bbox = bbox

    def adjust_bbox(self, x: int, y: int):
        self.bbox.adjust(x, y)

    def draw_bbox(self):
        self.bbox.draw()
        self.state_manager.undo_button['state'] = tk.NORMAL

    def get_bbox_coords(self) -> list:
        return self.bbox.get_coords()

    # Polygon specific methods
    def is_active_polygon(self):
        return bool(self.poly)

    def set_polygon(self, polygon: Polygon):
        self.poly = polygon

    def adjust_polygon_segment(self, x: int, y: int):
        self.poly.adjust_segment(x, y)

    def draw_polygon_segment(self):
        self.poly.draw_segment()
        self.state_manager.undo_button['state'] = tk.NORMAL

    def end_polygon_segment(self):
        if self.poly.end_segment():
            self.polygons.append(self.poly)
            self.poly = None

    # General methods
    def get_label(self) -> str:
        return self.label

    def get_colour(self) -> str:
        return self.colour

    def undo_state(self):
        self.state_manager.redo_state(self.redo)
        if not self.polygons and not self.bbox:
            self.state_manager.undo_button['state'] = tk.DISABLED

    def undo(self) -> bool:
        if self.poly:
            self.poly.undo_segment()
            if not self.poly.segments:
                self.poly = None
            self.undo_state()

            return True
        elif self.polygons:
            self.poly = self.polygons.pop()
            self.poly.undo_segment()
            self.undo_state()

            return True
        elif self.bbox:
            self.bbox.delete()
            self.bbox = None
            self.undo_state()

            return True

        return False


    def redo(self):
        if self.poly:
            self.poly.redo_segment()


