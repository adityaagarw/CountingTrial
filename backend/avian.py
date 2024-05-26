# AVIAN: Advanced Vision Analytics
import asyncio
import base64
from ultralytics import YOLO
import websockets
import simple_counter as counter
import cv2
import numpy as np
import argparse
import pandas as pd
import json
import os
import fcntl
import errno
from db.db_queries import DBQueries
from multiprocessing import shared_memory
import struct
import array
#from connection_manager import ConnectionManager

async def send_image_to_websocket(feed_id, im0, websocket):
    # async with websockets.connect("ws://127.0.0.1:8000/stream") as websocket:
    #resize im0 to 250x250
    im0 = cv2.resize(im0, (250, 250))
    is_success, im_buf_arr = cv2.imencode(".jpg", im0)
    byte_im = base64.b64encode(im_buf_arr).decode('utf-8')
    data = json.dumps({'feed_id': feed_id, 'image': byte_im, 'type': 'stream'})
    await websocket.send(data)

class Avian:
    def __init__(self, section_obj, feed_url, config, feed_id, camera_id, query):
        self.video_path = feed_url
        self.model = YOLO(config["model_name"])
        self.cap = cv2.VideoCapture(feed_url)
        assert self.cap.isOpened(), "Error reading video file"
        self.w, self.h, self.fps = (int(self.cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) #FIXME: Check if this is valid for streaming
        self.classes_to_count = json.loads(config["classes_to_count"]) if config["classes_to_count"] is not None else [0]
        self.num_save_frames = int(config["save_frames"])
        self.num_track_length = int(config["track_length"])
        self.num_buffer_size = int(config["buffer_size"])
        self.format_width = int(config["target_width"]) #or w
        self.format_height = int(config["target_height"]) #or h
        self.sections = section_obj
        self.track_confidence= float(config["track_confidence"])
        self.feed_id = feed_id
        self.camera_id = camera_id
        self.query_obj = query
        #self.manager = ConnectionManager()
        self.shm_test = shared_memory.SharedMemory(name='avian_test', create=True, size=4096000)
        self.websocket = None

    
    def fast_forward_callback(self, event, x, y, flags, param):
        # On right mouse button click, fast forward the video by 250 frames
        if event == cv2.EVENT_RBUTTONDBLCLK:
            to_count = self.cap.get(cv2.CAP_PROP_POS_FRAMES) + 250 if self.cap.get(cv2.CAP_PROP_POS_FRAMES) + 250 < self.frame_count else self.frame_count
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, to_count)
        elif event == cv2.EVENT_LBUTTONDBLCLK:
            to_count = self.cap.get(cv2.CAP_PROP_POS_FRAMES) - 250 if self.cap.get(cv2.CAP_PROP_POS_FRAMES) - 250 > 0 else 0
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, to_count)

    # Async function to send image stream to websocket
    async def run_tracker(self):
        ee_counter_array = []

        for section in self.sections:
            if section.section_type == "entry_exit": #FIXME: Change to feature_id in future
                ee_counter = counter.ObjectCounter(self.feed_id)
                ee_counter_array.append(ee_counter)
                ee_counter.set_args(view_img=True,
                                reg_pts=eval(section.coordinates),
                                classes_names=self.model.names,
                                draw_tracks=True,
                                width = self.format_width,
                                height = self.format_height,
                                fps = self.fps,
                                track_length = self.num_track_length,
                                buffer_size = self.num_buffer_size,
                                save_frames = self.num_save_frames,
                                total_frames = self.frame_count,
                                counter_name = "Counter " + str(section.id),
                                region_id = section.id,
                                camera_id = self.camera_id,
                                feed_id = self.feed_id,
                                query_obj = self.query_obj
                                )

        buffer = self.shm_test.buf
        # async with websockets.connect("ws://127.0.0.1:8000/stream") as websocket:
        while self.cap.isOpened():
            success, im0 = self.cap.read()

            im0 = cv2.resize(im0, (int(self.format_width), int(self.format_height)))
            frame_to_send = im0            
            frame_to_send = cv2.resize(frame_to_send, (250, 250))

            if not success:
                print("Video frame is empty or video processing has been successfully completed.")
                break
            
            # await send_image_to_websocket(self.feed_id, im0, websocket)

            tracks = self.model.track(np.ascontiguousarray(im0), persist=True, show=False, verbose=False,
                                classes=self.classes_to_count, conf=self.track_confidence)
            
            for i in range(len(ee_counter_array)):
                im0 = ee_counter_array[i].start_counting(np.ascontiguousarray(im0), tracks, self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                #cv2.setMouseCallback("Avian Tech " + str(self.feed_id), self.fast_forward_callback)

            while struct.unpack('i', buffer[:4])[0] != 0:
                continue
            
            # lock for producer
            buffer[:4] = array.array("i", [1]).tobytes()

            # convert frame to bytes and get its length
            is_success, im_buf_arr = cv2.imencode(".jpg", frame_to_send)
            frame_bytes = im_buf_arr.tobytes()
            frame_length = len(frame_bytes)

            # put the length of frame bytes at next 4 bytes
            buffer[4:8] = array.array("i", [frame_length]).tobytes()

            # put actual frame bytes
            buffer[8:frame_length+8] = frame_bytes

            # unlock 
            buffer[:4] = array.array("i", [0]).tobytes()

        self.cap.release()
        cv2.destroyAllWindows()

def start_message():
    # Display ascii art
    print("         .  ....         ...     ..            .       ..            ..")
    print("        ...   ..          ..     ..           ...       .. .         ..")
    print("       .. .    ..        ..      ..          .. .      ..  ..        ..")
    print("      ..  .    ..        ..      ..         ..  .      ..   ..       ..")
    print("     ..   .     ..      ..       ..        ..   .      ..   ..      ..")  
    print("    ... ...      ..     ..      ..        ... ...     ..     ..     ..")
    print("   ... ....      ..    ..       ..       ... ....     ..      ..   ..")
    print("  ...     .       ..  ..       ..       ...     .    ..        ..  ..")
    print(" ....     ..       .. ..       ..      ....     ..   ..         .. ..")
    print(".....     ..       ....       ..      .....     ..  ..           ...")
    print("                     ADVANCED VISION ANALYTICS                      ")

if __name__ == "__main__":
    print("Welcome to ...")
    start_message()
    # Parse arguments using arparge for video path
    parser = argparse.ArgumentParser(description="Counting the number of objects in a video")
    parser.add_argument("feed_id", type=str, help="Feed id")
    args = parser.parse_args()
    print("Starting feed ",args.feed_id,"...")
    
    query = DBQueries()
    
    section_obj = query.get_sections(args.feed_id) 
    feed_url = query.get_feed_url(args.feed_id)
    config = query.get_feed_config(args.feed_id)
    camera_id = query.get_feed_camera_id(args.feed_id)
    
    # Add Nonechecks for the objects
    if section_obj is None:
        print("No sections found for feed id ", args.feed_id)
        exit(0)
    
    if feed_url is None:
        print("No feed url found for feed id ", args.feed_id)
        exit(0)
        
    if config is None:
        print("No config found for feed id ", args.feed_id)

    #FIXME: Decide if multiple processes to be spawned for one multiple sections in a feed
    avian = Avian(section_obj, feed_url, config, args.feed_id, camera_id, query)
    # Call a new function for counting the objects in the video
    asyncio.run(avian.run_tracker())