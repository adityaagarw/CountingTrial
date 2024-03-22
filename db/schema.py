from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Date
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector


Base = declarative_base()

class CameraMaster(Base):
    __tablename__ = 'camera_master'

    id = Column(Integer, primary_key=True)
    camera_url_id = Column(String)
    camera_type = Column(String)
    resolution = Column(String)
    fps = Column(Integer)
    focal_length = Column(Integer)
    mac = Column(String)
    protocols = Column(String)  # Storing protocols as a string
    uid = Column(String)
    pwd = Column(String)  # Storing hashed password as a string
    port = Column(String)
    make_model = Column(String)
    added_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)

    # Define the relationship with the CameraUrl table
    # camera_url = relationship("CameraUrl")


class FeedMaster(Base):
    __tablename__ = 'feed_master'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('camera_master.id'))
    name = Column(String)
    location = Column(String)
    sections = Column(String)
    area_covered = Column(String)
    url = Column(String)
    feature_list = Column(String)  # Storing feature list as a string
    feed_type = Column(String)
    added_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    config = Column(String)


    # Define the relationship with the CameraMaster table
    camera = relationship("CameraMaster")


class SectionMaster(Base):
    __tablename__ = 'section_master'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('camera_master.id'))
    feed_id = Column(Integer, ForeignKey('feed_master.id'))
    coordinates = Column(String)
    section_name = Column(String)
    section_type = Column(String)
    extras = Column(String)

    # Define the relationships with the CameraMaster and FeedMaster tables
    camera = relationship("CameraMaster")
    feed = relationship("FeedMaster")

class GlobalIdMaster(Base):
    __tablename__ = 'global_id_master'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('camera_master.id'))
    feed_id = Column(Integer, ForeignKey('feed_master.id'))
    section_id = Column(Integer, ForeignKey('section_master.id'))
    frame_count = Column(Integer)
    added_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)

    # Define the relationships with the CameraMaster, FeedMaster, and SectionMaster tables
    camera = relationship("CameraMaster")
    feed = relationship("FeedMaster")
    section = relationship("SectionMaster")
    
class FeatureMaster(Base):
    __tablename__ = 'feature_master'

    id = Column(Integer, primary_key=True)
    desc = Column(String)
    name = Column(String)
    dependencies = Column(String)
    specifications = Column(String)

class DetectionData(Base):
    __tablename__ = 'detection_data'

    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey('feed_master.id'))
    section_id = Column(Integer, ForeignKey('section_master.id'))
    global_id = Column(Integer, ForeignKey('global_id_master.id'))
    detection_time = Column(TIMESTAMP)
    attribute = Column(String)
    added_at = Column(TIMESTAMP)
    frame_count = Column(Integer)

    # Define the relationships with the FeedMaster, SectionMaster, and GlobalIdMaster tables
    feed = relationship("FeedMaster")
    section = relationship("SectionMaster")
    global_id = relationship("GlobalIdMaster")


class PersonMaster(Base):
    __tablename__ = 'person_master'

    id = Column(Integer, primary_key=True)
    primary_embedding = Column(Vector(2048))
    secondary_embeddings = Column(ARRAY(Vector(2048)))
    added_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    person_type = Column(String)

class BusinessMaster(Base):
    __tablename__ = 'business_master'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)
    installation_date = Column(Date)
    activation_date = Column(Date) 
    expiry_date = Column(Date)
    license_status = Column(String)
    deployment_type = Column(String)

# Create an engine to connect to the PostgreSQL database using Docker
engine = create_engine('postgresql://avian-admin:avian-password@localhost:5432/avian-db')

# Bind the engine to the base class
Base.metadata.bind = engine

# Create the tables based on the defined models if they don't already exist
Base.metadata.create_all(engine)
