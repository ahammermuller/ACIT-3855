import mysql.connector


config = {
    "user": "user",
    "password": "password",
    "host": "ec2-52-14-223-100.us-east-2.compute.amazonaws.com",
    "database": "events",
    "raise_on_warnings": True,
}

cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()

cursor.execute('DROP TABLE IF EXISTS distance_covered_reading')

cursor.execute('DROP TABLE IF EXISTS running_pace_reading')

cnx.commit()
cursor.close()
cnx.close()