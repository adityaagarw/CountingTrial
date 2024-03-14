# Find max width and height of the person
import cv2
from ultralytics import YOLO
import numpy as np

model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture("test3.mp4")
assert cap.isOpened(), "Error reading video file"

classes_to_detect = [0]

w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
if frame_count is None:
    frame_count = 0

def calibrate(num_frames):
    # Find max width and height of the person
    max_width = 0
    max_height = 0
    fc = 0
    max_frame_width = 0
    max_frame_height = 0
    for i in range(num_frames):
        ret, frame = cap.read()
        if not ret:
            break
        fc += 1
        results = model(frame, verbose=False, classes=classes_to_detect)
        boxes = results[0].boxes.xyxy.cpu()
        for result in boxes.numpy():
            width = result[2] - result[0]
            height = result[3] - result[1]
            if width > max_width:
                max_frame_width = fc
                max_width = width
            if height > max_height:
                max_frame_height = fc
                max_height = height

    print("Resolution: ", w, "x", h)
    print("FPS: ", fps)
    print("Frame count: ", frame_count)

    print("Max width of person: ", max_width)
    print("Max height of person: ", max_height)
    
    print("Frame with max width: ", max_frame_width)
    print("Frame with max height: ", max_frame_height)
    
    #Read that frame and display with bounding box
    cap.set(cv2.CAP_PROP_POS_FRAMES, max_frame_width)
    ret, frame = cap.read()
    results = model(frame, verbose=False, classes = classes_to_detect, show=True)
    cv2.waitKey(0)
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, max_frame_height)
    ret, frame = cap.read()
    results = model(frame, verbose=False, classes = classes_to_detect, show=True)
    cv2.waitKey(0)
    
    cv2.destroyAllWindows()
    
    cap.release()
    
if __name__ == "__main__":
    num_frames = 1000
    calibrate(num_frames)