from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from db.schema import FeedMaster, PIDMaster, SectionMaster
from db.db_service import DBService
from pydantic import BaseModel
from datetime import datetime
import subprocess
import cv2
import os
import numpy as np
import struct
import errno
from pydantic import Field
from fastapi.responses import StreamingResponse, Response
import json
import platform

router = APIRouter()

class FeedInDB(BaseModel):
    cameraId: str 
    name: str 
    location: str
    areaCovered: str
    url: str
    featureList: str
    feedType: str
    config: str

# Add a new route to add a camera
@router.post("/add-feed")
def addFeed(form_data: FeedInDB):
    print(form_data)
    db = DBService().get_session()

    # Add code to insert camera row in the database
    feed = FeedMaster(
        camera_id=form_data.cameraId,
        name=form_data.name,
        location=form_data.location,
        area_covered=form_data.areaCovered,
        url=form_data.url,
        feature_list=form_data.featureList,
        feed_type=form_data.feedType,
        added_at = datetime.now(),
        modified_at = datetime.now(),
        config = form_data.config
    )

    db.add(feed)
    db.commit()
    # Return success message
    return {"message": "Feed added successfully"}

# Fetch all feeds
@router.get("/get-feeds")
def getFeeds():
    db = DBService().get_session()
    feeds = db.query(FeedMaster).all()
    return feeds

# Fetch all feed IDs
@router.get("/get-feed-ids")
def getFeedIds():
    db = DBService().get_session()
    feed_ids = db.query(FeedMaster.id).all()
    feed_ids = [id[0] for id in feed_ids]
    return feed_ids

# Delete specific feed
@router.delete("/delete-feed/{feed_id}")
def deleteFeed(feed_id: int):
    db = DBService().get_session()
    feed = db.query(FeedMaster).filter(FeedMaster.id == feed_id).first()
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    db.delete(feed)
    db.commit()
    return {"message": "Feed deleted successfully"}

# Get feed config
@router.get("/feed-target-resolution/{feed_id}")
def feedTargetResolution(feed_id: int):
    db = DBService().get_session()
    feed = db.query(FeedMaster).filter(FeedMaster.id == feed_id).first()
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    config = eval(feed.config)
    target_height = int(config['target_height'])
    target_width = int(config['target_width'])
    return {"target_height": target_height, "target_width": target_width}

# Get feed image
@router.get("/feed-image/{feed_id}")
def feedImage(feed_id: int):
    db = DBService().get_session()
    feed = db.query(FeedMaster).filter(FeedMaster.id == feed_id).first()
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    # Get image from feed
    config = eval(feed.config)
    target_height = int(config['target_height'])
    target_width = int(config['target_width'])
    cap = cv2.VideoCapture(feed.url)
    ret, frame = cap.read()
    #Encode image
    frame= cv2.resize(frame, (target_width, target_height))
    _, img_encoded = cv2.imencode('.jpg', frame)
    return Response(img_encoded.tobytes(), media_type="image/jpeg")

# Start feed
#FIXME: Should run in conda environment
@router.post("/start-feed/{feed_id}")
def startFeed(feed_id: int):
    # Start the avian python program with the feed_id
    proc = subprocess.Popen(['python', 'avian.py', str(feed_id)])#, shell=True)
    # Store pid in db
    db = DBService().get_session()
    feed = db.query(PIDMaster).filter(PIDMaster.feed_id == feed_id).first()
    if feed is None:
        pid = PIDMaster(
            feed_id=feed_id,
            pid=proc.pid
        )
        db.add(pid)
        db.commit()
    else:
        feed.pid = proc.pid
    return {"message": "Feed started successfully"}

# Stop feed
@router.post("/stop-feed/{feed_id}")
def stopFeed(feed_id: int):
    # Kill the avian python program with the feed_id
    # Fetch pid from db
    db = DBService().get_session()
    print("Killing feed " + str(feed_id))
    feed = db.query(PIDMaster).filter(PIDMaster.feed_id == feed_id).first()
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    #FIXME: Figure out better way to gracefully shutdown subprocess
    if platform.system() == 'Windows':
        subprocess.Popen(['taskkill', '/F', '/T', '/PID', str(feed.pid)])
    else:
        subprocess.Popen(['kill', '-9', str(feed.pid)])
    # Delete pid from db
    db.delete(feed)
    db.commit()
    return {"message": "Feed stopped successfully"}

def save_section(db: Session, section: SectionMaster):
    db.add(section)
    db.commit()
    db.refresh(section)
    return section.id

# Save regions
@router.post("/save-regions/{feed_id}")
async def saveRegions(feed_id: int, request: Request):
    data = await request.json()
    # Parse regions from json to {(x1, y1), (x2, y2), (x3, y3), (x4, y4)} format
    regions = data.get('regions', [])

    for region in regions:
        parsed_region = [
        (region['topLeft']['x'], region['topLeft']['y']),
        (region['topRight']['x'], region['topRight']['y']),
        (region['bottomRight']['x'], region['bottomRight']['y']),
        (region['bottomLeft']['x'], region['bottomLeft']['y'])
        ]
        # Save regions in db
        db = DBService().get_session()
        # Get feed_master details
        feed = db.query(FeedMaster).filter(FeedMaster.id == feed_id).first()
        if feed is None:
            raise HTTPException(status_code=404, detail="Feed not found")
        
        # Get camera_id from feed_master
        camera_id = feed.camera_id
        # Save section_master
        coordinates = str(parsed_region)
        section = SectionMaster(
            camera_id=camera_id,
            feed_id=feed_id,
            coordinates=coordinates,
            section_type="entry_exit",
            extras=""
        )
        section_id = save_section(db, section)
        section.section_name = f"entry_exit_{section_id}"
        db.commit()
        # Append section_id to feed_master
        sections = json.loads(feed.sections) if feed.sections is not None else []
        sections.append(section_id)
        
        feed.sections = json.dumps(sections)
        db.commit()
    return {"message": "Regions saved successfully"}
    
@router.get('/view-feed/{feed_id}')
async def view_feed(feed_id: int):

    pipe_name = "/tmp/avian_pipe_" + str(feed_id)
    pipe_fd = os.open(pipe_name, os.O_RDONLY)# | os.O_NONBLOCK)
    def generate():
        while True:
            try:
                dimensions = os.read(pipe_fd, 3 *4)
                width, height, size = np.frombuffer(dimensions, dtype=np.int32)
                #struct.unpack('iii', dimensions)
                frame_size = width * height * size
                frame_bytes = os.read(pipe_fd, frame_size)
                if not frame_bytes:
                    print("No frame bytes")
                    break  # End of file reached
                
                frame = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = frame.reshape((height, width, size))
                
                # Convert frame to jpeg
                _, img_encoded = cv2.imencode('.jpg', frame)
                frame_bytes_display = img_encoded.tobytes()
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes_display + b'\r\n'
                )
            except Exception as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                    print('No data available to read.')
                else:
                    print(e)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace;boundary=frame")
