import tkinter as tk
from PIL import ImageTk, Image
import os


# Represents each instance of an image that can be edited
class EditableImage:
    def __init__(self, image_path, canvas: tk.Canvas):
        self.image_path = image_path
        self.canvas = canvas

        load = Image.open(image_path)
        self.image = ImageTk.PhotoImage(load)
        self.width = load.width
        self.height = load.height

        self.undo_stack = []
        self.redo_stack = []

    def activate_image(self):
        self.canvas.configure(width=self.width, height=self.height)
        self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        for draw_coords in self.undo_stack:
            self.canvas.create_rectangle(draw_coords[0][0], draw_coords[0][1], draw_coords[0][2], draw_coords[0][3],
                                         width=4, outline=draw_coords[2])
            self.canvas.create_text(draw_coords[1][1][0], draw_coords[1][1][1], text=draw_coords[1][0],
                                    fill=draw_coords[2], font="Helvetica 15 bold")

    def deactivate_image(self):
        self.canvas.delete("all")

# Represents the canvas itself and the actions that can be performed with it
class ActiveCanvas:
    def __init__(self, canvas, colour_picker, status_bar):
        self.canvas = canvas
        self.colour_picker = colour_picker
        self.status_bar = status_bar
        self.history_manager = None

        self.image_pointer = 0
        self.editable_images = []
        self.active_image = None

        self.cur_undo_stack = []
        self.cur_redo_stack = []
        self.stack_change = tk.BooleanVar()

        self.start_x, self.start_y = None, None
        self.current_x, self.current_y = None, None
        self.current_box = None
        self.current_label = None

        self.draw_startup()

    # Placeholder screens
    def draw_placeholder(self, title, subtitle, description):
        self.canvas.configure(width=500, height=300)
        self.deactivate_canvas()
        self.canvas.create_text(20, 20, text=title, fill="black", font="Helvetica 30 bold", anchor=tk.NW)
        self.canvas.create_text(20, 70, text=subtitle, fill="gray", font="Helvetica 20 italic", anchor=tk.NW)
        self.canvas.create_text(20, 120, text=description, fill="black", font="Helvetica 15", anchor=tk.NW)

    def draw_startup(self):
        title = "Boxer 🥊"
        subtitle = "The simple bounding box tool"
        description = "To start annotating images, press the `🔍 Open`\nbutton and pick a relevant directory. If you need\nany help, please reference the docs. Enjoy!"
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
        self.cur_undo_stack = []
        self.cur_redo_stack = []
        self.editable_images = []
        self.image_pointer = 0
        self.current_box = None
        self.current_label = None

    def deactivate_canvas(self):
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.colour_picker.entry.unbind("<KeyRelease>")
        self.reset_canvas()

        self.stack_change.set(not self.stack_change.get())

    def activate_canvas(self, image_paths: list, history_manager):
        self.history_manager = history_manager

        # FIXME: The bindings are being unbound and then immediately rebound to the same functions
        if self.active_image:
            self.deactivate_canvas()

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.colour_picker.entry.bind("<KeyRelease>", self.update_labels)

        for image_path in image_paths:
            editable_image = EditableImage(image_path, self.canvas)
            image_stacks = history_manager.history_stack[os.path.basename(image_path)]
            editable_image.undo_stack = image_stacks['undo']
            editable_image.redo_stack = image_stacks['redo']
            self.editable_images.append(editable_image)

        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        self.cur_undo_stack = self.active_image.undo_stack
        self.cur_redo_stack = self.active_image.redo_stack

        filename = os.path.basename(self.active_image.image_path)
        file_ratio = f"{self.image_pointer}/{len(self.editable_images)}"
        self.status_bar.update_info(f"{filename}    {file_ratio}")

    def shift_image(self, delta: int):
        self.active_image.undo_stack = self.cur_undo_stack
        self.active_image.redo_stack = self.cur_redo_stack
        self.history_manager.update_canvas(self.editable_images)

        self.image_pointer += delta
        self.active_image.deactivate_image()
        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        self.cur_undo_stack = self.active_image.undo_stack
        self.cur_redo_stack = self.active_image.redo_stack
        self.status_bar.update_action(f"Moved to image {self.image_pointer+1} out of {len(self.editable_images)}.")

        filename = os.path.basename(self.active_image.image_path)
        file_ratio = f"{self.image_pointer}/{len(self.editable_images)}"
        self.status_bar.update_info(f"{filename}    |    {file_ratio}")

        # FIXME: This whole trace system feels very hack-ish, this should probably be changed in the future
        self.stack_change.set(not self.stack_change.get())

    def find_object_ref(self, coords: list):
        for object_ref in self.canvas.find_all():
            if self.canvas.coords(object_ref) == coords:
                return object_ref
        raise IndexError(f"The requested object, with coords {coords}, does not exist")

    def find_label_refs(self, label: str):
        ref_list = []
        for object_ref in self.canvas.find_all():
            if self.canvas.type(object_ref) == "text":
                if self.canvas.itemcget(object_ref, "text") == label:
                    ref_list.append(object_ref)

        return ref_list

    # Undo and redo events
    def undo_action(self):
        undo = self.cur_undo_stack.pop()
        self.canvas.delete(self.find_object_ref(undo[0]))
        self.canvas.delete(self.find_object_ref(undo[1][1]))
        self.status_bar.update_action(f"Removed `{undo[1][0]}` bounding box at {undo[0]}")
        self.cur_redo_stack.append(undo)

    def redo_action(self):
        redo = self.cur_redo_stack.pop()
        redo_box = self.canvas.create_rectangle(redo[0][0], redo[0][1], redo[0][2], redo[0][3], width=4,
                                                outline=redo[2])
        redo_label = self.canvas.create_text(redo[1][1][0], redo[1][1][1], text=redo[1][0], fill=redo[2],
                                             font="Helvetica 15 bold")
        self.status_bar.update_action(f"Created `{redo[1][0]}` bounding box at {redo[0]}")
        self.cur_undo_stack.append((self.canvas.coords(redo_box),
                                    [self.canvas.itemcget(redo_label, "text"), self.canvas.coords(redo_label)],
                                    self.canvas.itemcget(redo_box, "outline")))

    # FIXME: I think the UIHandler should be managing this, not the canvas
    # Event Bindings
    def update_labels(self, _event: tk.Event):
        old_label = self.colour_picker.label
        self.colour_picker.on_entry_edit()
        new_label = self.colour_picker.label

        label_list = self.find_label_refs(old_label)
        for label in label_list:
            self.canvas.itemconfigure(label, text=new_label)

        for undo in self.cur_undo_stack:
            if undo[1][0] == old_label:
                undo[1][0] = new_label
        for redo in self.cur_redo_stack:
            if redo[1][0] == old_label:
                redo[1][0] = new_label

        for image in self.editable_images:
            for undo in image.undo_stack:
                if undo[1][0] == old_label:
                    undo[1][0] = new_label
            for redo in image.redo_stack:
                if redo[1][0] == old_label:
                    redo[1][0] = new_label

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
        self.cur_undo_stack.append((self.canvas.coords(self.current_box),
                                    [self.colour_picker.label, self.canvas.coords(self.current_label)],
                                    self.canvas.itemcget(self.current_box, "outline")))
        self.status_bar.update_action(f"Created `{self.colour_picker.label}` bounding box at {self.canvas.coords(self.current_box)}")
        self.current_box = None
        self.cur_redo_stack = []
        self.stack_change.set(not self.stack_change.get())
