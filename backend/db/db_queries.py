from .db_service import DBService
from .schema import *

class DBQueries:

    def __init__(self):
        self.db = DBService()

    def get_sections(self, feed_id):
        return self.db.dispatch(SectionMaster, 'query', SectionMaster.feed_id == feed_id)

    def get_feed_url(self, feed_id):
        feed = self.db.dispatch(FeedMaster, 'query_one', FeedMaster.id == feed_id)
        return feed.url if feed and feed.url else None

    def get_feed_config(self, feed_id): 
        feed = self.db.dispatch(FeedMaster, 'query_one', FeedMaster.id == feed_id)
        return eval(feed.config) if feed and feed.config else None
    
    def get_feed_camera_id(self, feed_id):
        feed = self.db.dispatch(FeedMaster, 'query_one', FeedMaster.id == feed_id)
        return feed.camera_id if feed and feed.camera_id else None
    
    def add_section(self, camera_id, feed_id, coordinates, section_name, section_type, extras):
        section = SectionMaster(
            camera_id=camera_id,
            feed_id=feed_id,
            coordinates=str(coordinates), 
            section_name=section_name,
            section_type=section_type,
            extras=extras
        )
        self.db.dispatch(SectionMaster, 'add', section)

    def new_global_id(self, camera_id, feed_id, section_id, frame_count, added_at, modified_at):
        with self.db.get_session() as session:
            global_id = GlobalIdMaster(
                camera_id=camera_id,
                feed_id=feed_id,
                section_id=section_id,
                frame_count=frame_count,
                added_at=added_at,
                modified_at=modified_at
            )
            session.add(global_id)
            session.commit()
            return global_id.id

    def get_latest_global_id(self):
        global_id_row = self.db.dispatch(GlobalIdMaster, 'query_one', order_by=GlobalIdMaster.id.desc())
        return global_id_row.id if global_id_row else 0
    
    def record_entry_exit(self, feed_id, section_id, global_id, detection_time, attribute, added_at, frame):
        entry_exit = DetectionData(
            feed_id=feed_id,
            section_id=section_id,
            global_id=global_id,
            detection_time=detection_time,
            attribute=attribute,
            added_at=added_at,
            frame_count=frame
        )
        self.db.dispatch(DetectionData, 'add', entry_exit)