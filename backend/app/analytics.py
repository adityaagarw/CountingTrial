from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from fastapi_utils.inferring_router import InferringRouter
from pydantic import BaseModel, Field
from db.db_service import DBService
from sqlalchemy import Column, DateTime, Float, Integer, String, select, func, extract
from db.schema import DetectionData, SalesData
from typing import List

router = InferringRouter()



class QueryParameters(BaseModel):
    from_datetime: datetime = Field(default = None)
    to_datetime: datetime = Field(default = datetime.now())
    #group_by: str = Field(default = "attribute")
    feed_id: int = Field(default = None)
    #section_id: int = Field(default = None)
    sections: List[int] = Field(default=[])


# Model for request body
class RequestBody(BaseModel):
    from_datetime: datetime
    to_datetime: datetime
    detail_level: str
    feed_id: int


# Model for response data
class SalesVsFootfallResponse(BaseModel):
    time: datetime
    footfall_count: int
    tot_sales: float
    tot_qty: int
    tot_invoices: int


class TrendData(BaseModel):
    monthly: dict
    weekly: dict
    daily: dict
    hourly: dict

async def get_trend_data():
    db = DBService().get_session()
    try:
        # Query for footfall data
        footfall_monthly = db.query(func.count(DetectionData.id)).filter(
            DetectionData.detection_time >= datetime.now() - timedelta(days=30),
            DetectionData.detection_time <= datetime.now(),
            DetectionData.attribute == 'entry'
        ).scalar()
        footfall_weekly = db.query(func.count(DetectionData.id)).filter(
            DetectionData.detection_time >= datetime.now() - timedelta(days=7),
            DetectionData.detection_time <= datetime.now(),
            DetectionData.attribute == 'entry'
        ).scalar()
        footfall_daily = db.query(func.count(DetectionData.id)).filter(
            DetectionData.detection_time >= datetime.now() - timedelta(days=1),
            DetectionData.detection_time <= datetime.now(),
            DetectionData.attribute == 'entry'
        ).scalar()
        footfall_hourly = db.query(func.count(DetectionData.id)).filter(
            DetectionData.detection_time >= datetime.now() - timedelta(hours=1),
            DetectionData.detection_time <= datetime.now(),
            DetectionData.attribute == 'entry'
        ).scalar()

        # Query for sales data
        sales_monthly = db.query(func.sum(SalesData.tot_sales)).filter(
            SalesData.date >= datetime.now() - timedelta(days=30),
            SalesData.date <= datetime.now()
        ).scalar()
        sales_weekly = db.query(func.sum(SalesData.tot_sales)).filter(
            SalesData.date >= datetime.now() - timedelta(days=7),
            SalesData.date <= datetime.now()
        ).scalar()
        sales_daily = db.query(func.sum(SalesData.tot_sales)).filter(
            SalesData.date >= datetime.now() - timedelta(days=1),
            SalesData.date <= datetime.now()
        ).scalar()
        sales_hourly = db.query(func.sum(SalesData.tot_sales)).filter(
            SalesData.date >= datetime.now() - timedelta(hours=1),
            SalesData.date <= datetime.now()
        ).scalar()

        trend_data = TrendData(
            monthly={
                "current": footfall_monthly,
                "previous": 0  # Assuming no previous data
            },
            weekly={
                "current": footfall_weekly,
                "previous": 0  # Assuming no previous data
            },
            daily={
                "current": footfall_daily,
                "previous": 0  # Assuming no previous data
            },
            hourly={
                "current": footfall_hourly,
                "previous": 0  # Assuming no previous data
            }
        )

        return trend_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/trend-data", response_model=TrendData)
async def get_trend_data_endpoint():
    try:
        trend_data = await get_trend_data()
        return trend_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Function to query database based on parameters
async def query_sales_vs_footfall(request_body: RequestBody):
    db = DBService().get_session()

    detail_level = request_body.detail_level
    from_date = request_body.from_datetime
    to_date = request_body.to_datetime
    feed_id = request_body.feed_id

    try:
        if detail_level == 'day-wise':
            results = db.query(
                func.date_trunc('day', DetectionData.detection_time).label("time"),
                func.count(DetectionData.id).label("footfall_count"),
                func.sum(SalesData.tot_sales).label("tot_sales"),
                func.sum(SalesData.tot_qty).label("tot_qty"),
                func.sum(SalesData.tot_invoices).label("tot_invoices")
            ).outerjoin(
                DetectionData,
                func.date_trunc('day', SalesData.date) == func.date_trunc('day', DetectionData.detection_time)
            ).filter(
                DetectionData.feed_id == feed_id,
                DetectionData.attribute == 'entry',
                DetectionData.detection_time >= from_date,
                DetectionData.detection_time <= to_date
            ).group_by(
                func.date_trunc('day', DetectionData.detection_time)
            ).order_by(
                func.date_trunc('day', DetectionData.detection_time)
            ).all()
        elif detail_level == 'hour-wise':
            results = db.query(
                func.date_trunc('hour', DetectionData.detection_time).label("time"),
                func.count(DetectionData.id).label("footfall_count"),
                func.sum(SalesData.tot_sales).label("tot_sales"),
                func.sum(SalesData.tot_qty).label("tot_qty"),
                func.sum(SalesData.tot_invoices).label("tot_invoices")
            ).outerjoin(
                DetectionData,
                func.date_trunc('hour', SalesData.date) == func.date_trunc('hour', DetectionData.detection_time)
            ).filter(
                DetectionData.feed_id == feed_id,
                DetectionData.attribute == 'entry',
                DetectionData.detection_time >= from_date,
                DetectionData.detection_time <= to_date
            ).group_by(
                func.date_trunc('hour', DetectionData.detection_time)
            ).order_by(
                func.date_trunc('hour', DetectionData.detection_time)
            ).all()
        else:
            raise HTTPException(status_code=400, detail="Invalid detail_level. Use 'day-wise' or 'hour-wise'.")

        response_data = []
        for row in results:
            response_data.append({
                "time": row[0],
                "footfall_count": row[1],
                "tot_sales": row[2],
                "tot_qty": row[3],
                "tot_invoices": row[4]
            })

        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# FastAPI endpoint
@router.post("/sales-vs-footfall", response_model=list[SalesVsFootfallResponse])
async def sales_vs_footfall(request_body: RequestBody):
    try:
        result = await query_sales_vs_footfall(request_body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feed-attribute-count")
def get_all_feed_data(parameters: QueryParameters):
    where_clause = {}

    #query = select(DetectionData.attribute, func.count(DetectionData.id), func.date(DetectionData.added_at))
    query = select(
        DetectionData.section_id,
        DetectionData.attribute,
        func.to_char(DetectionData.added_at, 'YYYY-MM-DD HH24:00').label('date'),
        func.count(DetectionData.id)
    )
    if parameters.from_datetime:
        query = query.filter(DetectionData.detection_time >= parameters.from_datetime)
    if parameters.to_datetime:
        query = query.filter(DetectionData.detection_time <= parameters.to_datetime)
    if parameters.feed_id:
        query = query.filter(DetectionData.feed_id == parameters.feed_id)
    if parameters.sections:
        #query = query.filter(DetectionData.section_id == parameters.section_id)
        query = query.filter(DetectionData.section_id.in_(parameters.sections))

    #query = query.group_by(DetectionData.attribute, func.date(DetectionData.added_at))

    # query to group by attributes

    query = query.group_by(DetectionData.section_id, DetectionData.attribute, func.to_char(DetectionData.added_at, 'YYYY-MM-DD HH24:00'))    

    db = DBService().get_session()

    print(query)
    result = db.execute(query)
    result_dict = [result for result in result.mappings().all()]
    print(result_dict)
    return result_dict

