# The intersection logic here was heavily "inspired" by this article:
# https://www.geeksforgeeks.org/how-to-check-if-a-given-point-lies-inside-a-polygon/
import numpy as np
from PIL import Image


# Determines whether the line segments joining p1, p2 and p3 curve clockwise, anticlockwise or don't curve at all
def orientation(p1, p2, p3):
    result = ((p2[1] - p1[1]) * (p3[0] - p2[0])) - ((p2[0] - p1[0]) * (p3[1] - p2[1]))
    if result > 0:
        return 1
    elif result < 0:
        return -1
    else:
        return 0


# Checks whether the line segment (p3, p4) intersects the line segment (p1, p2)
def check_intersection(p1, p2, p3, p4):
    o1 = orientation(p1, p2, p3)
    o2 = orientation(p1, p2, p4)
    o3 = orientation(p3, p4, p1)
    o4 = orientation(p3, p4, p2)

    return bool(o1 != o2 and o3 != o4)


# Checks whether a given point lies inside a polygon described as a list of vertices
def check_inside_polygon(vertices, point, width):
    intersect_count = 0
    for i in range(len(vertices)-1):
        if check_intersection(vertices[i], vertices[i+1], point, (width, point[1])):
            intersect_count += 1

    return bool(intersect_count % 2 == 1)


# If a point lies outside a given width and height, it is adjusted to the nearest valid point
def adjust_point(point, width, height, rel_x=0, rel_y=0):
    x = point[0]
    y = point[1]

    if x > width + rel_x:
        x = width + rel_x
    elif x < rel_x:
        x = rel_x

    if y > height + rel_y:
        y = height + rel_y
    elif y < rel_y:
        y = rel_y

    return x, y


# Encodes annotation vertices to RLE encoded list
def vertices_to_rle(bbox: list, vertices: list):
    rle_list = []
    current_count = 0
    current_type = False
    for i in range(bbox[3]):
        for j in range(bbox[2]):
            y = i + bbox[0]
            x = j + bbox[1]
            if check_inside_polygon(vertices, (x, y), bbox[2]):
                if current_type:
                    current_count += 1
                else:
                    rle_list.append(current_count)
                    current_count = 1
                current_type = True
            else:
                if current_type:
                    rle_list.append(current_count)
                    current_count = 1
                else:
                    current_count += 1
                current_type = False

    return rle_list
