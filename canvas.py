import tkinter as tk
from PIL import ImageTk, Image
import os
from datetime import date
from collections import defaultdict


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


# Represents the canvas itself and the actions that can be performed with it
class ImageManager:
    def __init__(self, canvas, colour_picker, status_bar):
        self.canvas = canvas
        self.colour_picker = colour_picker
        self.status_bar = status_bar
        self.history_manager = None

        self.image_pointer = 0
        self.editable_images = []
        self.active_image = None

        self.stack_change = tk.BooleanVar()

        self.start_x, self.start_y = None, None
        self.current_x, self.current_y = None, None
        self.current_box = None
        self.current_label = None

        self.draw_startup()

    # Placeholder screens
    def draw_placeholder(self, title, subtitle, description):
        self.deactivate_canvas()
        self.canvas.create_text(20, 20, text=title, fill="black", font="Helvetica 30 bold", anchor=tk.NW)
        self.canvas.create_text(20, 70, text=subtitle, fill="gray", font="Helvetica 20 italic", anchor=tk.NW)
        self.canvas.create_text(20, 120, text=description, fill="black", font="Helvetica 15", anchor=tk.NW)

    def draw_startup(self):
        title = "Boxer 🥊"
        subtitle = "The simple bounding box tool"
        description = "To start annotating images, press `🔍 Open`\nbutton and pick a relevant directory. If you need\nany help, please reference the docs. Enjoy!"
        self.draw_placeholder(title, subtitle, description)
        self.status_bar.update_action("Let's begin! Press the `🔍 Open` and pick a directory.")
        self.status_bar.update_info("")

    def draw_invalid(self):
        title = "Boxer 🥊"
        subtitle = "The simple bounding box tool"
        description = "Sorry, the directory that you picked is invalid,\nit needs to contain either `.jpg`, `.png` or\n`.bmp` images. If you need any help, please\nreference the docs. Enjoy!"
        self.draw_placeholder(title, subtitle, description)
        self.status_bar.update_action("Sorry, the directory needs to contain `.jpg`, `.png` or `.bmp` images.")
        self.status_bar.update_info("")

    def reset_canvas(self):
        self.canvas.delete("all")
        self.active_image = None
        self.editable_images = []
        self.image_pointer = 0
        self.current_box = None
        self.current_label = None

        self.stack_change.set(not self.stack_change.get())

    def deactivate_canvas(self):
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.colour_picker.entry.unbind("<KeyRelease>")
        self.reset_canvas()

    def new_canvas(self, image_paths: list, history_manager):
        self.history_manager = history_manager

        if self.active_image:
            self.reset_canvas()
        else:
            self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
            self.canvas.bind("<B1-Motion>", self.on_mouse_move)
            self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
            self.colour_picker.entry.bind("<KeyRelease>", self.update_labels)

        for image_path in image_paths:
            editable_image = EditableImage(image_path, self.canvas)
            self.editable_images.append(editable_image)

        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        filename = os.path.basename(self.active_image.image_path)
        file_ratio = f"{self.image_pointer}/{len(self.editable_images)}"
        self.status_bar.update_info(f"{filename}    {file_ratio}")

        self.stack_change.set(not self.stack_change.get())

    def load_canvas(self, history_manager):
        self.history_manager = history_manager

        if self.active_image:
            self.reset_canvas()
        else:
            self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
            self.canvas.bind("<B1-Motion>", self.on_mouse_move)
            self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
            self.colour_picker.entry.bind("<KeyRelease>", self.update_labels)

        directory = self.history_manager.directory
        images = self.history_manager.images
        annotations = self.history_manager.annotations
        bbox_dict = defaultdict(list)
        id_category_map = self.history_manager.make_id_category_map()
        id_colour_map = self.history_manager.make_id_colour_map()
        for annotation in annotations:
            coords = [annotation["bbox"][0], annotation["bbox"][1], annotation["bbox"][0]+annotation["bbox"][2],
                      annotation["bbox"][1]+annotation["bbox"][3]]
            label = id_category_map[annotation["category_id"]]
            colour = id_colour_map[label]

            bbox_dict[annotation["image_id"]].append((coords, label, colour))

        for image in images:
            path = os.path.join(directory, image["file_name"])
            editable_image = EditableImage(path, self.canvas)
            editable_image.undo_stack = bbox_dict[image["id"]]
            self.editable_images.append(editable_image)

        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        filename = os.path.basename(self.active_image.image_path)
        file_ratio = f"{self.image_pointer}/{len(self.editable_images)}"
        self.status_bar.update_info(f"{filename}    {file_ratio}")

        self.stack_change.set(not self.stack_change.get())

    def shift_image(self, delta: int):
        self.image_pointer += delta
        self.active_image.deactivate_image()
        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        self.status_bar.update_action(f"Moved to image {self.image_pointer+1} out of {len(self.editable_images)}.")

        filename = os.path.basename(self.active_image.image_path)
        file_ratio = f"{self.image_pointer}/{len(self.editable_images)}"
        self.status_bar.update_info(f"{filename}    {file_ratio}")

        # FIXME: This whole trace system feels very hack-ish, this should probably be changed in the future
        self.stack_change.set(not self.stack_change.get())

    def find_object_ref(self, coords: list):
        for object_ref in self.canvas.find_all():
            if self.canvas.coords(object_ref) == coords:
                return object_ref

        return None

    def find_label_refs(self, label: str):
        ref_list = []
        for object_ref in self.canvas.find_all():
            if self.canvas.type(object_ref) == "text":
                if self.canvas.itemcget(object_ref, "text") == label:
                    ref_list.append(object_ref)

        return ref_list

    # Undo and redo events
    def undo_action(self):
        undo = self.active_image.pop_undo()
        self.canvas.delete(self.find_object_ref(undo[0]))
        self.canvas.delete(self.find_object_ref([(undo[0][0]+undo[0][2])/2, undo[0][3]+15]))
        self.status_bar.update_action(f"Removed `{undo[1]}` bounding box at {undo[0]}")
        self.active_image.append_redo(undo)

    def redo_action(self):
        redo = self.active_image.pop_redo()
        self.canvas.create_rectangle(redo[0][0], redo[0][1], redo[0][2], redo[0][3], width=4, outline=redo[2])
        self.canvas.create_text((redo[0][0]+redo[0][2])/2, redo[0][3]+15, text=redo[1][0], fill=redo[2],
                                font="Helvetica 15 bold")
        self.status_bar.update_action(f"Created `{redo[1]} bounding box at {redo[0]}")
        self.active_image.append_undo(redo)

    # Event Bindings
    def update_labels(self, _event: tk.Event):
        old_label = self.colour_picker.label
        self.colour_picker.on_entry_edit()
        new_label = self.colour_picker.label

        label_list = self.find_label_refs(old_label)
        for label in label_list:
            self.canvas.itemconfigure(label, text=new_label)

        for image in self.editable_images:
            for undo in image.undo_stack:
                if undo[1] == old_label:
                    undo[1] = new_label
            for redo in image.redo_stack:
                if redo[1] == old_label:
                    redo[1] = new_label

        self.status_bar.update_action(f"Changed {self.colour_picker.colour} label from `{old_label}` to `{new_label}`.")

    def on_mouse_press(self, event: tk.Event):
        self.start_x = event.x
        self.start_y = event.y
        self.current_box = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, width=4,
                                                        outline=self.colour_picker.colour)
        self.current_label = self.canvas.create_text(self.start_x, self.start_y+15, text=self.colour_picker.label,
                                                     fill=self.colour_picker.colour, font="Helvetica 15 bold")

    def on_mouse_move(self, event: tk.Event):
        self.current_x = event.x
        self.current_y = event.y
        self.canvas.coords(self.current_box, self.start_x, self.start_y, self.current_x, self.current_y)
        self.canvas.coords(self.current_label, ((self.start_x+self.current_x)/2, self.current_y+15))

    def on_mouse_release(self, _event: tk.Event):
        self.active_image.append_undo([self.canvas.coords(self.current_box), self.colour_picker.label,
                                       self.colour_picker.colour])

        self.status_bar.update_action(f"Created `{self.colour_picker.label}` bounding box at {self.canvas.coords(self.current_box)}")
        self.current_box = None
        self.active_image.redo_stack = []
        self.stack_change.set(not self.stack_change.get())
