import pytz
import connexion
from apscheduler.schedulers.background import BackgroundScheduler
import yaml
import logging
import logging.config
from flask_cors import CORS, cross_origin
import os
import json
import datetime
import requests


scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.start()


with open('app_conf.yml', 'r') as f: 
    app_config = yaml.safe_load(f.read())


with open('log_conf.yml', 'r') as f: 
    log_config = yaml.safe_load(f.read()) 
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


def populate_health():
    """Periodically update the health status of services."""
    logger.info("Start Periodic Health Check")

    default_health = {
        "receiver": "Running",
        "storage": "Down",
        "processing": "Running",
        "audit": "Running",
        "last_update": "2022-03-22T11:12:23"
    }

    # Check if the JSON file exists
    if os.path.exists(app_config['datastore']['filename']):
        logger.info("Health status file exists: %s", app_config['datastore']['filename'])
        # If the file exists, read its contents into the 'stats' dictionary
        with open(app_config['datastore']['filename'], 'r') as file:
            health_stats = json.load(file)
    else:
        # If the file doesn't exist, use default statistics and create the file
        health_stats = default_health
        with open(app_config['datastore']['filename'], 'w') as file:
            logger.info("Health status file does not exist, creating: %s", app_config['datastore']['filename'])
            json.dump(health_stats, file)

    current_timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    timeout = app_config['health_check']['timeout']

    for service_name, service_url in app_config['services'].items():
        response = requests.get(service_url, timeout=timeout)

        try:
            if response.ok:
                status = "Running"
                logger.info("Recorded status of service %s - URL %s - Status Code: %s - Response: %s", service_name, service_url, response.status_code, response.text)
            else:
                status = "Down"
                logger.error("Error checking service %s. Status Code: %s", service_name, response.status_code)
        except requests.RequestException as e:
            status = "Down"
            logger.error("Connection error checking service %s: %s", service_name, str(e))

        
        health_stats[service_name] = status
        logger.info("%s status: %s", service_name, status)

    health_stats['last_update'] = current_timestamp

    # Write the updated statistics to the JSON file
    with open(app_config['datastore']['filename'], 'w') as file:
        json.dump(health_stats, file)

    logger.info("Periodic Health Check completed")


def get_health():
    """Get the health status of services."""

    logger.info("Request for health status has started")

    # Check if the JSON file exists
    if os.path.exists(app_config['datastore']['filename']):
        with open(app_config['datastore']['filename'], 'r') as file:
            health_data = json.load(file)
        
        logger.debug("Health status data: %s", health_data)

        logger.info("Request for health status has completed")
        
        return health_data, 200
    
    else:
        logger.error("Health status file does not exist")
        logger.error("Health status file does not exist: %s", app_config['datastore']['filename'])
        return "Health status data does not exist", 404


def init_scheduler(): 
    sched = BackgroundScheduler(daemon=True) 
    sched.add_job(populate_health, 
                  'interval', 
                  seconds=app_config['health_check']['interval']) 
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')

CORS(app.app) 
app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("openapi.yaml", 
            strict_validation=True, 
            validate_responses=True)


if __name__ == '__main__':
    init_scheduler()
    app.run(port=8120)