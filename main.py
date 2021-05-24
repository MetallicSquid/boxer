import tkinter as tk
from tkinter import filedialog
import argparse
import os

from canvas import ActiveCanvas
from ui_handlers import ColourPicker, ButtonHandler
from file_io import file_browser

root = tk.Tk()


parser = argparse.ArgumentParser()
parser.add_argument("input_dir", help="The directory of images to be edited")
parser.add_argument("output_dir", help="The directory for the edited images to be placed")
args = parser.parse_args()

image_dir = os.path.expanduser(args.input_dir)

picture_frame = tk.Frame(root)
picture_frame.grid(row=1, column=1, rowspan=16)

colour_list = ["blue", "lime green", "yellow", "red", "deep pink"]
colour_box = tk.Listbox(root)
colour_box.grid(row=1, column=2, columnspan=2)
label_entry = tk.Entry(root)
label_entry.grid(row=2, column=2, columnspan=2)

colour_picker = ColourPicker(colour_list, colour_box, label_entry)
active_canvas = ActiveCanvas(image_dir, picture_frame, colour_picker)

undo_button = tk.Button(root, text="⏪ Undo")
undo_button.grid(row=3, column=2)

redo_button = tk.Button(root, text="️⏩️ Redo")
redo_button.grid(row=3, column=3)

prev_button = tk.Button(root, text="⏮️ Prev")
prev_button.grid(row=4, column=2)

next_button = tk.Button(root, text="⏭ Next️")
next_button.grid(row=4, column=3)

# open_button = tk.Button(root, text="🔍 Open", command=file_browser)
# open_button.grid(row=2, column=4)

event_handler = ButtonHandler(active_canvas, (undo_button, redo_button, prev_button, next_button))

root.mainloop()

# TODO: Have a simple UI with the image as the primary focus, keep the cruft to a minimum
