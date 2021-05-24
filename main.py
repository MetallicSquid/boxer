import tkinter as tk
import argparse
import os

from elements import ColourPicker, ActionHandler

root = tk.Tk()

parser = argparse.ArgumentParser()
parser.add_argument("input_dir", help="The directory of images to be edited")
args = parser.parse_args()

image_dir = os.path.expanduser(args.input_dir)

picture_frame = tk.Frame(root)
picture_frame.grid(row=1, column=1, rowspan=16)
canvas = tk.Canvas(picture_frame, width=1280, height=720, bg="white", bd=5, relief=tk.GROOVE)
canvas.pack(side=tk.TOP)

colour_list = ["blue", "lime green", "yellow", "red", "deep pink"]
colour_box = tk.Listbox(root)
colour_box.grid(row=2, column=2, columnspan=2)
label_entry = tk.Entry(root)
label_entry.grid(row=3, column=2, columnspan=2)
colour_picker = ColourPicker(colour_list, colour_box, label_entry)

b_open = tk.Button(root, text="🔍 Open")
b_open.grid(row=1, column=2, columnspan=2)
b_undo = tk.Button(root, text="⏪ Undo")
b_undo.grid(row=4, column=2)
b_redo = tk.Button(root, text="️⏩️ Redo")
b_redo.grid(row=4, column=3)
b_prev = tk.Button(root, text="⏮️ Prev")
b_prev.grid(row=5, column=2)
b_next = tk.Button(root, text="⏭ Next️")
b_next.grid(row=5, column=3)

action_handler = ActionHandler(canvas, colour_picker, (b_open, b_undo, b_redo, b_prev, b_next))

root.mainloop()
