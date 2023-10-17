import connexion
from connexion import NoContent
import yaml
import logging
import logging.config
import uuid
import datetime
import json
from pykafka import KafkaClient


with open('app_conf.yml', 'r') as f: 
    app_config = yaml.safe_load(f.read())


with open('log_conf.yml', 'r') as f: 
    log_config = yaml.safe_load(f.read()) 
    logging.config.dictConfig(log_config)


logger = logging.getLogger('basicLogger')

def report_distance_covered_reading(body):
    
    event_name = "eventstore1"
    trace_id = str(uuid.uuid4())
    body['trace_id'] = trace_id

    logger.info(f"Received event {event_name} request with a trace id of {trace_id}")
    
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])] 
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

    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}") 
    topic = client.topics[str.encode(app_config['events']['topic'])] 
    producer = topic.get_sync_producer()
    msg = { "type": "running_pace", 
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), 
           "payload": body } 
    msg_str = json.dumps(msg) 
    producer.produce(msg_str.encode('utf-8'))

    logger.info(f"Returned event {event_name} response (ID: {trace_id}) with status code 201")

    return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", 
            strict_validation=True, 
            validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)