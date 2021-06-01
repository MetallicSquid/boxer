import tkinter as tk
import os
from collections import defaultdict


from info import InfoManager, load_dir
from canvas import EditableImage


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


# Handles button states and function calls for the tool bar
class ToolBar:
    def __init__(self, image_manager, info_entry,  colour_picker, buttons: tuple, status_bar):
        self.image_manager = image_manager
        self.info_entry = info_entry
        self.colour_picker = colour_picker
        self.status_bar = status_bar
        self.info_manager = InfoManager()

        self.image_manager.stack_change.trace_add("write", self.on_stack_change)

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

    # Button state checks
    def on_stack_change(self, _var, _index, _mode):
        if self.image_manager.active_image:
            self.stack_state(self.image_manager.active_image.undo_stack, self.undo_button)
            self.stack_state(self.image_manager.active_image.redo_stack, self.redo_button)
        self.prev_next_state()

    def stack_state(self, stack: list, button: tk.Button):
        if self.image_manager.active_image:
            if (button['state'] == tk.NORMAL or button['state'] == tk.ACTIVE) and not stack:
                button['state'] = tk.DISABLED
            elif button['state'] == tk.DISABLED and stack:
                button['state'] = tk.NORMAL
        else:
            button['state'] = tk.DISABLED

    def prev_next_state(self):
        index = self.image_manager.image_pointer
        image_no = len(self.image_manager.editable_images) - 1

        if (self.prev_button['state'] == tk.NORMAL or self.prev_button['state'] == tk.ACTIVE) and index == 0:
            self.prev_button['state'] = tk.DISABLED
        elif self.prev_button['state'] == tk.DISABLED and index != 0:
            self.prev_button['state'] = tk.NORMAL

        if image_no == -1:
            self.next_button['state'] = tk.DISABLED
        elif (self.next_button['state'] == tk.NORMAL or self.next_button['state'] == tk.ACTIVE) and index == image_no:
            self.next_button['state'] = tk.DISABLED
        elif self.next_button['state'] == tk.DISABLED and index != image_no:
            self.next_button['state'] = tk.NORMAL

    # Button pressed events
    def open_pressed(self):
        if self.info_manager.directory:
            self.info_manager.bulk_populate_fields(self.image_manager.editable_images)
            self.info_manager.write_coco()
            self.info_manager.write_colour_map()

        dir_info = load_dir(self.info_manager)
        if dir_info == "cancelled":
            self.info_manager.set_valid(False)
            print("The `🔍 Open` action was cancelled")
        elif dir_info == "invalid":
            self.info_manager.set_valid(False)
            self.image_manager.draw_invalid()
        elif dir_info == "read":
            self.info_manager.set_valid(True)
            self.info_entry.set_info(self.info_manager.info)
            self.image_manager.load_canvas(self.info_manager)
            self.colour_picker.remap_colour_picker(self.info_manager)

            self.stack_state(self.image_manager.active_image.undo_stack, self.undo_button)
            self.stack_state(self.image_manager.active_image.redo_stack, self.redo_button)
            self.prev_next_state()

            self.status_bar.update_action(f"Opened {self.info_manager.directory} containing {len(dir_info)} valid images.")
        elif type(dir_info) == list:
            self.info_manager.set_valid(True)
            self.image_manager.new_canvas(dir_info, self.info_manager)
            self.colour_picker.remap_colour_picker(self.info_manager)

            self.stack_state(self.image_manager.active_image.undo_stack, self.undo_button)
            self.stack_state(self.image_manager.active_image.redo_stack, self.redo_button)
            self.prev_next_state()

            self.status_bar.update_action(f"Opened {self.info_manager.directory} containing {len(dir_info)} valid images.")

    def undo_pressed(self):
        self.image_manager.undo_action()
        self.stack_state(self.image_manager.active_image.undo_stack, self.undo_button)
        self.stack_state(self.image_manager.active_image.redo_stack, self.redo_button)

    def redo_pressed(self):
        self.image_manager.redo_action()
        self.stack_state(self.image_manager.active_image.undo_stack, self.undo_button)
        self.stack_state(self.image_manager.active_image.redo_stack, self.redo_button)

    def prev_pressed(self):
        self.image_manager.shift_image(-1)
        self.prev_next_state()

    def next_pressed(self):
        self.image_manager.shift_image(1)
        self.prev_next_state()


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

    def canvas_state(self, history_manager):
        self.history_manager = history_manager

        if self.active_image:
            self.reset_canvas()
        else:
            self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
            self.canvas.bind("<B1-Motion>", self.on_mouse_move)
            self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
            self.colour_picker.entry.bind("<KeyRelease>", self.update_labels)

    def set_canvas(self):
        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        filename = os.path.basename(self.active_image.image_path)
        file_ratio = f"{self.image_pointer}/{len(self.editable_images)}"
        self.status_bar.update_info(f"{filename}    {file_ratio}")

        self.stack_change.set(not self.stack_change.get())

    def new_canvas(self, image_paths: list, history_manager):
        self.canvas_state(history_manager)

        for image_path in image_paths:
            editable_image = EditableImage(image_path, self.canvas)
            self.editable_images.append(editable_image)

        self.set_canvas()

    def load_canvas(self, history_manager):
        self.canvas_state(history_manager)

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

    # FIXME: I'm undecided on whether this should be here or not
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
