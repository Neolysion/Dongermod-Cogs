import random
import datetime
import json
import os
import pymysql
import requests

# Connect to the database
from pymysql import MySQLError

log = logging.getLogger(__name__)


class DAO:
    """Custom Dongermod DAO"""

    def __init__(self):
        self.sql_schema_file = '../Activitytracker/dongermod_schema.sql'
        self.member_stats_default_config_file = "../Activitytracker/default_member_stats.json"
        self.connection = self.create_connection()

    def create_connection(self):
        con = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="user",
            password="pw",
            db="dongermod",
            autocommit=True,
        )
        return con

    def get_member_stats_template(self):
        with open(self.member_stats_default_config_file, "r") as json_template_file:
            defaut_conf = json.load(json_template_file)
        return defaut_conf

    def update_member_stats(self, server_id, member_id, j_stats):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT stats_json FROM member_stats WHERE member_fk=%s AND server_fk=%s;"
                cursor.execute(sql, (member_id, server_id))
                c = cursor.fetchone()
                found_data = None
                if c:
                    found_data = c[0]
                if found_data:
                    js_stats = json.dumps(j_stats)
                    sql2 = "UPDATE member_stats SET stats_json = %s WHERE server_fk= %s AND member_fk = %s;"
                    cursor.execute(sql2, (js_stats, server_id, member_id))
                else:
                    js_stats = json.dumps(j_stats)
                    sql3 = "INSERT INTO member_stats (member_fk, server_fk, stats_json) VALUES (%s, %s, %s);"
                    cursor.execute(sql3, (member_id, server_id, js_stats))
            self.connection.commit()
        finally:
            pass

    def get_member_stats(self, server_id, member_id):
        found_data = self.get_member_stats_template()
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT stats_json FROM member_stats WHERE member_fk=%s AND server_fk=%s;"
                cursor.execute(sql, (member_id, server_id))
                c = cursor.fetchone()
                if c:
                    found_data = c[0]
        finally:
            pass
            if isinstance(found_data, dict):
                return found_data
            else:
                return json.loads(found_data)

