# AVIAN: Advanced Vision Analytics
from ultralytics import YOLO
import simple_counter as counter
import cv2
import numpy as np
import argparse
import pandas as pd

class Avian:
    def __init__(self, video_path):
        self.video_path = video_path
        self.model = YOLO("yolov8n.pt")
        self.cap = cv2.VideoCapture(video_path)
        assert self.cap.isOpened(), "Error reading video file"
        self.w, self.h, self.fps = (int(self.cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.classes_to_count = [0]
        self.video_name = self.get_video_name(self.video_path)
        self.num_save_frames = 1000
        self.num_track_length = 100
        self.num_buffer_size = 0
        self.format_width = 1024 #or w
        self.format_height = 576 #or h

    def fast_forward_callback(self, event, x, y, flags, param):
        # On right mouse button click, fast forward the video by 250 frames
        if event == cv2.EVENT_RBUTTONDBLCLK:
            to_count = self.cap.get(cv2.CAP_PROP_POS_FRAMES) + 250 if self.cap.get(cv2.CAP_PROP_POS_FRAMES) + 250 < self.frame_count else self.frame_count
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, to_count)
        elif event == cv2.EVENT_LBUTTONDBLCLK:
            to_count = self.cap.get(cv2.CAP_PROP_POS_FRAMES) - 250 if self.cap.get(cv2.CAP_PROP_POS_FRAMES) - 250 > 0 else 0
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, to_count)

    def track_and_count(self):

        counter_array = []    
        # Read excel file "video_name.xlsx" and create array of counters based on number of rows in the file
        df = pd.read_excel(self.video_name + ".xlsx")
        if df is None or df.empty:
            print("The excel file is empty or does not exist.")
            reg_pts=None
            counter_array.append(counter.ObjectCounter())
            counter_name = "Counter"
            counter_array[0].set_args(view_img=True,
                                reg_pts=reg_pts,
                                classes_names=self.model.names,
                                draw_tracks=True,
                                width = self.format_w,
                                height = self.format_h,
                                fps = self.fps,
                                track_length = self.num_track_length,
                                buffer_size = self.num_buffer_size,
                                save_frames = self.num_save_frames,
                                total_frames = self.frame_count,
                                counter_name = counter_name
                                )
        
        else:
            for i in range(len(df)):
                # Store points from columns of pd in reg_pts
                # FIXME: This is a temporary solution. The points should be stored in a better way.

                reg_pts = [(df["x1"][i], df["y1"][i]), (df["x2"][i], df["y2"][i]), (df["x3"][i], df["y3"][i]), (df["x4"][i], df["y4"][i])]
                counter_array.append(counter.ObjectCounter())
                counter_name = "Counter" + str(i)
                counter_array[i].set_args(view_img=True,
                                    reg_pts=reg_pts,
                                    classes_names=self.model.names,
                                    draw_tracks=True,
                                    width = self.format_width,
                                    height = self.format_height,
                                    fps = self.fps,
                                    track_length = self.num_track_length,
                                    buffer_size = self.num_buffer_size,
                                    save_frames = self.num_save_frames,
                                    total_frames = self.frame_count,
                                    counter_name = counter_name,
                                    region_id = i
                                    )

        while self.cap.isOpened():
            success, im0 = self.cap.read()

            im0 = cv2.resize(im0, (int(self.format_width), int(self.format_height)))

            if not success:
                print("Video frame is empty or video processing has been successfully completed.")
                break
            tracks = self.model.track(np.ascontiguousarray(im0), persist=True, show=False, verbose=False,
                                classes=self.classes_to_count, conf=0.15)

            for i in range(len(counter_array)): 
                im0 = counter_array[i].start_counting(np.ascontiguousarray(im0), tracks, self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                cv2.setMouseCallback("Avian Tech", self.fast_forward_callback)

        self.cap.release()
        cv2.destroyAllWindows()
    
    def get_video_name(self, video_path):
        # Split the video path to get the video name
        video_name = video_path.split("/")[-1]
        # Split the video name to get the video name without the extension
        video_name_without_extension = video_name.split(".")[0]
        # Return the video name and the video name without the extension
        return video_name_without_extension

if __name__ == "__main__":
    # Parse arguments using arparge for video path
    parser = argparse.ArgumentParser(description="Counting the number of objects in a video")
    parser.add_argument("video_path", type=str, help="Path to the stream/video")
    args = parser.parse_args()

    avian = Avian(args.video_path)
    # Call a new function for counting the objects in the video
    avian.track_and_count()