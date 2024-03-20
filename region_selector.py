import cv2
import argparse
import pandas as pd
import numpy as np

# Global variables
selecting = False
moving_points = []
pt1 = (0, 0)
pt2 = (0, 0)
img_show = None
coordinates = []
selected_index = -1

def select_region_callback(event, x, y, flags, param):
    global selecting, moving_points, pt1, pt2, img_show, coordinates, selected_index
    if event == cv2.EVENT_LBUTTONDOWN:
        # Check if clicked near any existing rectangle point
        for i, coord in enumerate(coordinates):
            for j, point in enumerate(coord):
                if np.hypot(x - point[0], y - point[1]) < 10:
                    selected_index = i
                    moving_points = [j]
                    coordinates[i][j] = (x, y)
                    break
            else:
                if cv2.pointPolygonTest(np.array(coord, np.int32), (x, y), False) >= 0:
                    selected_index = i
                    moving_points = coord
                    break
        else:
            selecting = True
            pt1 = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        selecting = False
        moving_points = []
        if selected_index == -1:
            pt2 = (x, y)
            coordinates.append([pt1, (pt2[0], pt1[1]), pt2, (pt1[0], pt2[1])])
        selected_index = -1
    elif event == cv2.EVENT_MOUSEMOVE:
        if moving_points:
            if len(moving_points) == 1:
                coordinates[selected_index][moving_points[0]] = (x, y)
            else:
                dx = x - moving_points[0][0]
                dy = y - moving_points[0][1]
                for i in range(len(moving_points)):
                    coordinates[selected_index][i] = (moving_points[i][0] + dx, moving_points[i][1] + dy)
                moving_points = coordinates[selected_index]
        elif selecting:
            pt2 = (x, y)
    elif event == cv2.EVENT_RBUTTONDBLCLK:
        # Check if clicked near any existing rectangle point
        for i, coord in enumerate(coordinates):
            if cv2.pointPolygonTest(np.array(coord, np.int32), (x, y), False) >= 0:
                coordinates.pop(i)
                break

def draw_point(image, point):
    cv2.circle(image, point, 5, (255, 0, 0), -1)

def select_region(image_path):
    global selecting, moving_points, pt1, pt2, img_show, coordinates, selected_index

    video_name = get_video_name(image_path)
    # Load the image or video frame
    if image_path.endswith('.mp4') or image_path.endswith('.avi'):
        cap = cv2.VideoCapture(image_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 9)  # Set to the 10th frame
        ret, image = cap.read()
        if not ret:
            print("Error: Unable to read frame from the video.")
            return
    else:
        image = cv2.imread(image_path)
        if image is None:
            print("Error: Unable to load image.")
            return

    new_h = 576
    new_w = 1024
    image = cv2.resize(image, (int(new_w), int(new_h)))

    # Create a window and set mouse callback
    cv2.namedWindow('Select Region')
    cv2.setMouseCallback('Select Region', select_region_callback)

    img_show = image.copy()

    while True:
        img_display = img_show.copy()
        for coord in coordinates:
            cv2.polylines(img_display, [np.array(coord, np.int32)], True, (0, 255, 0), thickness=2)
            for point in coord:
                draw_point(img_display, point)
        if selecting:
            cv2.rectangle(img_display, pt1, pt2, (255, 0, 0), 2)
            for point in [pt1, (pt2[0], pt1[1]), pt2, (pt1[0], pt2[1])]:
                draw_point(img_display, point)
        elif moving_points:
            selected_coord = coordinates[selected_index]
            cv2.polylines(img_display, [np.array(selected_coord, np.int32)], True, (255, 0, 0), thickness=2)
            for point in selected_coord:
                draw_point(img_display, point)

        cv2.imshow('Select Region', img_display)

        # Wait for 'r' key to save the selected regions
        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'):
            excel_file = video_name + ".xlsx"
            df = pd.DataFrame([np.array(coord).reshape(-1) for coord in coordinates], columns=['x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4'])
            df.to_excel(excel_file, index=False)
            print("Selected regions saved to '" + excel_file + "'")
            break

        # Wait for ESC key to exit
        elif key == 27:
            break

    cv2.destroyAllWindows()

def get_video_name(video_path):
    # Split the video path to get the video name
    video_name = video_path.split("/")[-1]
    # Split the video name to get the video name without the extension
    video_name_without_extension = video_name.split(".")[0]
    # Return the video name and the video name without the extension
    return video_name_without_extension

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Select regions on an image or video')
    parser.add_argument('path', type=str, help='Path to the image or video')
    args = parser.parse_args()
    select_region(args.path)