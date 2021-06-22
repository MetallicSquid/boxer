import tkinter as tk
import os
from collections import defaultdict


from info import InfoManager, load_dir
from objects import EditableImage, Annotation, BoundingBox, Polygon
from operations import adjust_point


def write_entry(entry, string: str):
    entry.delete(0, tk.END)
    entry.insert(0, string)


def write_text(entry, string: str):
    entry.delete(1.0, tk.END)
    entry.insert(1.0, string)


class InfoEntry:
    def __init__(self, entries: tuple):
        self.year = None
        self.version = ""
        self.description = ""
        self.contributor = ""
        self.url = ""

        self.year_entry = entries[0]
        self.version_entry = entries[1]
        self.description_entry = entries[2]
        self.contributor_entry = entries[3]
        self.url_entry = entries[4]

        self.set_default()

    def read_entries(self):
        self.year = self.year_entry.get()
        self.version = self.version_entry.get()
        self.description = self.description_entry.get(1.0, tk.END)
        self.contributor = self.contributor_entry.get(1.0, tk.END)
        self.url = self.url_entry.get(1.0, tk.END)

    def write_entries(self):
        write_entry(self.year_entry, self.year)
        write_entry(self.version_entry, self.version)
        write_text(self.description_entry, self.description)
        write_text(self.contributor_entry, self.contributor)
        write_text(self.url_entry, self.url)

    def save_entries(self, info_manager: InfoManager):
        self.read_entries()
        info_manager.populate_info(self.year, self.version, self.description, self.contributor, self.url)

    def set_default(self):
        self.year = "2021"
        self.version = "0.1.0"
        self.description = "Boxer: The simple bounding box tool"
        self.contributor = "Guillaume Macneil"
        self.url = "https://www.github.com/MetallicSquid/boxer"
        self.write_entries()

    def set_info(self, info: dict):
        self.year = info["year"]
        self.version = info["version"]
        self.description = info["description"]
        self.contributor = info["contributor"]
        self.url = info["url"]
        self.write_entries()


class StateManager:
    def __init__(self, info_entry: InfoEntry, colour_picker, tool_buttons: tuple):
        self.colour_picker = colour_picker
        self.info_entry = info_entry
        self.open_button = tool_buttons[0]
        self.undo_button = tool_buttons[1]
        self.redo_button = tool_buttons[2]
        self.prev_button = tool_buttons[3]
        self.next_button = tool_buttons[4]

    def colour_picker_state(self, valid: bool):
        if valid:
            self.colour_picker.list_box['state'] = tk.NORMAL
            self.colour_picker.entry['state'] = tk.NORMAL
        else:
            self.colour_picker.list_box['state'] = tk.DISABLED
            self.colour_picker.entry['state'] = tk.DISABLED

    def info_entry_state(self, valid: bool):
        if valid:
            self.info_entry.year_entry['state'] = tk.NORMAL
            self.info_entry.version_entry['state'] = tk.NORMAL
            self.info_entry.description_entry['state'] = tk.NORMAL
            self.info_entry.contributor_entry['state'] = tk.NORMAL
            self.info_entry.url_entry['state'] = tk.NORMAL
        else:
            self.info_entry.year_entry['state'] = tk.DISABLED
            self.info_entry.version_entry['state'] = tk.DISABLED
            self.info_entry.description_entry['state'] = tk.DISABLED
            self.info_entry.contributor_entry['state'] = tk.DISABLED
            self.info_entry.url_entry['state'] = tk.DISABLED

    def undo_state(self, undo_stack: list):
        if undo_stack:
            self.undo_button['state'] = tk.NORMAL
        else:
            self.undo_button['state'] = tk.DISABLED

    def redo_state(self, redo_stack: list):
        if redo_stack:
            self.redo_button['state'] = tk.NORMAL
        else:
            self.redo_button['state'] = tk.DISABLED

    def prev_state(self, index: int):
        if index == 0:
            self.prev_button['state'] = tk.DISABLED
        else:
            self.prev_button['state'] = tk.NORMAL

    def next_state(self, index: int, image_no: int):
        if image_no == -1 or image_no == index:
            self.next_button['state'] = tk.DISABLED
        else:
            self.next_button['state'] = tk.NORMAL

    def deactivate_tool_buttons(self):
        self.undo_button['state'] = tk.DISABLED
        self.redo_button['state'] = tk.DISABLED
        self.prev_button['state'] = tk.DISABLED
        self.next_button['state'] = tk.DISABLED


# Handles function calls for the tool bar
class ToolBar:
    def __init__(self, image_manager, info_entry,  colour_picker, buttons: tuple, status_bar, state_handler):
        self.image_manager = image_manager
        self.info_entry = info_entry
        self.colour_picker = colour_picker
        self.status_bar = status_bar
        self.state_handler = state_handler
        self.info_manager = InfoManager()

        self.state_handler.deactivate_tool_buttons()
        self.state_handler.colour_picker_state(False)
        self.state_handler.info_entry_state(False)

        self.open_button = buttons[0]
        self.open_button.configure(command=self.open_pressed)
        self.undo_button = buttons[1]
        self.undo_button.configure(command=self.undo_pressed, state=tk.DISABLED)
        self.redo_button = buttons[2]
        self.redo_button.configure(command=self.redo_pressed, state=tk.DISABLED)
        self.prev_button = buttons[3]
        self.prev_button.configure(command=self.prev_pressed, state=tk.DISABLED)
        self.next_button = buttons[4]
        self.next_button.configure(command=self.next_pressed, state=tk.DISABLED)

    def on_quit(self):
        if self.info_manager:
            self.info_manager.bulk_populate_fields(self.image_manager.editable_images)
            self.info_entry.save_entries(self.info_manager)
            self.info_manager.write_coco()
            self.info_manager.write_colour_map()

    # Button pressed events
    def open_pressed(self):
        if self.info_manager.directory:
            self.info_manager.bulk_populate_fields(self.image_manager.editable_images)
            self.info_manager.write_coco()
            self.info_manager.write_colour_map()

        dir_info = load_dir(self.info_manager)
        if dir_info == "cancelled":
            print("The `🔍 Open` action was cancelled")
        elif dir_info == "invalid":
            self.info_manager.set_valid(False)
            self.state_handler.colour_picker_state(False)
            self.state_handler.info_entry_state(False)
            self.state_handler.deactivate_tool_buttons()

            self.image_manager.draw_invalid()
        elif dir_info == "read":
            self.info_manager.set_valid(True)
            self.info_entry.set_info(self.info_manager.info)
            self.image_manager.load_canvas(self.info_manager)
            self.state_handler.colour_picker_state(True)
            self.state_handler.info_entry_state(True)
            self.colour_picker.remap_colour_picker(self.info_manager)

            self.state_handler.undo_state(self.image_manager.active_image.undo_stack)
            self.state_handler.redo_state(self.image_manager.active_image.redo_stack)
            self.state_handler.prev_state(self.image_manager.image_pointer)
            self.state_handler.next_state(self.image_manager.image_pointer, len(self.image_manager.editable_images))

            self.status_bar.update_action(f"Opened {self.info_manager.directory} containing {len(dir_info)} valid images.")
        elif type(dir_info) == list:
            self.info_manager.set_valid(True)
            self.image_manager.new_canvas(dir_info, self.info_manager)
            self.state_handler.colour_picker_state(True)
            self.state_handler.info_entry_state(True)
            self.colour_picker.remap_colour_picker(self.info_manager)

            self.state_handler.undo_state(self.image_manager.active_image.undo_stack)
            self.state_handler.redo_state(self.image_manager.active_image.redo_stack)
            self.state_handler.prev_state(self.image_manager.image_pointer)
            self.state_handler.next_state(self.image_manager.image_pointer, len(self.image_manager.editable_images))

            self.status_bar.update_action(f"Opened {self.info_manager.directory} containing {len(dir_info)} valid images.")

    def undo_pressed(self):
        self.image_manager.undo_action()

    def redo_pressed(self):
        self.image_manager.redo_action()

    def prev_pressed(self):
        self.image_manager.shift_image(-1)
        self.state_handler.prev_state(self.image_manager.image_pointer)
        self.state_handler.next_state(self.image_manager.image_pointer, len(self.image_manager.editable_images))

    def next_pressed(self):
        self.image_manager.shift_image(1)
        self.state_handler.prev_state(self.image_manager.image_pointer)
        self.state_handler.next_state(self.image_manager.image_pointer, len(self.image_manager.editable_images))


# Manages the colour listbox and label selector
class ColourPicker:
    def __init__(self, colour_list: list, list_box: tk.Listbox, entry: tk.Entry):
        self.colour_list = colour_list
        self.entry = entry
        self.list_box = list_box
        self.info_manager = None

        list_box.bind("<<ListboxSelect>>", self.on_selection)

        self.index_label_dict = {}
        for i in range(len(colour_list)):
            list_box.insert(i, colour_list[i])
            self.index_label_dict[i] = colour_list[i]
        list_box.selection_set(0)

        self.selection = list_box.curselection()[0]
        self.colour = list_box.get(self.selection)
        self.label = self.index_label_dict[self.selection]
        self.entry.insert(0, self.label)

    def update_colour_picker(self):
        self.selection = self.list_box.curselection()[0]
        self.colour = self.list_box.get(self.selection)
        self.label = self.index_label_dict[self.selection]
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.label)

    def remap_colour_picker(self, info_manager):
        self.info_manager = info_manager
        self.index_label_dict = {}
        self.list_box.delete(0, tk.END)

        count = 0
        for key, value in self.info_manager.colour_map.items():
            self.list_box.insert(count, key)
            self.index_label_dict[count] = value
            count += 1

        self.list_box.selection_set(0)
        self.update_colour_picker()

    def on_entry_edit(self):
        self.index_label_dict[self.selection] = self.entry.get()
        self.label = self.index_label_dict[self.selection]
        self.info_manager.colour_map[self.colour] = self.label

    def on_selection(self, _event: tk.Event):
        self.update_colour_picker()


# The status bar that shows the most recent action and information about the current file
class StatusBar:
    def __init__(self, action_bar: tk.Label, info_bar: tk.Label):
        self.action_bar = action_bar
        self.info_bar = info_bar

    def update_action(self, action_string: str):
        self.action_bar.configure(text=action_string)

    def update_info(self, info_string: str):
        self.info_bar.configure(text=info_string)


# Manages the image on the canvas and the actions that can be performed on it
class ImageManager:
    def __init__(self, canvas: tk.Canvas, colour_picker, status_bar, state_manager):
        self.canvas = canvas
        self.colour_picker = colour_picker
        self.status_bar = status_bar
        self.state_manager = state_manager
        self.history_manager = None

        self.width = self.canvas.winfo_width()
        self.height = self.canvas.winfo_height()

        self.image_pointer = 0
        self.editable_images = []
        self.active_image = None

        self.draw_startup()

    # Placeholder screens
    def draw_placeholder(self, title, subtitle, description):
        self.deactivate_canvas()
        self.reset_canvas()
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

        self.state_manager.deactivate_tool_buttons()

    def deactivate_canvas(self):
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<ButtonPress-3>")
        self.colour_picker.entry.unbind("<KeyRelease>")

    # FIXME: This can probably be dropped
    def canvas_state(self, history_manager):
        self.history_manager = history_manager

        if self.active_image:
            self.reset_canvas()
        else:
            self.canvas.delete("all")

    def set_canvas(self):
        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        filename = os.path.basename(self.active_image.image_path)
        file_ratio = f"{self.image_pointer}/{len(self.editable_images)}"
        self.status_bar.update_info(f"{filename}    {file_ratio}")

        self.state_manager.undo_state(self.active_image.undo_stack)
        self.state_manager.redo_state(self.active_image.redo_stack)
        self.state_manager.prev_state(self.image_pointer)
        self.state_manager.next_state(self.image_pointer, len(self.editable_images))

    def new_canvas(self, image_paths: list, history_manager):
        self.canvas_state(history_manager)

        for image_path in image_paths:
            editable_image = EditableImage(image_path, self.canvas, self.state_manager)
            self.editable_images.append(editable_image)
            self.set_tool_bbox()

        self.set_canvas()

    def load_canvas(self, history_manager):
        self.canvas_state(history_manager)

        directory = self.history_manager.directory
        images = self.history_manager.images
        annotations = self.history_manager.annotations

        bbox_dict = defaultdict(list)
        id_category_map = self.history_manager.make_id_category_map()
        id_colour_map = self.history_manager.make_id_colour_map()

        # FIXME: This needs to be updated for the new annotation model
        for annotation in annotations:
            coords = [annotation["bbox"][0], annotation["bbox"][1], annotation["bbox"][0]+annotation["bbox"][2],
                      annotation["bbox"][1]+annotation["bbox"][3]]
            label = id_category_map[annotation["category_id"]]
            colour = id_colour_map[label]

            bbox_dict[annotation["image_id"]].append(BoundingBox(self.canvas, coords, label, colour))

        for image in images:
            path = os.path.join(directory, image["file_name"])
            editable_image = EditableImage(path, self.canvas)
            editable_image.undo_stack = bbox_dict[image["id"]]
            self.editable_images.append(editable_image)

        self.set_canvas()

    def shift_image(self, delta: int):
        self.image_pointer += delta
        self.active_image.deactivate_image()
        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        self.status_bar.update_action(f"Moved to image {self.image_pointer+1} out of {len(self.editable_images)}.")
        filename = os.path.basename(self.active_image.image_path)
        file_ratio = f"{self.image_pointer}/{len(self.editable_images)}"
        self.status_bar.update_info(f"{filename}    {file_ratio}")

        self.state_manager.undo_state(self.active_image.undo_stack)
        self.state_manager.redo_state(self.active_image.redo_stack)
        self.state_manager.prev_state(self.image_pointer)
        self.state_manager.next_state(self.image_pointer, len(self.editable_images))

    # Undo and redo events
    def undo_action(self):
        undo = self.active_image.pop_undo()
        self.state_manager.undo_state(self.active_image.undo_stack)
        undo.delete()
        self.active_image.append_redo(undo)
        self.state_manager.redo_state(self.active_image.redo_stack)
        self.active_image.annotation.update_annotation_after_undo()

        if not self.active_image.annotation.is_active_bbox():
            self.set_tool_bbox()
            self.active_image.annotations.pop()

    def redo_action(self):
        redo = self.active_image.pop_redo()
        self.state_manager.redo_state(self.active_image.redo_stack)
        redo.draw()
        self.active_image.append_undo(redo)
        self.state_manager.undo_state(self.active_image.undo_stack)
        self.active_image.annotation.update_annotation_after_redo(redo)

    # Tool changes
    def set_tool_bbox(self):
        self.deactivate_canvas()
        self.canvas.bind("<ButtonPress-1>", self.bbox_on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.bbox_on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.bbox_on_mouse_release)
        self.colour_picker.entry.bind("<KeyRelease>", self.update_labels)

    def set_tool_polygon(self):
        self.deactivate_canvas()
        self.canvas.bind("<ButtonPress-1>", self.poly_on_mouse_press)
        self.canvas.bind("<ButtonPress-3>", self.end_annotation)
        self.colour_picker.entry.bind("<KeyRelease>", self.update_labels)

    # Event Bindings
    def update_labels(self, _event: tk.Event):
        old_label = self.colour_picker.label
        self.colour_picker.on_entry_edit()
        new_label = self.colour_picker.label

        for image in self.editable_images:
            for undo in image.undo_stack:
                if undo.get_label() == old_label:
                    undo.change_label(new_label)
            for redo in image.redo_stack:
                if redo.get_label() == old_label:
                    redo.change_label(new_label)

        self.status_bar.update_action(f"Changed {self.colour_picker.colour} label to `{new_label}`.")

    # Bounding box actions
    def bbox_on_mouse_press(self, event: tk.Event):
        self.active_image.annotation = Annotation(self.canvas, self.state_manager)
        self.active_image.annotation.set_label(self.colour_picker.label, self.colour_picker.colour)
        self.active_image.annotation.set_bbox(BoundingBox(self.canvas, [event.x, event.y, event.x, event.y],
                                                          self.colour_picker.label, self.colour_picker.colour))
        self.active_image.annotation.draw_bbox()

    def bbox_on_mouse_move(self, event: tk.Event):
        x, y = adjust_point((event.x, event.y), self.active_image.width, self.active_image.height)
        start_x, start_y = self.active_image.annotation.bbox.get_coords()[:2]
        if x < start_x and y < start_y:
            self.active_image.annotation.bbox.start_x = x
            self.active_image.annotation.bbox.start_y = y
        elif x < start_x:
            self.active_image.annotation.bbox.start_x = x
        elif y < start_y:
            self.active_image.annotation.bbox.start_y = y
        self.active_image.annotation.adjust_bbox(x, y)

    def bbox_on_mouse_release(self, _event: tk.Event):
        self.active_image.append_undo(self.active_image.annotation.get_bbox())
        self.active_image.append_annotation(self.active_image.annotation)

        self.set_tool_polygon()

        self.status_bar.update_action(f"Created `{self.active_image.annotation.get_label()}` bounding box at {self.active_image.annotation.get_bbox_coords()}")

        self.active_image.redo_stack = []
        self.state_manager.undo_state(self.active_image.undo_stack)
        self.state_manager.redo_state(self.active_image.redo_stack)

    # Polygon actions
    def adjust_poly_point(self, event: tk.Event):
        bbox = self.active_image.annotation.bbox.get_coords()
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return adjust_point((event.x, event.y), width, height, rel_x=bbox[0], rel_y=bbox[1])

    def poly_on_mouse_press(self, event: tk.Event):
        if not self.active_image.annotation.bbox:
            self.set_tool_bbox()
            self.bbox_on_mouse_press(event)
        else:
            if self.active_image.annotation.is_active_polygon():
                if not self.active_image.annotation.resume_polygon(event.x, event.y):
                    self.active_image.annotation.end_polygon_segment()
                    if self.active_image.annotation.get_segment() not in self.active_image.undo_stack:
                        self.active_image.append_undo(self.active_image.annotation.get_segment())
            else:
                x, y = self.adjust_poly_point(event)
                if x == event.x and y == event.y:
                    self.active_image.annotation.set_polygon(Polygon(self.canvas, self.active_image.annotation.get_colour(), x, y))
                    self.active_image.annotation.draw_polygon_segment()
                    self.canvas.bind("<Motion>", self.poly_on_mouse_move)

        self.active_image.redo_stack = []
        self.state_manager.undo_state(self.active_image.undo_stack)
        self.state_manager.redo_state(self.active_image.redo_stack)

    def poly_on_mouse_move(self, event: tk.Event):
        if self.active_image.annotation.is_active_polygon():
            if self.active_image.annotation.is_active_segment():
                x, y = self.adjust_poly_point(event)
                self.active_image.annotation.adjust_polygon_segment(x, y)

    def end_annotation(self, _event: tk.Event):
        self.set_tool_bbox()

