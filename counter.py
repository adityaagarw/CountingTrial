# Ultralytics YOLO 🚀, AGPL-3.0 license

from collections import defaultdict

import cv2
import time # DWELL TIME
from ultralytics.utils.checks import check_imshow, check_requirements
from ultralytics.utils.plotting import Annotator, colors
import pandas as pd

ENTRY_THRESHOLD = 5
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

class ObjectCounter:
    """A class to manage the counting of objects in a real-time video stream based on their tracks."""

    def __init__(self):
        """Initializes the Counter with default values for various tracking and counting parameters."""

        self.entry_time = {}  # DWELL TIME
        # Mouse events
        self.is_drawing = False
        self.selected_point = None

        # Region & Line Information
        self.reg_pts = [(20, 400), (1260, 400)]
        self.buffer_zone = [(10,20), (20, 20)]
        self.line_dist_thresh = 15
        self.counting_region = None
        self.region_color = (255, 0, 255)
        self.region_thickness = 5

        # Image and annotation Information
        self.im0 = None
        self.tf = None
        self.view_img = False
        # self.view_in_counts = True
        # self.view_out_counts = True

        self.names = None  # Classes names
        self.annotator = None  # Annotator

        # Object counting Information
        self.in_counts = 0
        self.out_counts = 0
        self.counting_list = []
        self.count_txt_thickness = 0
        self.count_txt_color = (0, 0, 0)
        self.count_color = (255, 255, 255)

        # Tracks info
        self.track_history = defaultdict(list)
        self.object_info = defaultdict(ObjectInfo)
        self.track_thickness = 2
        self.draw_tracks = False
        self.track_color = (0, 255, 0)

        # Frame attributes
        self.width = 1280
        self.height = 720
        self.fps = 30
        self.track_length = 30
        # Check if environment support imshow
        self.env_check = check_imshow(warn=True)

        # Frame counter
        self.frame_count = 0
        self.excel_created = False

    def set_args(
        self,
        classes_names,
        reg_pts,
        count_reg_color=(255, 0, 255),
        line_thickness=2,
        track_thickness=2,
        view_img=False,
        view_in_counts=True,
        view_out_counts=True,
        draw_tracks=False,
        count_txt_thickness=2,
        count_txt_color=(0, 0, 0),
        count_color=(255, 255, 255),
        track_color=(0, 255, 0),
        region_thickness=5,
        line_dist_thresh=15,
        width = 1280,
        height = 720,
        fps = 30,
        track_length = 30,
        buffer_size = 10, # in percent
        total_frames = 0
    ):
        """
        Configures the Counter's image, bounding box line thickness, and counting region points.

        Args:
            line_thickness (int): Line thickness for bounding boxes.
            view_img (bool): Flag to control whether to display the video stream.
            view_in_counts (bool): Flag to control whether to display the incounts on video stream.
            view_out_counts (bool): Flag to control whether to display the outcounts on video stream.
            reg_pts (list): Initial list of points defining the counting region.
            classes_names (dict): Classes names
            track_thickness (int): Track thickness
            draw_tracks (Bool): draw tracks
            count_txt_thickness (int): Text thickness for object counting display
            count_txt_color (RGB color): count text color value
            count_color (RGB color): count text background color value
            count_reg_color (RGB color): Color of object counting region
            track_color (RGB color): color for tracks
            region_thickness (int): Object counting Region thickness
            line_dist_thresh (int): Euclidean Distance threshold for line counter
        """
        self.tf = line_thickness
        self.view_img = view_img
        self.view_in_counts = view_in_counts
        self.view_out_counts = view_out_counts
        self.track_thickness = track_thickness
        self.draw_tracks = draw_tracks
        self.width = width
        self.height = height
        self.fps = fps
        self.track_length = track_length
        self.total_frames = total_frames

        # Region and line selection
        if reg_pts and len(reg_pts) >= 0:
            print("Region Counter Initiated.")
            x1 = reg_pts[0][0]
            x2 = reg_pts[1][0]
            y1 = reg_pts[0][1]
            y2 = reg_pts[2][1]
            
            new_x1 = x1 + (x1 * buffer_size / 100)
            new_x2 = x2 - (x2 * buffer_size / 100)
            new_y1 = y1 + (y1 * buffer_size / 100)
            new_y2 = y2 - (y2 * buffer_size / 100)
            
            self.reg_pts = [(new_x1, new_y1), (new_x2, new_y1), (new_x2, new_y2), (new_x1, new_y2)]
            
            self.counting_region = Polygon(self.reg_pts)
        else:
            print("None region")
            x1 = 0
            x2 = self.width
            y1 = 0
            y2 = self.height
            
            
            new_x1 = x1 + (x1 * buffer_size / 100)
            new_x2 = x2 - (x2 * buffer_size / 100)
            new_y1 = y1 + (y1 * buffer_size / 100)
            new_y2 = y2 - (y2 * buffer_size / 100)
            # Set reg_pts to width and height in xyxy format
            #self.reg_pts = [(0, 0), (self.width, 0), (self.width, self.height), (0, self.height)]
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

    def extract_and_process_tracks(self, tracks):
        """Extracts and processes tracks for object counting in a video stream."""
        boxes = tracks[0].boxes.xyxy.cpu()
        clss = tracks[0].boxes.cls.cpu().tolist()
        track_ids = tracks[0].boxes.id.int().cpu().tolist()

        # Annotator Init and region drawing
        self.annotator = Annotator(self.im0, self.tf, self.names)
        self.annotator.draw_region(reg_pts=self.reg_pts, color=self.region_color, thickness=self.region_thickness)

        # Extract tracks
        for box, track_id, cls in zip(boxes, track_ids, clss):
            # Draw bounding box
            self.annotator.box_label(box, label=f"Person {track_id}", color=colors(int(cls), True))

            # Draw Tracks
            track_line = self.object_info[track_id].track_history
            #track_line = self.track_history[track_id]
            track_line.append((float((box[0] + box[2]) / 2), float((box[1] + box[3]) / 2)))
            if len(track_line) > self.track_length:
                track_line.pop(0)

            if self.counting_region.contains(Point(track_line[-1])):
                # If the object is not already in the counting list, record the current time
                if self.object_info[track_id].entry_frame is None:
                    self.object_info[track_id].entry_frame = self.frame_count
                    
                self.object_info[track_id].frame_count += 1
                if (self.object_info[track_id].frame_count/self.fps) > ENTRY_THRESHOLD:
                    self.counting_list.append(track_id)
                    self.object_info[track_id].entered = True
                
                # Display the dwell time
                frame_count_label = f"Frame count (ID {track_id}): {self.object_info[track_id].frame_count}"
                cv2.putText(self.im0, frame_count_label, (int(box[0]), int(box[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
            else:
                if self.object_info[track_id].entry_frame is not None:
                    self.object_info[track_id].exit_frame = self.frame_count
                    self.object_info[track_id].dwell_time = (self.object_info[track_id].exit_frame - self.object_info[track_id].entry_frame)/self.fps
                    self.object_info[track_id].exited = True

            # Draw track trails
            if self.draw_tracks:
                self.annotator.draw_centroid_and_tracks(
                    track_line, color=self.track_color, track_thickness=self.track_thickness
                )

            prev_position = self.object_info[track_id].track_history[-2] if len(self.object_info[track_id].track_history) > 1 else None
            #prev_position = self.track_history[track_id][-2] if len(self.track_history[track_id]) > 1 else None

            if (
                prev_position is not None
                and self.counting_region.contains(Point(track_line[-1]))
                and track_id not in self.counting_list
            ):
                pass
                # if(dwell_time > ENTRY_THRESHOLD):
                #     self.counting_list.append(track_id)
                #     if (box[0] - prev_position[0]) * (self.counting_region.centroid.x - prev_position[0]) > 0:
                #         self.in_counts += 1
                #     else:
                #         self.out_counts += 1
            elif (
                prev_position is None
                and self.counting_region.contains(Point(track_line[-1]))
                and track_id not in self.counting_list
                ):
                pass
                # Case where person was detected in the region for the first time

        count = 0
        # Increment "count" where entered flag is True
        for track_id in self.object_info:
            if self.object_info[track_id].entered is True:
                count += 1
                
        # Display the count
        cv2.putText(self.im0, f"Count: {count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (36,255,12), 2)

        # Display frame count in the bottom right corner
        cv2.putText(self.im0, f"Frame: {self.frame_count}", (self.width-300, self.height-50), cv2.FONT_HERSHEY_SIMPLEX, 1, (36,255,12), 2)

        #Store object info in a dataframe and store in excel when the video ends
        if self.frame_count >= self.total_frames:
            if not self.excel_created:
                print("Saving object info to excel")
                df = pd.DataFrame(columns=['ID', 'Entry Frame', 'Frame Count', 'Exit Frame', 'Tracking History' ,'Dwell Time', 'Entered', 'Exited'])
                for track_id in self.object_info:
                    new_row = {'ID': track_id, 'Entry Frame': self.object_info[track_id].entry_frame, 'Frame Count': self.object_info[track_id].frame_count, 'Exit Frame': self.object_info[track_id].exit_frame, 'Tracking History': self.object_info[track_id].track_history, 'Dwell Time': self.object_info[track_id].dwell_time, 'Entered': self.object_info[track_id].entered, 'Exited': self.object_info[track_id].exited}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    
                self.excel_created = True
                df1 = df.groupby(['Entered','Exited'])['Entered'].count()
                # Convert df1 rows to columns
                df1 = df1.unstack(fill_value=0)
                df1 = df1.reset_index()
                # Concat unstacked df1 to df at row 1 after data, give a gap of 1 column
                df = pd.concat([df.iloc[:, :-1], df1], axis=1)

                df.to_excel("object_info.xlsx", index=False)


        # Fix me: always display stats

            # for track_id in self.object_info:
            #     df = df.append({'ID': track_id, 'Entry Frame': self.object_info[track_id].entry_frame, 'Exit Frame': self.object_info[track_id].exit_frame, 'Dwell Time': self.object_info[track_id].dwell_time}, ignore_index=True)
            # df.to_excel("object_info.xlsx", index=False)

        # incount_label = f"In Count : {self.in_counts}"
        # outcount_label = f"OutCount : {self.out_counts}"

        # # Display counts based on user choice
        # counts_label = None
        # if not self.view_in_counts and not self.view_out_counts:
        #     counts_label = None
        # elif not self.view_in_counts:
        #     counts_label = outcount_label
        # elif not self.view_out_counts:
        #     counts_label = incount_label
        # else:
        #     counts_label = f"{incount_label} {outcount_label}"

        # if counts_label is not None:
        #     self.annotator.count_labels(
        #         counts=counts_label,
        #         count_txt_size=self.count_txt_thickness,
        #         txt_color=self.count_txt_color,
        #         color=self.count_color,
        #     )

    def display_frames(self):
        """Display frame."""
        if self.env_check:
            cv2.namedWindow("Avian Tech")
            cv2.imshow("Avian Tech", self.im0)
            # Break Window
            if cv2.waitKey(1) & 0xFF == ord("q"):
                return

    def start_counting(self, im0, tracks):
        """
        Main function to start the object counting process.

        Args:
            im0 (ndarray): Current frame from the video stream.
            tracks (list): List of tracks obtained from the object tracking process.
        """
        self.im0 = im0  # store image
        self.frame_count += 1

        if tracks[0].boxes.id is None:
            if self.view_img:
                self.display_frames()
            return im0
        self.extract_and_process_tracks(tracks)

        if self.view_img:
            self.display_frames()
        return self.im0


if __name__ == "__main__":
    ObjectCounter()