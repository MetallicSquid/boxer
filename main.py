import tkinter as tk

from canvas import ImageManager
from ui_elements import InfoEntry, ColourPicker, ToolBar, StatusBar

root = tk.Tk()
root.title("Boxer")

# The status bar at the bottom of the screen
status_frame = tk.Frame(root, bd=1, relief=tk.SUNKEN)
status_frame.pack(side=tk.BOTTOM, fill=tk.X)
action_bar = tk.Label(status_frame, anchor=tk.W)
action_bar.pack(side=tk.LEFT)
info_bar = tk.Label(status_frame, anchor=tk.E)
info_bar.pack(side=tk.RIGHT)
status_bar = StatusBar(action_bar, info_bar)

# The information entry fields at the top of the screen
info_frame = tk.Frame(root)
info_frame.pack(side=tk.TOP)
year_label = tk.Label(info_frame, text="Year: ", font="Helvetica 10")
year_label.grid(row=0, column=0)
year_entry = tk.Entry(info_frame, width=4)
year_entry.grid(row=0, column=1)
version_label = tk.Label(info_frame, text="Version: ", font="Helvetica 10")
version_label.grid(row=1, column=0)
version_entry = tk.Entry(info_frame, width=6)
version_entry.grid(row=1, column=1)
description_label = tk.Label(info_frame, text="Description: ", font="Helvetica 10")
description_label.grid(row=0, column=2, rowspan=2)
description_entry = tk.Text(info_frame, width=20, height=3, wrap=tk.WORD)
description_entry.grid(row=0, column=3, rowspan=2)
contributor_label = tk.Label(info_frame,  text="Contributor: ", font="Helvetica 10")
contributor_label.grid(row=0, column=4, rowspan=2)
contributor_entry = tk.Text(info_frame, width=20, height=3, wrap=tk.WORD)
contributor_entry.grid(row=0, column=5, rowspan=2)
url_label = tk.Label(info_frame, text="Project Url: ", font="Helvetica 10")
url_label.grid(row=0, column=6, rowspan=2)
url_entry = tk.Text(info_frame, width=20, height=3)
url_entry.grid(row=0, column=7, rowspan=2)
entries = (year_entry, version_entry, description_entry, contributor_entry, url_entry)
info_entry = InfoEntry(entries)

# The tool bar on the right side of the screen
tool_frame = tk.Frame(root)
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
buttons = (b_open, b_undo, b_redo, b_prev, b_next)

box_label = tk.Label(tool_frame, text="Box: ")
box_label.grid(row=6, column=1)
box_check = tk.Checkbutton(tool_frame)
box_check.grid(row=6, column=2)
polygon_label = tk.Label(tool_frame, text="Polygon: ")
polygon_label.grid(row=7, column=1)
polygon_check = tk.Checkbutton(tool_frame)
polygon_check.grid(row=7, column=2)

# The canvas on the left / middle of the screen
image_frame = tk.Frame(root)
image_frame.pack(side=tk.LEFT, expand=True)
canvas = tk.Canvas(image_frame, width=600, height=300, bg="white", bd=5, relief=tk.GROOVE)
canvas.pack(fill=tk.BOTH, expand=True)
image_manager = ImageManager(canvas, colour_picker, status_bar)

tool_bar = ToolBar(image_manager, info_entry, colour_picker, buttons, status_bar)


def safe_quit():
    tool_bar.on_quit()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", safe_quit)
root.mainloop()
