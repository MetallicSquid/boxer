import tkinter as tk

from info import InfoManager, load_dir
from canvas import ImageManager


# Manages the ui events
class UIHandler:
    def __init__(self, canvas, colour_picker,  buttons: tuple, status_bar):
        self.canvas = canvas
        self.colour_picker = colour_picker
        self.status_bar = status_bar
        self.history_manager = InfoManager()

        self.active_canvas = ImageManager(canvas, colour_picker, status_bar)
        self.active_canvas.stack_change.trace_add("write", self.on_stack_change)
        self.history_path = None

        self.open_button = buttons[0]
        self.open_button.configure(command=self.open_pressed)

        self.undo_button = buttons[1]
        self.undo_button.configure(command=self.undo_pressed)
        self.redo_button = buttons[2]
        self.redo_button.configure(command=self.redo_pressed)

        self.prev_button = buttons[3]
        self.prev_button.configure(command=self.prev_pressed)
        self.next_button = buttons[4]
        self.next_button.configure(command=self.next_pressed)

        self.info_button = buttons[5]
        self.info_button.configure(command=self.info_pressed, state=tk.DISABLED)

        self.undo_redo_state()
        self.prev_next_state()

    def on_quit(self):
        if self.history_manager:
            self.history_manager.bulk_populate_fields(self.active_canvas.editable_images)
            self.history_manager.write_coco()
            self.history_manager.write_colour_map()

    # Button state checks
    def on_stack_change(self, _var, _index, _mode):
        self.undo_redo_state()
        self.prev_next_state()

    def undo_redo_state(self):
        if self.active_canvas.active_image:
            undo_stack = self.active_canvas.active_image.undo_stack
            redo_stack = self.active_canvas.active_image.redo_stack

            if (self.undo_button['state'] == tk.NORMAL or self.undo_button['state'] == tk.ACTIVE) and not undo_stack:
                self.undo_button['state'] = tk.DISABLED
            elif self.undo_button['state'] == tk.DISABLED and undo_stack:
                self.undo_button['state'] = tk.NORMAL

            if (self.redo_button['state'] == tk.NORMAL or self.redo_button['state'] == tk.ACTIVE) and not redo_stack:
                self.redo_button['state'] = tk.DISABLED
            elif self.redo_button['state'] == tk.DISABLED and redo_stack:
                self.redo_button['state'] = tk.NORMAL
        else:
            self.undo_button['state'] = tk.DISABLED
            self.redo_button['state'] = tk.DISABLED

    def prev_next_state(self):
        index = self.active_canvas.image_pointer
        image_no = len(self.active_canvas.editable_images) - 1

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
        if self.history_manager.directory:
            self.history_manager.bulk_populate_fields(self.active_canvas.editable_images)
            self.history_manager.write_coco()
            self.history_manager.write_colour_map()

        dir_info = load_dir(self.history_manager)
        if dir_info == "cancelled":
            print("The `🔍 Open` action was cancelled")
            self.info_button['state'] = tk.DISABLED
        elif dir_info == "invalid":
            self.active_canvas.draw_invalid()
            self.info_button['state'] = tk.DISABLED
        elif dir_info == "read":
            self.active_canvas.load_canvas(self.history_manager)
            self.colour_picker.remap_colour_picker(self.history_manager)

            self.undo_redo_state()
            self.prev_next_state()
            self.info_button['state'] = tk.NORMAL

            self.status_bar.update_action(f"Opened {self.history_manager.directory} containing {len(dir_info)} valid images.")
        elif type(dir_info) == list:
            self.active_canvas.new_canvas(dir_info, self.history_manager)
            self.colour_picker.remap_colour_picker(self.history_manager)

            self.undo_redo_state()
            self.prev_next_state()
            self.info_button['state'] = tk.NORMAL

            self.status_bar.update_action(f"Opened {self.history_manager.directory} containing {len(dir_info)} valid images.")

    def undo_pressed(self):
        self.active_canvas.undo_action()
        self.undo_redo_state()

    def redo_pressed(self):
        self.active_canvas.redo_action()
        self.undo_redo_state()

    def prev_pressed(self):
        self.active_canvas.shift_image(-1)
        self.prev_next_state()

    def next_pressed(self):
        self.active_canvas.shift_image(1)
        self.prev_next_state()

    def info_pressed(self):
        InfoWidget(self.history_manager)


# Manages the colour listbox and label selector
class ColourPicker:
    def __init__(self, colour_list: list, list_box: tk.Listbox, entry: tk.Entry):
        self.colour_list = colour_list
        self.entry = entry
        self.list_box = list_box
        self.history_manager = None

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

    def remap_colour_picker(self, history_manager):
        self.history_manager = history_manager
        self.index_label_dict = {}
        self.list_box.delete(0, tk.END)

        count = 0
        for key, value in self.history_manager.colour_map.items():
            self.list_box.insert(count, key)
            self.index_label_dict[count] = value
            count += 1

        self.list_box.selection_set(0)
        self.update_colour_picker()

    def on_entry_edit(self):
        self.index_label_dict[self.selection] = self.entry.get()
        self.label = self.index_label_dict[self.selection]
        self.history_manager.colour_map[self.colour] = self.label

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


class InfoWidget:
    def __init__(self, history_manager):
        self.history_manager = history_manager
        self.widget = tk.Toplevel()
        self.widget.title("Boxer")

        tk.Label(self.widget, text="Dataset Information", font="Helvetica 15 bold")
