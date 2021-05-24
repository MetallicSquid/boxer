from tkinter import filedialog
import json
import os


def setup_image_dir():
    directory = filedialog.askdirectory()
    history_dict = {}

    image_paths = []
    image_types = [".jpg", ".png", ".bmp"]
    for file in os.listdir(directory):
        if os.path.splitext(file)[1] in image_types:
            image_path = os.path.join(directory, file)
            image_paths.append(image_path)
            history_dict[file] = {'undo': [], 'redo': []}

    history_path = os.path.join(directory, "box_history.json")
    mode = "w+"
    if os.path.exists(history_path):
        mode = "r"

    with open(history_path, mode) as history_file:
        content = history_file.read()
        if content:
            history_dict = json.loads(content)
        else:
            json.dumps(history_dict)

    return image_paths, history_dict, history_path


def write_history(history_path: str, editable_images: list):
    new_history = {}
    for image in editable_images:
        filename = os.path.basename(image.image_path)
        undo_stack = image.undo_stack
        redo_stack = image.redo_stack
        new_history[filename] = {'undo': undo_stack, 'redo': redo_stack}

    with open(history_path, "w") as history_file:
        history_file.write(json.dumps(new_history))

