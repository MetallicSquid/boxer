from tkinter import filedialog
from datetime import date
import json
import os


class InfoManager:
    def __init__(self):
        self.directory = None
        self.valid = False
        self.colour_map = {}

        self.info = {}
        self.licenses = []
        self.categories = []
        self.images = []
        self.annotations = []

    def set_valid(self, valid: bool):
        self.valid = valid

    def clear_fields(self):
        self.info = {}
        self.licenses = []
        self.categories = []
        self.images = []
        self.annotations = []

    def activate(self, directory: str):
        self.directory = directory
        self.clear_fields()

    def populate_info(self, year: int, version: str, description: str, contributor: str, url: str):
        self.info = {"year": year,
                     "version": version,
                     "description": description,
                     "contributor": contributor,
                     "url": url,
                     "date_created": str(date.today())}

    # TODO: Handle annotation iscrowd

    '''
    RLE is handled by looping over all of the pixels in the image and seeing if a given pixel lies within the bounding
    polygon. The segmentation field ends up having two lists - size and counts. Size depicts the size of the image.
    Counts is a list of the number of pixels that are valid and are not valid for a given annotation, it might look like
    [147, 4, 32, 17, 123, 8, ...]
     NV   V  NV  V   NV   V  ...
     
     In order to support this, I first need to write an efficient algorithm for detecting whether two lines intersect,
     and then using this determine whether a point lies within a polygon by counting the number of intersections on a 
     given plane.
     
     (Maybe handle supercategories first)
    '''

    # TODO: Handle category supercategory

    # Fills all possible fields based on accessible information
    def bulk_populate_fields(self, editable_images: list):
        self.clear_fields()
        image_counter = 0
        annotation_counter = 0
        category_counter = 0

        present_categories = []
        category_id_map = {}

        for editable_image in editable_images:
            for annotation in editable_image.annotations:
                coords = annotation.bbox.get_coords()
                bbox = [coords[0], coords[1], coords[2]-coords[0], coords[3]-coords[1]]
                area = bbox[2] * bbox[3]

                if annotation.label not in present_categories:
                    present_categories.append(annotation.label)
                    category_id_map[annotation.label] = category_counter
                    self.categories.append({"id": category_counter,
                                            "name": annotation.label,
                                            "supercategory": None})
                    category_counter += 1

                segmentation = []
                for polygon in annotation.polygons:
                    # TODO: Set iscrowd=1 if there are multiple polygons here
                    # TODO: Handle RLE if iscrowd=1/
                    segmentation.append(polygon.get_coords())

                self.annotations.append({"id": annotation_counter,
                                         "image_id": image_counter,
                                         "category_id": category_id_map[annotation.label],
                                         "segmentation": segmentation,
                                         "area": area,
                                         "bbox": bbox,
                                         "iscrowd": None})
                annotation_counter += 1

            self.images.append({"id": image_counter,
                                "width": editable_image.width,
                                "height": editable_image.height,
                                "file_name": editable_image.file_name,
                                "license": None,
                                "date_captured": editable_image.date_captured})
            image_counter += 1

    def make_id_category_map(self):
        id_category_map = {}
        for category in self.categories:
            id_category_map[category["id"]] = category["name"]

        return id_category_map

    def make_id_colour_map(self):
        id_colour_map = {}
        for key, value in self.colour_map.items():
            id_colour_map[value] = key

        return id_colour_map

    def write_coco(self):
        if self.directory and self.valid:
            path = os.path.join(self.directory, "coco.json")
            coco = {"info": self.info,
                    "licenses": self.licenses,
                    "categories": self.categories,
                    "images": self.images,
                    "annotations": self.annotations}

            with open(path, "w") as coco_file:
                coco_file.write(json.dumps(coco))

    def read_coco(self):
        if self.directory:
            path = os.path.join(self.directory, "coco.json")
            with open(path, "r") as coco_file:
                content = json.loads(coco_file.read())

                self.info = content["info"]
                self.licenses = content["licenses"]
                self.categories = content["categories"]
                self.images = content["images"]
                self.annotations = content["annotations"]

    def write_colour_map(self):
        if self.directory and self.valid:
            path = os.path.join(self.directory, ".colour_map.json")
            with open(path, "w") as colour_file:
                colour_file.write(json.dumps(self.colour_map))

    def read_colour_map(self):
        if self.directory:
            path = os.path.join(self.directory, ".colour_map.json")
            with open(path, "r") as colour_file:
                content = json.loads(colour_file.read())

                self.colour_map = content


def load_dir(info_manager: InfoManager):
    directory = filedialog.askdirectory()
    if directory:
        info_manager.activate(directory)
    else:
        return "cancelled"

    coco_path = os.path.join(directory, "coco.json")
    colour_map_path = os.path.join(directory, ".colour_map.json")
    if os.path.exists(coco_path):
        info_manager.read_coco()
        info_manager.read_colour_map()

        return "read"
    else:
        info_manager.colour_map = {"blue": "blue",
                                   "lime green": "lime green",
                                   "yellow": "yellow",
                                   "red": "red",
                                   "deep pink": "deep pink"}

        image_types = [".jpg", ".png", ".bmp"]
        valid_images = []
        for file in os.listdir(directory):
            if os.path.splitext(file)[1] in image_types:
                valid_images.append(os.path.join(directory, file))

        if not valid_images:
            return "invalid"

        open(coco_path, "x")
        open(colour_map_path, "x")

        return valid_images
