import tkinter as tk

from file_io import setup_image_dir, write_history
from canvas import ActiveCanvas

class ActionHandler:
    def __init__(self, canvas, colour_picker,  buttons: tuple):
        self.active_canvas = ActiveCanvas(canvas, colour_picker)
        self.active_canvas.stack_change.trace_add("write", self.upon_stack_change)
        self.history_path = None

        self.canvas = canvas
        self.colour_picker = colour_picker

        self.open_button = buttons[0]
        self.open_button.configure(command=self.open_pressed)

        self.undo_button = buttons[1]
        self.undo_button.configure(command=self.undo_pressed)
        self.redo_button = buttons[2]
        self.redo_button.configure(command=self.redo_pressed)
        self.undo_redo_state()

        self.prev_button = buttons[3]
        self.prev_button.configure(command=self.prev_pressed)
        self.next_button = buttons[4]
        self.next_button.configure(command=self.next_pressed)
        self.prev_next_state()

    # Button state checks
    def upon_stack_change(self, _var, _index, _mode):
        print("triggered")
        self.undo_redo_state()
        self.update_history()

    def undo_redo_state(self):
        undo_stack = self.active_canvas.cur_undo_stack
        redo_stack = self.active_canvas.cur_redo_stack

        if (self.undo_button['state'] == tk.NORMAL or self.undo_button['state'] == tk.ACTIVE) and not undo_stack:
            self.undo_button['state'] = tk.DISABLED
        elif self.undo_button['state'] == tk.DISABLED and undo_stack:
            self.undo_button['state'] = tk.NORMAL

        if (self.redo_button['state'] == tk.NORMAL or self.redo_button['state'] == tk.ACTIVE) and not redo_stack:
            self.redo_button['state'] = tk.DISABLED
        elif self.redo_button['state'] == tk.DISABLED and redo_stack:
            self.redo_button['state'] = tk.NORMAL

    def prev_next_state(self):
        index = self.active_canvas.image_pointer
        image_no = len(self.active_canvas.editable_images) - 1

        if (self.prev_button['state'] == tk.NORMAL or self.prev_button['state'] == tk.ACTIVE) and index == 0:
            self.prev_button['state'] = tk.DISABLED
        elif self.prev_button['state'] == tk.DISABLED and index != 0:
            self.prev_button['state'] = tk.NORMAL

        if (self.next_button['state'] == tk.NORMAL or self.next_button['state'] == tk.ACTIVE) and index == image_no:
            self.next_button['state'] = tk.DISABLED
        elif self.next_button['state'] == tk.DISABLED and index != image_no:
            self.next_button['state'] = tk.NORMAL

    # Button pressed events
    def open_pressed(self):
        image_paths, history_dict, history_path = setup_image_dir()
        self.history_path = history_path
        self.active_canvas.activate_canvas(image_paths, history_dict)

    def undo_pressed(self):
        self.active_canvas.undo_action()
        self.undo_redo_state()
        self.update_history()

    def redo_pressed(self):
        self.active_canvas.redo_action()
        self.undo_redo_state()
        self.update_history()

    def prev_pressed(self):
        self.active_canvas.shift_image(-1)
        self.prev_next_state()

    def next_pressed(self):
        self.active_canvas.shift_image(1)
        self.prev_next_state()

    # History logging
    def update_history(self):
        print(self.history_path)
        self.active_canvas.active_image.undo_stack = self.active_canvas.cur_undo_stack
        self.active_canvas.active_image.redo_stack = self.active_canvas.cur_redo_stack
        write_history(self.history_path, self.active_canvas.editable_images)


class ColourPicker:
    def __init__(self, colour_list: list, list_box: tk.Listbox, entry: tk.Entry):
        self.colour_list = colour_list
        self.entry = entry
        self.list_box = list_box
        list_box.bind("<<ListboxSelect>>", self.on_selection)

        self.label_dict = {}
        for i in range(len(colour_list)):
            list_box.insert(i, colour_list[i])
            self.label_dict[i] = colour_list[i]
        list_box.selection_set(0)

        self.selection = list_box.curselection()[0]
        self.colour = list_box.get(self.selection)
        self.label = self.label_dict[list_box.curselection()[0]]
        self.entry.insert(0, self.label)

    def on_entry_edit(self):
        self.label_dict[self.selection] = self.entry.get()
        self.label = self.label_dict[self.selection]

    def on_selection(self, _event: tk.Event):
        self.selection = self.list_box.curselection()[0]
        self.colour = self.list_box.get(self.selection)
        self.label = self.label_dict[self.selection]
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.label)
