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

        self.annotations = []
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
    def pop_annotation(self):
        return self.annotations.pop()

    def pop_undo(self):
        return self.undo_stack.pop()

    def pop_redo(self):
        return self.redo_stack.pop()

    def append_annotation(self, annotation):
        self.annotations.append(annotation)

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
        self.line_object = None

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
        self.segment = Segment(canvas, colour, x, y)

        self.vertices = []
        self.vertices.append(x)
        self.vertices.append(y)

    def draw_segment(self):
        self.segment.draw()

    def adjust_segment(self, x: int, y: int):
        self.segment.adjust(x, y)

    def end_segment(self) -> bool:
        coords = self.segment.get_coords()

        if len(self.vertices) >= 6 and distance(coords[0], coords[1], self.vertices[0], self.vertices[1]) <= 8:
            self.segment.adjust(self.vertices[0], self.vertices[1])
            self.segments.append(self.segment)

            return True
        else:
            if not self.check_invalid():
                self.segments.append(self.segment)
                self.vertices.append(coords[0])
                self.vertices.append(coords[1])
                self.segment = Segment(self.canvas, self.colour, coords[0], coords[1])
                self.draw_segment()

            return False

    def resume_segment(self, x: int, y: int) -> bool:
        if len(self.segments) - 1 >= 0:
            last_x, last_y = self.segments[len(self.segments)-1].get_coords()
            if distance(x, y, last_x, last_y) <= 8:
                self.segment = Segment(self.canvas, self.colour, last_x, last_y)
                self.vertices.append(last_x)
                self.vertices.append(last_y)
                self.draw_segment()

                return True

        return False

    def get_coords(self) -> list:
        return self.vertices

    def check_invalid(self):
        def orientation(a, b, c):
            result = ((b[1] - a[1]) * (c[0] - b[0]))  - ((b[0] - a[0]) * (c[1] - b[1]))
            if result > 0:
                return 1
            elif result < 0:
                return -1
            else:
                return 0

        p1 = self.segment.get_start()
        p2 = self.segment.get_coords()
        for segment in self.segments:
            p3 = segment.get_start()
            p4 = segment.get_coords()

            if p1 != p4 and p2 != p3:
                o1 = orientation(p1, p2, p3)
                o2 = orientation(p1, p2, p4)
                o3 = orientation(p3, p4, p1)
                o4 = orientation(p3, p4, p2)

                if o1 != o2 and o3 != o4:
                    return True

        return False


class Annotation:
    def __init__(self, canvas: tk.Canvas, state_manager, label: str, colour: str):
        self.canvas = canvas
        self.state_manager = state_manager
        self.label = label
        self.colour = colour

        self.bbox = None
        self.poly = None
        self.segment = None
        self.polygons = []

    # Bounding box specific methods
    def is_active_bbox(self):
        return bool(self.bbox)

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

    def is_active_segment(self):
        return bool(self.poly.segment)

    def set_polygon(self, polygon: Polygon):
        self.poly = polygon

    def adjust_polygon_segment(self, x: int, y: int):
        self.poly.adjust_segment(x, y)

    def draw_polygon_segment(self):
        self.poly.draw_segment()
        self.state_manager.undo_button['state'] = tk.NORMAL

    def end_polygon_segment(self):
        self.segment = self.poly.segment
        print(self.poly.check_invalid())
        if self.poly.end_segment():
            self.polygons.append(self.poly)
            self.poly = None

    def resume_polygon(self, x: int, y: int) -> bool:
        return self.poly.resume_segment(x, y)

    # Undo / redo checks
    def update_annotation_after_undo(self):
        if not self.poly and self.polygons:
            self.poly = self.polygons.pop()
            self.poly.segments.pop()
            self.poly.segment = None
            self.poly.vertices.pop()
            self.poly.vertices.pop()
        elif self.poly:
            if self.poly.segments:
                self.poly.vertices.pop()
                self.poly.vertices.pop()
                self.poly.segments.pop()
            else:
                self.poly = None
                self.update_annotation_after_undo()
        else:
            self.bbox = None

    def update_annotation_after_redo(self, redo):
        if type(redo) == BoundingBox:
            self.bbox = redo
        elif type(redo) == Segment:
            if self.poly:
                self.poly.segment = redo
                self.end_polygon_segment()
                if self.poly:
                    self.poly.segment = None
            else:
                self.poly = Polygon(self.canvas, self.colour, 0, 0)
                self.poly.segment = redo

    # General methods
    def get_bbox(self) -> BoundingBox:
        return self.bbox

    def get_segment(self) -> Segment:
        return self.segment

    def get_label(self) -> str:
        return self.label

    def get_colour(self) -> str:
        return self.colour
