import connexion
from connexion import NoContent
import yaml
import logging
import logging.config
import uuid
import datetime
import json
from pykafka import KafkaClient
import time
import os


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

# External Logging Configuration
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
    
logger = logging.getLogger('basicLogger')
logger.info("App Conf File: %s" % app_conf_file) 
logger.info("Log Conf File: %s" % log_conf_file)


    # Connect to kafka with retries

hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
events_config = app_config["events"]
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


def report_distance_covered_reading(body):
    
    event_name = "eventstore1"
    trace_id = str(uuid.uuid4())
    body['trace_id'] = trace_id

    logger.info(f"Received event {event_name} request with a trace id of {trace_id}")
    
    # client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    # topic = client.topics[str.encode(app_config["events"]["topic"])]

    producer = topic.get_sync_producer()
    msg = { "type": "distance_covered", 
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), 
           "payload": body } 
    msg_str = json.dumps(msg) 
    producer.produce(msg_str.encode('utf-8'))

    logger.info(f"Returned event {event_name} response (ID: {trace_id}) with status code 201")

    return NoContent, 201


def report_running_pace_reading(body):

    event_name = "eventstore2"
    trace_id = str(uuid.uuid4())
    body['trace_id'] = trace_id
    logger.info(f"Received event {event_name} request with a trace id of {trace_id}")

    #client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}") 
    # topic = client.topics[str.encode(app_config["events"]["topic"])]

    producer = topic.get_sync_producer()

    msg = { "type": "running_pace", 
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), 
           "payload": body } 
    msg_str = json.dumps(msg) 
    producer.produce(msg_str.encode('utf-8'))

    logger.info(f"Returned event {event_name} response (ID: {trace_id}) with status code 201")

    return NoContent, 201


def health():
    return "audit : Running", 200


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", 
            strict_validation=True, 
            validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)