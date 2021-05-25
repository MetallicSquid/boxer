import tkinter as tk

from ui_elements import ColourPicker, UIHandler, StatusBar

root = tk.Tk()

main_frame = tk.Frame(root, bd=4)
main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

image_frame = tk.Frame(main_frame)
image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
canvas = tk.Canvas(image_frame, width=500, height=300, bg="white", bd=5, relief=tk.GROOVE)
canvas.pack(fill=tk.BOTH, expand=True)

tool_frame = tk.Frame(main_frame)
tool_frame.pack(side=tk.RIGHT)

colour_list = ["blue", "lime green", "yellow", "red", "deep pink"]
colour_box = tk.Listbox(tool_frame)
colour_box.grid(row=2, column=1, columnspan=2)
label_entry = tk.Entry(tool_frame)
label_entry.grid(row=3, column=1, columnspan=2)
colour_picker = ColourPicker(colour_list, colour_box, label_entry)

b_open = tk.Button(tool_frame, text="🔍 Open")
b_open.grid(row=1, column=1, columnspan=2)
b_undo = tk.Button(tool_frame, text="⏪ Undo")
b_undo.grid(row=4, column=1)
b_redo = tk.Button(tool_frame, text="️⏩️ Redo")
b_redo.grid(row=4, column=2)
b_prev = tk.Button(tool_frame, text="⏮️ Prev")
b_prev.grid(row=5, column=1)
b_next = tk.Button(tool_frame, text="⏭ Next️")
b_next.grid(row=5, column=2)
b_export = tk.Button(tool_frame, text="✈️ Export")
b_export.grid(row=6, column=1, columnspan=2)
buttons = (b_open, b_undo, b_redo, b_prev, b_next, b_export)

status_frame = tk.Frame(root, bd=1, relief=tk.SUNKEN)
status_frame.pack(side=tk.BOTTOM, fill=tk.X)
action_bar = tk.Label(status_frame, anchor=tk.W)
action_bar.pack(side=tk.LEFT)
info_bar = tk.Label(status_frame, anchor=tk.E)
info_bar.pack(side=tk.RIGHT)
status_bar = StatusBar(action_bar, info_bar)

ui_handler = UIHandler(canvas, colour_picker, buttons, status_bar)

root.mainloop()
