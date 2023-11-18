import connexion
from connexion import NoContent
from base import Base
from sqlalchemy.orm import sessionmaker
from distance_covered import DistanceCoveredReading
from running_pace import RunningPaceReading
from sqlalchemy import create_engine
from sqlalchemy import and_
import yaml
import logging.config
import datetime
import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import time


with open('app_conf.yml', 'r') as f: 
    app_config = yaml.safe_load(f)

db_config = app_config["datastore"]
events_config = app_config["events"]

# Create the DB_ENGINE using the extracted configuration values
DB_ENGINE = create_engine(
    f'mysql+pymysql://{db_config["user"]}:{db_config["password"]}@{db_config["hostname"]}:{db_config["port"]}/{db_config["db"]}'
)
Base.metadata.bind = DB_ENGINE

with open('log_conf.yml', 'r') as f: 
    log_config = yaml.safe_load(f.read()) 
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info(f"Connecting to DB. Hostname: {db_config['hostname']}, Port: {db_config['port']}")

DB_SESSION = sessionmaker(bind=DB_ENGINE)

    # Connect to kafka with retries



# def report_distance_covered_reading(body):
#     """ Receives a distance covered reading """

#     session = DB_SESSION()

#     dc = DistanceCoveredReading(body['trace_id'],
#                                 body['athlete_id'],
#                                 body['device_id'],
#                                 body['distance'],
#                                 body['distance_timestamp'])

#     session.add(dc)

#     session.commit()
#     session.close()

#     event_name = 'eventstore1'
#     logger.debug(f"Stored event {event_name} request with a trace id of {body['trace_id']}")

#     return NoContent, 201

def get_distance_covered_reading(timestamp, end_timestamp): 
    """ Gets new distance covered readings after the timestamp """ 
    logger.info(f"GET request for distance covered readings with timestamp between: {timestamp} and {end_timestamp}")
    
    session = DB_SESSION() 
    
    # timestamp_datetime = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    # end_timestamp_datetime = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    
    readings = session.query(DistanceCoveredReading).filter(
        and_(DistanceCoveredReading.date_created >= timestamp_datetime, DistanceCoveredReading.date_created < end_timestamp_datetime))

    results_list = [] 
    for reading in readings: 
        results_list.append(reading.to_dict()) 
    
    session.close() 
    logger.info("Query for Distance Covered readings after %s returns %d results" % (timestamp, len(results_list))) 


    return results_list, 200

# def report_running_pace_reading(body):
#     """ Receives a running pace reading """

#     session = DB_SESSION()

#     rp = RunningPaceReading(body['trace_id'],
#                             body['athlete_id'],
#                             body['average_pace'],
#                             body['elevation'],
#                             body['location'],
#                             body['pace'],
#                             body['pace_timestamp'])

#     session.add(rp)
#     session.commit()
#     session.close()

#     event_name = 'eventstore2'
#     logger.debug(f"Stored event {event_name} request with a trace id of {body['trace_id']}")

#     return NoContent, 201

def get_running_pace_reading(timestamp, end_timestamp): 
    """ Gets new running pace readings after the timestamp """ 
    logger.info(f"GET request for running pace readings with timestamp: {timestamp}")
    session = DB_SESSION() 
    
    # timestamp_datetime = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    # end_timestamp_datetime = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    readings = session.query(RunningPaceReading).filter(
        and_(RunningPaceReading.date_created >= timestamp_datetime, RunningPaceReading.date_created < end_timestamp_datetime))

    results_list = [] 
    for reading in readings: 
        results_list.append(reading.to_dict()) 
    
    session.close() 
    logger.info("Query for Running Pace readings after %s returns %d results" % (timestamp, len(results_list))) 
    
    return results_list, 200


def process_messages():
    """ Process event messages """

    #client = KafkaClient(hosts=hostname) 
    #topic = client.topics[str.encode(app_config["events"]["topic"])] 
    
    # Create a consume on a consumer group, that only reads new messages (uncommitted messages) when the service re-starts 
    # (i.e., it doesn't read all the old messages from the history in the message queue). 
    
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    max_retries = 10
    retry_interval = events_config["sleep_time"]

    current_retry_count = 0
    connected = False

    while current_retry_count < max_retries and not connected:
        try:
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]        
            connected = True
            logger.info("Successfully connected to Kafka.")        
        except Exception as e:
            logger.error(f"Connection to Kafka failed after {current_retry_count}")
            time.sleep(retry_interval)
            current_retry_count += 1

    if not connected:
        raise Exception(f"Failed to connect to Kafka after {max_retries} retries")

    consumer = topic.get_simple_consumer(consumer_group=b'event_group', reset_offset_on_start=False, auto_offset_reset=OffsetType.LATEST) 

        # This is blocking - it will wait for a new message 
    
    for msg in consumer: 
        msg_str = msg.value.decode('utf-8') 
        msg = json.loads(msg_str) 
        logger.info("Message: %s" % msg) 
                    
        payload = msg["payload"] 
                
        if msg["type"] == "distance_covered":
            # Store the event2 (i.e., the payload) to the DB 
            dc = DistanceCoveredReading(payload['trace_id'],
                                        payload['athlete_id'],
                                        payload['device_id'],
                                        payload['distance'],
                                        payload['distance_timestamp'])
                        
            session = DB_SESSION()
            session.add(dc)
            session.commit()
            session.close()
            logger.info("Stored event1 to the database: %s" % payload)

        elif msg["type"] == "running_pace":
            # Store the event2 (i.e., the payload) to the DB 
            rp = RunningPaceReading(payload['trace_id'],
                                    payload['athlete_id'],
                                    payload['average_pace'],
                                    payload['elevation'],
                                    payload['location'],
                                    payload['pace'],
                                    payload['pace_timestamp'])
                        
            session = DB_SESSION()
            session.add(rp)
            session.commit()
            session.close()
            logger.info("Stored event2 to the database: %s" % payload)

                        
        # Commit the new message as being read 
        consumer.commit_offsets()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", 
            strict_validation=True, 
            validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages) 
    t1.setDaemon(True) 
    t1.start()
    app.run(port=8090, threaded=True)