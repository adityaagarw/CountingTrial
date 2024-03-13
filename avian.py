# AVIAN: Advanced Vision Analytics
from ultralytics import YOLO
import counter
import cv2
import numpy as np
import pafy

model = YOLO("yolov8n.pt")
video = pafy.new("https://www.youtube.com/watch?v=WmYCZglRy78")
best = video.getbest(preftype="mp4")
cap = cv2.VideoCapture("..\\test2.mp4")
assert cap.isOpened(), "Error reading video file"
w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

x1=0
x2=600
y1=0
y2=690

reg_points1 = [(0, 600), (400, 600), (500, 20), (100, 20)]  # line or region points
#reg_points = [(x1+40,y1+40), (x2-40, y1+40), (x2-40,y2-40), (x1+40,y2-40)]
#reg_points2 = [(800, 600), (1200, 600), (1000, 20), (600, 20)]
reg_points2 = [(1200, 600), (800, 600), (600, 20), (1000, 20)]
classes_to_count = [0, 2]  # person and car classes for count

# Video writer
video_writer = cv2.VideoWriter("object_counting_output.avi",
                       cv2.VideoWriter_fourcc(*'mp4v'),
                       fps,
                       (w, h))

#Init Object Counter
# counter1 = object_counter.ObjectCounter()
# counter1.set_args(view_img=True,
#                  reg_pts=reg_points1,
#                  classes_names=model.names,
#                  draw_tracks=True
#                  )

# counter2 = object_counter.ObjectCounter()
# counter2.set_args(view_img=True,
#                   reg_pts=reg_points2,
#                   classes_names=model.names,
#                   draw_tracks=True)

counter = counter.ObjectCounter()
counter.set_args(view_img=True,
                 reg_pts=None,
                 classes_names=model.names,
                 draw_tracks=True,
                 width = w,
                 height = h,
                 fps = fps,
                 track_length = 40,
                 buffer_size = 10,
                 total_frames = 1000
                 )

while cap.isOpened():
    success, im0 = cap.read()
    #cropped_im0 = im0[30:800, 600:1200]

    if not success:
        print("Video frame is empty or video processing has been successfully completed.")
        break
    tracks = model.track(np.ascontiguousarray(im0), persist=True, show=False,
                         classes=classes_to_count)

    im0 = counter.start_counting(np.ascontiguousarray(im0), tracks)
    # im0 = counter1.start_counting(np.ascontiguousarray(im0), tracks)
    # im0 = counter2.start_counting(np.ascontiguousarray(im0), tracks)
    
    #video_writer.write(im0)

cap.release()
#video_writer.release()
cv2.destroyAllWindows()