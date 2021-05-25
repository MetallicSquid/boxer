from tkinter import filedialog
import json
import os


class HistoryManager:
    def __init__(self, history_path: str, history_stack: dict, labels: dict):
        self.history_path = history_path
        self.history_stack = history_stack
        self.labels = labels

    # FIXME: The distinction between update_labels and update_canvas is arbitrary as the history is overwritten anyway
    def update_labels(self, new_labels: dict):
        self.labels = new_labels
        self.write_history()

    def update_canvas(self, editable_images: list):
        new_stack = {}
        for image in editable_images:
            filename = os.path.basename(image.image_path)
            new_stack[filename] = {"undo": image.undo_stack, "redo": image.redo_stack}
        self.history_stack = new_stack
        self.write_history()

    def write_history(self):
        with open(self.history_path, "w") as history_file:
            history_file.write(json.dumps([self.history_stack, self.labels]))


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

        json_history = [stacks, default_labels]
        history_path = os.path.join(directory, "boxer_history.json")

        mode = "w+"
        if os.path.exists(history_path):
            mode = "r"

        with open(history_path, mode) as history_file:
            content = history_file.read()
            if content:
                json_history = json.loads(content)
            else:
                json.dumps(json_history)

        history_manager = HistoryManager(history_path, json_history[0], json_history[1])

        return image_paths, history_manager, directory
    else:
        return "cancelled"
