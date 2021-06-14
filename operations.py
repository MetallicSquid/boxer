# The intersection logic here was heavily "inspired" by this article:
# https://www.geeksforgeeks.org/how-to-check-if-a-given-point-lies-inside-a-polygon/

def orientation(p1, p2, p3):
    result = ((p2[1] - p1[1]) * (p3[0] - p2[0])) - ((p2[0] - p1[0]) * (p3[1] - p2[1]))
    if result > 0:
        return 1
    elif result < 0:
        return -1
    else:
        return 0


def on_segment(p1, p2, q):
    x_range = bool(q[0] <= max(p1[0], p2[0]) and q[0] >= min(p1[0], p2[0]))
    y_range = bool(q[1] <= max(p1[1], p2[1]) and q[1] <= min(p1[1], p2[1]))

    return bool(x_range and y_range)


def check_intersection(p1, p2, p3, p4):
    o1 = orientation(p1, p2, p3)
    o2 = orientation(p1, p2, p4)
    o3 = orientation(p3, p4, p1)
    o4 = orientation(p3, p4, p2)

    s1 = bool(o1 == 0 and on_segment(p1, p2, p3))
    s2 = bool(o2 == 0 and on_segment(p1, p2, p4))
    s3 = bool(o3 == 0 and on_segment(p3, p4, p1))
    s4 = bool(o4 == 0 and on_segment(p3, p4, p2))

    general = bool(o1 != o2 and o3 != o4)
    special = bool(s1 or s2 or s3 or s4)

    return bool(general or special)


def check_inside_polygon(vertices, point, width):
    intersect_count = 0
    for i in range(len(vertices)):
        if check_intersection(vertices[i], vertices[i+1], point, (width, point[1])):
            if orientation(vertices[i], point, vertices[i+1]) == 0:
                return on_segment(vertices[i], vertices[i+1], point)

            intersect_count += 1

    return bool(intersect_count % 2 == 1)

