from tkinter import filedialog
import json
import os


# Creates / loads the history for a chosen directory
def setup_image_dir():
    directory = filedialog.askdirectory()
    if directory:
        stacks = {}
        default_labels = {"blue": "blue", "lime green": "lime green", "yellow": "yellow", "red": "red",
                          "deep pink": "deep pink"}

        image_paths = []
        image_types = [".jpg", ".png", ".bmp"]
        for file in os.listdir(directory):
            if os.path.splitext(file)[1] in image_types:
                image_path = os.path.join(directory, file)
                image_paths.append(image_path)
                stacks[file] = {'undo': [], 'redo': []}

        if not image_paths:
            return "invalid"

        history = [stacks, default_labels]
        history_path = os.path.join(directory, "boxer_history.json")
        mode = "w+"
        if os.path.exists(history_path):
            mode = "r"

        with open(history_path, mode) as history_file:
            content = history_file.read()
            if content:
                history = json.loads(content)
            else:
                json.dumps(history)

        return image_paths, history, history_path
    else:
        return "cancelled"


# Writes the history to the .json file
def write_history(history_path: str, editable_images: list, label_dict: dict):
    new_stack = {}
    for image in editable_images:
        filename = os.path.basename(image.image_path)
        undo_stack = image.undo_stack
        redo_stack = image.redo_stack
        new_stack[filename] = {'undo': undo_stack, 'redo': redo_stack}

    new_history = [new_stack, label_dict]
    with open(history_path, "w") as history_file:
        history_file.write(json.dumps(new_history))

