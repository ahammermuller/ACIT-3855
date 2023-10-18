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

cursor.execute('DROP TABLE IF EXISTS distance_covered_reading')

cursor.execute('DROP TABLE IF EXISTS running_pace_reading')

cnx.commit()
cursor.close()
cnx.close()