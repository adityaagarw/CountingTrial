from collections import defaultdict

import cv2
import time
import math
from ultralytics.utils.checks import check_imshow, check_requirements
from ultralytics.utils.plotting import Annotator, colors
import pandas as pd
import numpy as np
from pandas import ExcelWriter

ENTRY_THRESHOLD = 1
EXIT_THRESHOLD = 5

check_requirements("shapely>=2.0.0")

from shapely.geometry import LineString, Point, Polygon

class ObjectInfo:
    def __init__(self):
        self.entry_frame = None
        self.frame_count = 0
        self.exit_frame = None
        self.track_history = []
        self.dwell_time = None
        self.entered = False
        self.exited = False
        self.embedding = []
        self.entry_started = False
        self.exit_started = False

class ObjectCounter:
    """A class to manage the counting of objects in a real-time video stream based on their tracks."""

    def __init__(self):
        """Initializes the Counter with default values for various tracking and counting parameters."""

        self.entry_time = {}
        self.is_drawing = False
        self.selected_point = None

        self.reg_pts = [(20, 400), (1260, 400)]
        self.buffer_zone = [(10, 20), (20, 20)]
        self.line_dist_thresh = 15
        self.counting_region = None
        self.region_color = (255, 0, 255)
        self.region_thickness = 5

        self.im0 = None
        self.tf = None
        self.view_img = False

        self.names = None
        self.annotator = None

        self.counting_list = []
        self.count_txt_thickness = 0
        self.count_txt_color = (0, 0, 0)
        self.count_color = (255, 255, 255)

        self.track_history = defaultdict(list)
        self.object_info = defaultdict(ObjectInfo)
        self.track_thickness = 2
        self.draw_tracks = False
        self.track_color = (0, 255, 0)

        self.width = 1280
        self.height = 720
        self.fps = 30
        self.track_length = 30
        self.env_check = check_imshow(warn=True)

        self.frame_count = 0
        self.last_saved_frame = 0
        self.entry_count = 0
        self.exit_count = 0

        self.backtrack_length = 14

    def set_args(
        self,
        classes_names,
        reg_pts,
        count_reg_color=(255, 0, 255),
        line_thickness=2,
        track_thickness=2,
        view_img=False,
        draw_tracks=False,
        count_txt_thickness=2,
        count_txt_color=(0, 0, 0),
        count_color=(255, 255, 255),
        track_color=(0, 255, 0),
        region_thickness=5,
        line_dist_thresh=15,
        width=1280,
        height=720,
        fps=30,
        track_length=30,
        buffer_size=10,
        save_frames=0,
        total_frames=0,
        counter_name="Counter"
    ):
        """
        Configures the Counter's image, bounding box line thickness, and counting region points.
        """
        self.tf = line_thickness
        self.view_img = view_img
        self.track_thickness = track_thickness
        self.draw_tracks = draw_tracks
        self.width = width
        self.height = height
        self.fps = fps
        self.track_length = track_length
        self.save_frames = save_frames
        self.counter_name = counter_name

        print("--------------------------------------------------------------------")
        print(self.counter_name + " Analysis Initiated.")
        print("Stream/Video Dimensions: ", width, "x", height)
        print("FPS: ", fps)
        print("Total Frames in video (0 for stream): ", total_frames)
        print("Buffer Size: ", buffer_size)
        print(reg_pts)
        print("--------------------------------------------------------------------")

        print("\n")

        if reg_pts and len(reg_pts) >= 0:
            x1 = reg_pts[0][0]
            x2 = reg_pts[1][0]
            x3 = reg_pts[2][0]
            x4 = reg_pts[3][0]
            y1 = reg_pts[0][1]
            y2 = reg_pts[1][1]
            y3 = reg_pts[2][1]
            y4 = reg_pts[3][1]

            # new_x1 = x1 + ((x2 - x1) * buffer_size / 100)
            # new_y1 = y1 + ((y2 - y1) * buffer_size / 100)
            # new_x2 = x2 - ((x2 - x1) * buffer_size / 100)
            # new_y2 = y2 - ((y2 - y1) * buffer_size / 100)
            self.reg_pts = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]

            self.counting_region = Polygon(self.reg_pts)
        else:
            x1 = 0
            x2 = self.width
            y1 = 0
            y2 = self.height

            new_x1 = x1 + ((x2 - x1) * buffer_size / 100)
            new_y1 = y1 + ((y2 - y1) * buffer_size / 100)
            new_x2 = x2 - ((x2 - x1) * buffer_size / 100)
            new_y2 = y2 - ((y2 - y1) * buffer_size / 100)
            self.reg_pts = [(new_x1, new_y1), (new_x2, new_y1), (new_x2, new_y2), (new_x1, new_y2)]

            self.counting_region = Polygon(self.reg_pts)

        self.names = classes_names
        self.track_color = track_color
        self.count_txt_thickness = count_txt_thickness
        self.count_txt_color = count_txt_color
        self.count_color = count_color
        self.region_color = count_reg_color
        self.region_thickness = region_thickness
        self.line_dist_thresh = line_dist_thresh

    def save_object_info(self):
        if self.frame_count >= self.save_frames and self.frame_count // self.save_frames > self.last_saved_frame // self.save_frames:
            print("Saving object info to excel")
            df = pd.DataFrame(columns=['ID', 'Entry Frame', 'Frame Count', 'Exit Frame', 'Tracking History', 'Dwell Time', 'Entered', 'Exited'])
            for track_id in self.object_info:
                new_row = {
                    'ID': track_id,
                    'Entry Frame': self.object_info[track_id].entry_frame,
                    'Frame Count': self.object_info[track_id].frame_count,
                    'Exit Frame': self.object_info[track_id].exit_frame,
                    'Tracking History': self.object_info[track_id].track_history,
                    'Dwell Time': self.object_info[track_id].dwell_time,
                    'Entered': self.object_info[track_id].entered,
                    'Exited': self.object_info[track_id].exited
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            self.last_saved_frame = self.frame_count
            self.excel_created = True
            df1 = df.groupby(['Entered', 'Exited'])['Entered'].count()
            df1 = df1.unstack(fill_value=0)
            df1 = df1.reset_index()
            df = pd.concat([df, df1], axis=1)
            if (self.frame_count // self.save_frames) == 1:
                mode = 'w'
            else:
                mode = 'a'

            excel_file = self.counter_name + ".xlsx"
            with pd.ExcelWriter(excel_file, engine='openpyxl', mode=mode) as writer:
                df.to_excel(writer, sheet_name=f'sheet_{self.frame_count // self.save_frames}', index=False)
                print("Count: ", self.frame_count // self.save_frames, " Excel saved")

    def calculate_direction(self, track_line):
        if len(track_line) < 2:
            return 0

        start_point = track_line[0]
        end_point = track_line[-1]

        direction = end_point[1] - start_point[1]
        return direction

    def calculate_angle(self, line1, line2):
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

    def orientation(self, p1, p2, p3):
        val = (p2[1] - p1[1]) * (p3[0] - p2[0]) - (p2[0] - p1[0]) * (p3[1] - p2[1])
        if val == 0:
            return 0  # collinear
        elif val > 0:
            return 1  # clockwise
        else:
            return 2  # counterclockwise

    def check_intersection(self, line1, line2):
        p1 = line1[0]
        q1 = line1[1]
        p2 = line2[0]
        q2 = line2[1]
        """
        Returns True if line segments 'p1q1' and 'p2q2' intersect.
        """
        # Find the four orientations needed for the general and
        # special cases
        o1 = self.orientation(p1, q1, p2)
        o2 = self.orientation(p1, q1, q2)
        o3 = self.orientation(p2, q2, p1)
        o4 = self.orientation(p2, q2, q1)

        # Intersection case
        if o1 != o2 and o3 != o4:
            return True

        return False

    def cross_product(self, track_line, ref_line):
        track_line_vector = np.array(track_line[1]) - np.array(track_line[0])
        ref_line_vector = np.array(ref_line[1]) - np.array(ref_line[0])
        cross_product = np.cross(track_line_vector, ref_line_vector)
        return cross_product

    def extract_and_process_tracks(self, tracks):
        cv2.putText(self.im0, f"Entry Count: {self.entry_count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (36, 255, 12), 2)
        cv2.putText(self.im0, f"Exit Count: {self.exit_count}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (36, 255, 12), 2)

        cv2.putText(self.im0, f"Frame: {self.frame_count}", (self.width - 300, self.height - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (36, 255, 12), 2)

        self.annotator = Annotator(self.im0, self.tf, self.names)
        self.annotator.draw_region(reg_pts=self.reg_pts, color=self.region_color, thickness=self.region_thickness)

        self.save_object_info()

        if tracks[0].boxes.id is None:
            return

        boxes = tracks[0].boxes.xyxy.cpu()
        clss = tracks[0].boxes.cls.cpu().tolist()
        track_ids = tracks[0].boxes.id.int().cpu().tolist()

        for box, track_id, cls in zip(boxes, track_ids, clss):
            self.annotator.box_label(box, label=f"Person {track_id}", color=colors(int(cls), True))

            track_line = self.object_info[track_id].track_history
            foot_position = (float((box[0] + box[2]) / 2), float(box[3]))
            track_line.append(foot_position)
            if len(track_line) > self.track_length:
                track_line.pop(0)

            if self.draw_tracks:
                #Change the color of the track line based on the position of the track. earliest points are violet and the latest points are red
                self.track_color = (int(255 * (len(track_line) / self.track_length)), 0, int(255 * (1 - len(track_line) / self.track_length)))
                self.annotator.draw_centroid_and_tracks(
                    track_line, color=self.track_color, track_thickness=self.track_thickness
                )                

            if len(track_line) >= self.backtrack_length:
                start_point = track_line[len(track_line) - self.backtrack_length - 1]
                end_point = track_line[len(track_line) - 1]

                # Check for all points between start_point and end_point
                for i in range(len(track_line) - self.backtrack_length, len(track_line)):
                    #if self.counting_region.contains(Point(track_line[i])):
                    entry_line = [self.reg_pts[2], self.reg_pts[3]]
                    exit_line = [self.reg_pts[1], self.reg_pts[0]]
                    track_vector = [start_point, end_point]

                    if self.check_intersection(track_vector, entry_line):
                        if not self.object_info[track_id].entered :
                            cp = self.cross_product(track_vector, entry_line)
                            print("Intersection at entry line: ", cp)
                            if cp > 0 and self.object_info[track_id].entry_started:
                                self.entry_count += 1
                                self.object_info[track_id].entered = True
                            elif cp < 0:
                                self.object_info[track_id].exit_started = True
                                
                    if self.check_intersection(track_vector, exit_line):
                        if not self.object_info[track_id].exited:
                            cp = self.cross_product(track_vector, exit_line)
                            print("Intersection at exit line: ", cp)
                            if cp < 0 and self.object_info[track_id].exit_started:
                                self.exit_count += 1
                                self.object_info[track_id].exited = True
                            elif cp > 0:
                                self.object_info[track_id].entry_started = True

    def display_frames(self):
        if self.env_check:
            cv2.namedWindow("Avian Tech")
            cv2.imshow("Avian Tech", self.im0)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                return

    def start_counting(self, im0, tracks, fc):
        self.im0 = im0
        self.frame_count = fc

        self.extract_and_process_tracks(tracks)

        if self.view_img:
            self.display_frames()
        return self.im0


if __name__ == "__main__":
    ObjectCounter()