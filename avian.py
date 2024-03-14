# AVIAN: Advanced Vision Analytics
from ultralytics import YOLO
import counter
import cv2
import numpy as np
import pafy

model = YOLO("yolov8n.pt")
video = pafy.new("https://www.youtube.com/watch?v=WmYCZglRy78")
best = video.getbest(preftype="mp4")
cap = cv2.VideoCapture("test3.mp4")
assert cap.isOpened(), "Error reading video file"
w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

classes_to_count = [0]  # person and car classes for count

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
                 save_frames = 1000,
                 total_frames = frame_count
                 )

while cap.isOpened():
    success, im0 = cap.read()
    #cropped_im0 = im0[30:800, 600:1200]

    if not success:
        print("Video frame is empty or video processing has been successfully completed.")
        break
    tracks = model.track(np.ascontiguousarray(im0), persist=True, show=False, verbose=False,
                         classes=classes_to_count)

    im0 = counter.start_counting(np.ascontiguousarray(im0), tracks)


cap.release()
cv2.destroyAllWindows()