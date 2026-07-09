import psycopg2

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="vehicle_db",
        user="postgres",
        password="moiz123"
    )
    return conn