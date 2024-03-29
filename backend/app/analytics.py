from datetime import datetime
from fastapi_utils.inferring_router import InferringRouter
from pydantic import BaseModel, Field
from db.db_service import DBService
from sqlalchemy import select, func
from db.schema import DetectionData

router = InferringRouter()



class QueryParameters(BaseModel):
    from_datetime: datetime = Field(default = None)
    to_datetime: datetime = Field(default = datetime.now())
    #group_by: str = Field(default = "attribute")
    feed_id: int = Field(default = None)
    section_id: int = Field(default = None)




@router.post("/feed-attribute-count")
def get_all_feed_data(parameters: QueryParameters):
    where_clause = {}

    query = select(DetectionData.attribute, func.count(DetectionData.id))

    if parameters.from_datetime:
        query = query.filter(DetectionData.detection_time >= parameters.from_datetime)
    if parameters.to_datetime:
        query = query.filter(DetectionData.detection_time <= parameters.to_datetime)
    if parameters.feed_id:
        query = query.filter(DetectionData.feed_id == parameters.feed_id)
    if parameters.section_id:
        query = query.filter(DetectionData.section_id == parameters.section_id)

    query = query.group_by(DetectionData.attribute)

    db = DBService().get_session()

    print(query)
    result = db.execute(query)
    result_dict = [result for result in result.mappings().all()]
    print(result_dict)
    return result_dict

