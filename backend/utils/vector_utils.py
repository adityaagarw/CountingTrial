import math
import numpy as np

class VectorUtils:
    def calculate_direction(track_line):
        if len(track_line) < 2:
            return 0

        start_point = track_line[0]
        end_point = track_line[-1]

        direction = end_point[1] - start_point[1]
        return direction

    def calculate_angle(line1, line2):
        x1, y1 = line1[0]
        x2, y2 = line1[1]
        x3, y3 = line2[0]
        x4, y4 = line2[1]

        vector1 = (x2 - x1, y2 - y1)
        vector2 = (x4 - x3, y4 - y3)

        dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]
        magnitude1 = math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
        magnitude2 = math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)

        if magnitude1 == 0 or magnitude2 == 0:
            return 0

        angle = math.acos(dot_product / (magnitude1 * magnitude2))
        angle_degrees = math.degrees(angle)

        return angle_degrees

    def orientation(p1, p2, p3):
        val = (p2[1] - p1[1]) * (p3[0] - p2[0]) - (p2[0] - p1[0]) * (p3[1] - p2[1])
        if val == 0:
            return 0  # collinear
        elif val > 0:
            return 1  # clockwise
        else:
            return 2  # counterclockwise

    def check_intersection(line1, line2):
        p1 = line1[0]
        q1 = line1[1]
        p2 = line2[0]
        q2 = line2[1]
        """
        Returns True if line segments 'p1q1' and 'p2q2' intersect.
        """
        # Find the four orientations needed for the general and
        # special cases
        o1 = VectorUtils.orientation(p1, q1, p2)
        o2 = VectorUtils.orientation(p1, q1, q2)
        o3 = VectorUtils.orientation(p2, q2, p1)
        o4 = VectorUtils.orientation(p2, q2, q1)

        # Intersection case
        if o1 != o2 and o3 != o4:
            return True

        return False
    
    def cross_product(track_line, ref_line):
        track_line_vector = np.array(track_line[1]) - np.array(track_line[0])
        ref_line_vector = np.array(ref_line[1]) - np.array(ref_line[0])
        cross_product = np.cross(track_line_vector, ref_line_vector)
        return cross_product
