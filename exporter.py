import json
import mysql.connector
from mysql.connector import Error

class DataExporter:
    def __init__(self, user, password, host, database):
        self.config = {
            'user': user,
            'password': password,
            'host': host,
            'database': database
        }
        self.cnx = None

    def connect(self):
        try:
            self.cnx = mysql.connector.connect(**self.config)
            if self.cnx.is_connected():
                print("Connected to MySQL")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.cnx = None

    def close(self):
        if self.cnx and self.cnx.is_connected():
            self.cnx.close()
            print("MySQL connection closed")

    def export_to_mysql(self, url, data, table_name="news_table"):
        if not self.cnx or not self.cnx.is_connected():
            self.connect()
            if not self.cnx:
                raise Exception("MySQL connection failed")

        cursor = self.cnx.cursor()
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            sql = f"INSERT INTO {table_name} (url, parsed_data) VALUES (%s, %s)"
            cursor.execute(sql, (url, json_data))
            self.cnx.commit()
            print(f"{cursor.rowcount} records inserted into `{table_name}`")
        except Error as e:
            self.cnx.rollback()
            raise Exception(f"Error inserting data into MySQL: {e}")
        finally:
            cursor.close()
            self.close()

    