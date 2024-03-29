from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.schema import FeedMaster, PIDMaster
from db.db_service import DBService
from pydantic import BaseModel
from datetime import datetime
import subprocess

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
@router.post("/addFeed")
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
@router.get("/getFeeds")
def getFeeds():
    db = DBService().get_session()
    feeds = db.query(FeedMaster).all()
    return feeds

# Fetch all feed IDs
@router.get("/getFeedIds")
def getFeedIds():
    db = DBService().get_session()
    feed_ids = db.query(FeedMaster.id).all()
    feed_ids = [id[0] for id in feed_ids]
    return feed_ids

# Delete specific feed
@router.delete("/deleteFeed/{feed_id}")
def deleteFeed(feed_id: int):
    db = DBService().get_session()
    feed = db.query(FeedMaster).filter(FeedMaster.id == feed_id).first()
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    db.delete(feed)
    db.commit()
    return {"message": "Feed deleted successfully"}

# Start feed
#FIXME: Should run in conda environment
@router.post("/startFeed/{feed_id}")
def startFeed(feed_id: int):
    # Start the avian python program with the feed_id
    proc = subprocess.Popen(['python', '../avian.py', str(feed_id)])#, shell=True)
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
@router.post("/stopFeed/{feed_id}")
def stopFeed(feed_id: int):
    # Kill the avian python program with the feed_id
    # Fetch pid from db
    db = DBService().get_session()
    feed = db.query(PIDMaster).filter(FeedMaster.id == feed_id).first()
    if feed is None:
        raise HTTPException(status_code=404, detail="Feed not found")
    # On linux, use the following command
    # subprocess.Popen(['kill', '-9', feed.pid])
    # On windows, use the following command
    subprocess.Popen(['taskkill', '/F', '/T', '/PID', str(feed.pid)])
    # Delete pid from db
    db.delete(feed)
    db.commit()
    return {"message": "Feed stopped successfully"}