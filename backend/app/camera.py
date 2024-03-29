from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.schema import CameraMaster
from db.db_service import DBService
from pydantic import BaseModel
from datetime import datetime
router = APIRouter()

class CameraInDB(BaseModel):
    cameraUrlId: str
    cameraType: str
    resolution: str
    fps: int
    focalLength: int
    mac: str
    protocols: str
    uid: str
    pwd: str
    port: str
    makeModel: str

# Add a new route to add a camera
@router.post("/addCamera")
def addCamera(form_data: CameraInDB):
    db = DBService().get_session()

    # Add code to insert camera row in the database
    camera = CameraMaster(
        camera_url_id=form_data.cameraUrlId,
        camera_type=form_data.cameraType,
        resolution=form_data.resolution,
        fps=form_data.fps,
        focal_length=form_data.focalLength,
        mac=form_data.mac,
        protocols=form_data.protocols,
        uid=form_data.uid,
        pwd=form_data.pwd,
        port=form_data.port,
        make_model=form_data.makeModel,
        added_at = datetime.now(),
        modified_at = datetime.now()
    )
    
    db.add(camera)
    db.commit()
    # Return success message
    return {"message": "Camera added successfully"}

# Fetch all cameras
@router.get("/getCameras")
def getCamera():
    db = DBService().get_session()
    cameras = db.query(CameraMaster).all()
    return cameras

# Fetch all camera IDs
@router.get("/getCameraIds")
def getCameraIds():
    db = DBService().get_session()
    camera_ids = db.query(CameraMaster.id).all()
    camera_ids = [id[0] for id in camera_ids]
    return camera_ids

@router.delete("/deleteCamera/{camera_id}")
def deleteCamera(camera_id: int):
    db = DBService().get_session()
    camera = db.query(CameraMaster).filter(CameraMaster.id == camera_id).first()
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    db.delete(camera)
    db.commit()
    return {"message": "Camera deleted successfully"}