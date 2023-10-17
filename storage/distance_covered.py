from base import Base
from sqlalchemy import Column, Integer, String, DateTime, Float
import datetime


class DistanceCoveredReading(Base):
    """ Distance Covered """

    __tablename__ = "distance_covered_reading"

    id = Column(Integer, primary_key=True)
    trace_id = Column(String(250), nullable=False)
    athlete_id = Column(String(250), nullable=False)
    device_id = Column(String(250), nullable=False)
    distance = Column(Float, nullable=False)
    distance_timestamp = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)


    def __init__(self, trace_id, athlete_id, device_id, distance, distance_timestamp):
        """ Initializes a distance covered reading """
        self.trace_id = trace_id
        self.athlete_id = athlete_id
        self.device_id = device_id
        self.distance = distance
        self.distance_timestamp = distance_timestamp
        self.date_created = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


    def to_dict(self):
        """ Dictionary Representation of a distance covered reading """
        dict = {}
        dict['id'] = self.id
        dict['trace_id'] = self.trace_id
        dict['athlete_id'] = self.athlete_id
        dict['device_id'] = self.device_id
        dict['distance'] = self.distance
        dict['distance_timestamp'] = self.distance_timestamp
        dict['date_created'] = self.date_created

        return dict