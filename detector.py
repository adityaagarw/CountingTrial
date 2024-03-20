# AVIAN: Advanced Vision Analytics
from ultralytics import YOLO
import counter as counter
import cv2
import argparse

def run_detection(video_path):
    classes_to_count = [0]  # We are only counting people  
    # Load the YOLO model
    model = YOLO("yolov8x.pt")
    cap = cv2.VideoCapture(video_path)
    
    # Check if the video file is opened
    assert cap.isOpened(), "Error reading video file"
    # Get the width, height and fps of the video
    w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
    
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        w = 1024
        h = 576

        frame= cv2.resize(frame, (int(w), int(h)))
        # Call the counter fun
        model.track(frame, show=True, classes=classes_to_count, conf=0.15, iou=0.4, persist=False) #), tracker = "bytetrack.yaml")
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Parse arguments using arparge for video path
    parser = argparse.ArgumentParser(description="Counting the number of objects in a video")
    parser.add_argument("video_path", type=str, help="Path to the stream/video")
    args = parser.parse_args()

    # Call a new function for counting the objects in the video
    run_detection(args.video_path)