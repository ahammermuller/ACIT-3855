import mysql.connector


config = {
    "user": "user",
    "password": "password",
    "host": "18.219.140.116",
    "database": "events",
    "raise_on_warnings": True,
}


cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS distance_covered_reading
        (id INT NOT NULL AUTO_INCREMENT,
        trace_id VARCHAR(100) NOT NULL,
        athlete_id VARCHAR(250) NOT NULL,
        device_id VARCHAR(250) NOT NULL,
        distance FLOAT NOT NULL,
        distance_timestamp VARCHAR(100) NOT NULL,
        date_created VARCHAR(100) NOT NULL,
        CONSTRAINT distance_covered_pk PRIMARY KEY (id))
''')


cursor.execute('''
    CREATE TABLE IF NOT EXISTS running_pace_reading
        (id INT NOT NULL AUTO_INCREMENT,
        trace_id VARCHAR(100) NOT NULL,
        athlete_id VARCHAR(250) NOT NULL,
        average_pace FLOAT NOT NULL,
        elevation INT NOT NULL,
        location VARCHAR(250) NOT NULL,
        pace FLOAT NOT NULL,
        pace_timestamp VARCHAR(100) NOT NULL,
        date_created VARCHAR(100) NOT NULL,
        CONSTRAINT running_pace_pk PRIMARY KEY (id))
''')

cnx.commit()
cursor.close()
cnx.close()