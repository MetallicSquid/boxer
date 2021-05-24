import tkinter as tk
from PIL import ImageTk, Image
import os


class EditableImage:
    def __init__(self, image_path, canvas: tk.Canvas):
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


class ActiveCanvas:
    def __init__(self, input_path, master_frame: tk.Frame, colour_picker):
        self.canvas = tk.Canvas(master_frame, width=1280, height=720, bg="white", bd=5, relief=tk.GROOVE)
        self.canvas.pack(side=tk.TOP)

        self.colour_picker = colour_picker
        self.colour_picker.entry.bind("<KeyRelease>", self.update_labels)

        self.image_pointer = 0
        self.editable_images = []
        self.gather_images(input_path)
        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

        self.cur_undo_stack = []
        self.cur_redo_stack = []
        self.stack_populated = tk.BooleanVar()

        self.start_x, self.start_y = None, None
        self.current_x, self.current_y = None, None
        self.current_box = None
        self.current_label = None

    # FIXME: This should be handled in file_io and passed in as a list
    def gather_images(self, input_path):
        files = os.listdir(input_path)
        for file in files:
            extension = os.path.splitext(file)[1]
            if extension == ".jpg" or extension == ".png":
                image_path = os.path.join(input_path, file)
                self.editable_images.append(EditableImage(image_path, self.canvas))

    def shift_image(self, delta: int):
        self.active_image.undo_stack = self.cur_undo_stack
        self.active_image.redo_stack = self.cur_redo_stack

        self.image_pointer += delta
        self.active_image.deactivate_image()
        self.active_image = self.editable_images[self.image_pointer]
        self.active_image.activate_image()

        self.cur_undo_stack = self.active_image.undo_stack
        self.cur_redo_stack = self.active_image.redo_stack

        # FIXME: This whole trace system feels very hack-ish (it works, but I don't like it)
        self.stack_populated.set(not self.stack_populated)

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

    def undo_action(self):
        undo = self.cur_undo_stack.pop()
        self.canvas.delete(self.find_object_ref(undo[0]))
        self.canvas.delete(self.find_object_ref(undo[1][1]))

        self.cur_redo_stack.append(undo)

    def redo_action(self):
        redo = self.cur_redo_stack.pop()
        redo_box = self.canvas.create_rectangle(redo[0][0], redo[0][1], redo[0][2], redo[0][3], width=4,
                                                outline=redo[2])
        redo_label = self.canvas.create_text(redo[1][1][0], redo[1][1][1], text=redo[1][0], fill=redo[2],
                                             font="Helvetica 15 bold")

        self.cur_undo_stack.append((self.canvas.coords(redo_box),
                                    [self.canvas.itemcget(redo_label, "text"), self.canvas.coords(redo_label)],
                                    self.canvas.itemcget(redo_box, "outline")))

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
                                    [self.canvas.itemcget(self.current_label, "text"), self.canvas.coords(self.current_label)],
                                    self.canvas.itemcget(self.current_box, "outline")))

        self.current_box = None
        self.cur_redo_stack = []

        if not self.stack_populated.get():
            self.stack_populated.set(True)


