from base import Base
from sqlalchemy import Column, Integer, String, DateTime, Float
import datetime


class RunningPaceReading(Base):
    """ Running Pace """

    __tablename__ = "running_pace_reading"

    id = Column(Integer, primary_key=True)
    trace_id = Column(String(250), nullable=False)
    athlete_id = Column(String(250), nullable=False)
    average_pace = Column(Float, nullable=False)
    elevation = Column(Integer, nullable=False)
    location = Column(String(250), nullable=False)
    pace = Column(Float, nullable=False)
    pace_timestamp = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)


    def __init__(self, trace_id, athlete_id, average_pace, elevation, location, pace, pace_timestamp):
        """ Initializes a running pace reading """
        self.trace_id = trace_id
        self.athlete_id = athlete_id
        self.average_pace = average_pace
        self.elevation = elevation
        self.location = location
        self.pace = pace
        self.pace_timestamp = pace_timestamp
        self.date_created = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


    def to_dict(self):
        """ Dictionary Representation of a running pace reading """
        dict = {}
        dict['id'] = self.id
        dict['trace_id'] = self.trace_id
        dict['athlete_id'] = self.athlete_id
        dict['average_pace'] = self.average_pace
        dict['elevation'] = self.elevation
        dict['location'] = self.location
        dict['pace'] = self.pace
        dict['pace_timestamp'] = self.pace_timestamp
        dict['date_created'] = self.date_created

        return dict