from pykafka import KafkaClient
import json
import yaml
import logging
import logging.config
import connexion
from connexion import NoContent
from flask_cors import CORS, cross_origin
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


def get_distance_covered_reading(index):
    """ Get DC Reading in History """ 
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"]) 
    client = KafkaClient(hosts=hostname) 
    topic = client.topics[str.encode(app_config["events"]["topic"])] 
    
    # Here we reset the offset on start so that we retrieve # messages at the beginning of the message queue. 
    # To prevent the for loop from blocking, we set the timeout to # 100ms. 
    # There is a risk that this loop never stops if the # index is large and messages are constantly being received! 
    
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000) 
    
    logger.info("Retrieving DC at index %d" % index) 
    
    count = 0
    try: 
        for msg in consumer: 
            msg_str = msg.value.decode('utf-8') 
            msg = json.loads(msg_str) 
            # Find the event at the index you want and # return code 200 # i.e., return event, 200 
            
            if msg["type"] == "distance_covered":
                count += 1
                if count == index:
                    return msg["payload"], 200
    except: 
        logger.error("No more messages found") 
        logger.error("Could not find BP at index %d" % index) 
    return { "message": "Not Found"}, 404

def get_running_pace_reading(index):
    """ Get DC Reading in History """ 
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"]) 
    client = KafkaClient(hosts=hostname) 
    topic = client.topics[str.encode(app_config["events"]["topic"])] 
    
    # Here we reset the offset on start so that we retrieve # messages at the beginning of the message queue. 
    # To prevent the for loop from blocking, we set the timeout to # 100ms. 
    # There is a risk that this loop never stops if the # index is large and messages are constantly being received! 
    
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000) 
    
    logger.info("Retrieving BP at index %d" % index) 
    
    
    count = 0
    try: 
        for msg in consumer: 
            msg_str = msg.value.decode('utf-8') 
            msg = json.loads(msg_str)
            
            if msg["type"] == "running_pace":
                count += 1
                if count == index:
                    return msg["payload"], 200
            # Find the event at the index you want and # return code 200 # i.e., return event, 200 
    
    except: 
        logger.error("No more messages found") 
        logger.error("Could not find PC at index %d" % index) 
    return { "message": "Not Found"}, 404


def health():
    return "audit : Running", 200


app = connexion.FlaskApp(__name__, specification_dir='')

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("openapi.yaml", base_path="/audit_log", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    app.run(port=8070)