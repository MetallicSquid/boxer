import tkinter as tk

from info import InfoManager, load_dir
from canvas import ImageManager


# Manages the ui events
class UIHandler:
    def __init__(self, canvas, colour_picker,  buttons: tuple, status_bar):
        self.canvas = canvas
        self.colour_picker = colour_picker
        self.status_bar = status_bar
        self.info_manager = InfoManager()

        self.image_manager = ImageManager(canvas, colour_picker, status_bar)
        self.image_manager.stack_change.trace_add("write", self.on_stack_change)
        self.history_path = None

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
