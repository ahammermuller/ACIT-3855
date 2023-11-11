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

with open('app_conf.yml', 'r') as f: 
    app_config = yaml.safe_load(f.read())


with open('log_conf.yml', 'r') as f: 
    log_config = yaml.safe_load(f.read()) 
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


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

        # Write the updated statistics to the JSON file
    with open(app_config['datastore']['filename'], 'w') as file:
        json.dump(stats, file)

    # Get current datetime
    old_datetime = default_stats['last_timestamp']
    current_timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Query the two GET endpoints from Data Store Service
    event_name = "eventstore"
    url = app_config.get(event_name, {}).get("url")

    distance_covered_url = f"{url}/readings/distance?timestamp={old_datetime}&timestamp={current_timestamp}" # Lab 11
    distance_covered_response = requests.get(distance_covered_url)

    running_pace_url = f"{url}/readings/pace?timestamp={old_datetime}&timestamp={current_timestamp}" # Lab 11
    running_pace_response = requests.get(running_pace_url)

    logger.debug(f"Distance Covered URL: {distance_covered_url}")
    logger.debug(f"Running Pace URL: {running_pace_url}")

    # Log an info message with the number of events received and log an error message in case did not get a 200 response code.   
    if distance_covered_response.status_code == 200:
        distance_covered_events = distance_covered_response.json()
        num_new_distance_events = len(distance_covered_events) - stats['num_distance_events_received']
        if num_new_distance_events > 0:
            stats['num_distance_events_received'] += num_new_distance_events
            logger.info(f"Received {num_new_distance_events} new Distance Covered events")
    else:
        logger.error(f"Error fetching Distance Covered. Status code: {distance_covered_response.status_code}")
        logger.error(f"Response content: {distance_covered_response.text}")

    # Check if there are new Running Pace events and update the count
    if running_pace_response.status_code == 200:
        running_pace_events = running_pace_response.json()
        num_new_pace_events = len(running_pace_events) - stats['num_pace_events_received']
        if num_new_pace_events > 0:
            stats['num_pace_events_received'] += num_new_pace_events
            logger.info(f"Received {num_new_pace_events} new Running Pace events")
    else:
        logger.error(f"Error fetching Running Pace. Status code: {running_pace_response.status_code}")



    # Calculate statistics such as total distance covered, average pace and max elevation. 
    
    # Initialize default stats
    total_distance_covered = 0
    average_pace = 0
    max_elevation = 0
    num_distance_events_received = 0
    num_pace_events_received = 0

    # Calculate total distance covered
    for event in distance_covered_events:
        total_distance_covered += event['distance']

    # Calculate average pace
    if running_pace_events:
        total_pace = 0
        for event in running_pace_events:
            total_pace += event['pace']
        average_pace = round(total_pace / len(running_pace_events),2)

    # Calculate max elevation
    if running_pace_events:
        max_elevation = running_pace_events[0]['elevation']
        for event in running_pace_events:
            max_elevation = max(max_elevation, event['elevation'])


    # Calclulate num distance covered events and pace events received
    num_distance_events_received += len(distance_covered_events)
    num_pace_events_received += len(running_pace_events)

    # Update default stats
    default_stats['total_distance_covered'] = round(total_distance_covered, 2)
    default_stats['average_pace'] = average_pace
    default_stats['max_elevation'] = max_elevation
    default_stats['num_distance_events_received'] = num_distance_events_received
    default_stats['num_pace_events_received'] = num_pace_events_received
    default_stats['last_timestamp'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


    # Write the updated statistics to the JSON file
    with open(app_config['datastore']['filename'], 'w') as file:
        json.dump(default_stats, file)


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
        
        # Log a DEBUG message with the contents of the Python Dictionary
        logger.debug(f"Statistics data: {stats}")

        logger.info(f"Request for statistics has completed")
        
        return stats, 200
    
    else:
        # If the file doesn't exist, log error message and return 404
        logger.error("Statistics file does not exist")
        return "Statistics do not exist", 404


def init_scheduler(): 
    sched = BackgroundScheduler(daemon=True) 
    sched.add_job(populate_stats, 
                  'interval', 
                  seconds=app_config['scheduler']['period_sec']) 
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')

CORS(app.app) 
app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("openapi.yaml", 
            strict_validation=True, 
            validate_responses=True)


if __name__ == "__main__":
    init_scheduler() 
    app.run(port=8100, use_reloader=False)