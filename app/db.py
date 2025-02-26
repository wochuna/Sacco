import mysql.connector
from flask import current_app


"""def get_db_connection():

    Connects to the MySQL database and returns a connection object.

    Returns:
        mysql.connector.MySQLConnection: A connection object to the database.
    try:
        conn = mysql.connector.connect(
            host=current_app.config['host'],
            database="saccos",
            user=current_app.config['db_username'],
            password=current_app.config['db_password'],  # Add password here
            collation="utf8mb4_general_ci"
        )
        if conn.is_connected():
            print('Connected to MySQL Database')
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None"""

def my_data():
    conn = None
    try:
        conn = mysql.connector.MySQLConnection(
            host = current_app.config['host'],
            database="saccos",
            user=current_app.config['db_username'],
            collation="utf8mb4_general_ci")
        if conn.is_connected():
            print('Connected to MySQL Database')
        return conn
    except mysql.connector.Error as e:
        print(e)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
            