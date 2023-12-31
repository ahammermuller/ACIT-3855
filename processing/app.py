import pytz
import connexion
from connexion import NoContent
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import yaml
import logging
import logging.config
import os
import json
import datetime
from flask_cors import CORS, cross_origin


scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.start()


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


def populate_stats():
    """ Periodically update stats """   
    
    logger.info(f"Start Periodic Processing")

    default_stats = {
    "total_distance_covered": 0,
    "average_pace": 0,
    "max_elevation": 0,
    "num_distance_events_received": 0,
    "num_pace_events_received": 0,
    "last_timestamp": "2016-08-29T09:12:33Z"
    }
        

        # Check if the JSON file exists
    if os.path.exists(app_config['datastore']['filename']):
        # If the file exists, read its contents into the 'stats' dictionary
        with open(app_config['datastore']['filename'], 'r') as file:
            stats = json.load(file)

    else:
        # If the file doesn't exist, use default statistics
        stats = default_stats
        with open(app_config['datastore']['filename'], 'w') as file:
            json.dump(stats, file)


    # Get current datetime
    old_datetime = stats['last_timestamp']
    current_timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Query the two GET endpoints from Data Store Service
    url = app_config['eventstore']['url']

    distance_covered_url = url + "/readings/distance?timestamp=" + old_datetime + "&end_timestamp=" + current_timestamp
    distance_covered_response = requests.get(distance_covered_url)
    distance_covered_events = distance_covered_response.json()
    

    running_pace_url = url + "/readings/pace?timestamp=" + old_datetime + "&end_timestamp=" + current_timestamp
    running_pace_response = requests.get(running_pace_url)
    running_pace_events = running_pace_response.json()
  

    # Initialize variables
    total_distance_covered = stats['total_distance_covered']
    average_pace = stats['average_pace']
    max_elevation = stats['max_elevation']
    num_distance_events_received = stats['num_distance_events_received']
    num_pace_events_received = stats['num_pace_events_received']
    total_pace = 0

    # Log an info message with the number of events received and log an error message in case did not get a 200 response code.   
    if distance_covered_response.status_code == 200:
        num_new_distance_events = len(distance_covered_events) - num_distance_events_received
        
        if num_new_distance_events > 0:
            logger.info(f"Received {num_new_distance_events} new Distance Covered events")
    else:
        logger.error(f"Error fetching Distance Covered. Status code: {distance_covered_response.status_code}")

    # Check if there are new Running Pace events and update the count
    if running_pace_response.status_code == 200:
        num_new_pace_events = len(running_pace_events) - num_pace_events_received

        if num_new_pace_events > 0:
            logger.info(f"Received {num_new_pace_events} new Running Pace events")
    else:
        logger.error(f"Error fetching Running Pace. Status code: {running_pace_response.status_code}")

    # Calculate statistics based on both distance_covered_events and running_pace_events
    # Calculate total distance covered
    for event in distance_covered_events:
        total_distance_covered += event['distance']
        num_distance_events_received += 1

        # Calculate average pace
    for event in running_pace_events:
        total_pace += event['pace']
        num_pace_events_received += 1

    # Calculate average pace outside the loop
    if running_pace_events:
        average_pace = round(total_pace / len(running_pace_events), 2)
        max_elevation = max(max_elevation, event['elevation'])


    # Update stats
    stats['total_distance_covered'] = round(total_distance_covered, 2)
    stats['num_distance_events_received'] = num_distance_events_received
    stats['average_pace'] = average_pace
    stats['max_elevation'] = max_elevation
    stats['num_pace_events_received'] = num_pace_events_received
    stats['last_timestamp'] = str(current_timestamp)

    logger.info("stats before write file:", stats)

    # Write the updated statistics to the JSON file
    with open(app_config['datastore']['filename'], 'w') as file:
        json.dump(stats, file)
        print("write stats at:", (app_config['datastore']['filename']))

    # Log a DEBUG message with your updated statistics values
    logger.debug(f"Total Distance Covered: {total_distance_covered}, "
                f"Average Pace: {average_pace}, " 
                f"Max Elevation: {max_elevation}, "
                f"Num Distance Covered events: {num_distance_events_received}, "
                f"Num Running Pace events: {num_pace_events_received} ")

    # Log info period processing ended
    logger.info(f"Period processing has ended")



def get_stats():

    logger.info(f"Request for statistics has started")

    # Check if the JSON file exists
    if os.path.exists(app_config['datastore']['filename']):
        # If the file exists, read its contents into the 'stats' dictionary
        with open(app_config['datastore']['filename'], 'r') as file:
            stats = json.load(file)

        logger.info(f"Request for statistics has completed")
        
        return stats, 200
    
    else:
        # If the file doesn't exist, log error message and return 404
        logger.error("Statistics file does not exist")
        return "Statistics do not exist", 404


def health():
    return "audit : Running", 200


def init_scheduler(): 
    sched = BackgroundScheduler(daemon=True) 
    sched.add_job(populate_stats, 
                  'interval', 
                  seconds=app_config['scheduler']['period_sec']) 
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("openapi.yaml", base_path="/processing", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    init_scheduler() 
    app.run(port=8100, use_reloader=False)