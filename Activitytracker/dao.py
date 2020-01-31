import random
import datetime
import json
import os
import pymysql
import requests

# Connect to the database
from pymysql import MySQLError

class DAO():
    """Custom Dongermod DAO"""

    def __init__(self):
        self.sql_schema_file = '../Activitytracker/dongermod_schema.sql'
        self.server_default_config_file = "../Activitytracker/default_server_config.json"
        self.member_stats_default_config_file = "../Activitytracker/default_member_stats.json"
        self.connection = self.create_connection()

    def create_connection(self):
        con = pymysql.connect(host='127.0.0.1',
                                    port=3306,
                                    user='user',
                                    password='pw',
                                    db='dongermod',
                                    autocommit=True)
        return con


    def get_server_config_template(self):
        with open(server_default_config_file, "r") as json_template_file:
            defaut_conf = json.load(json_template_file)
        return defaut_conf


    def get_member_stats_template(self):
        with open(self.member_stats_default_config_file, "r") as json_template_file:
            defaut_conf = json.load(json_template_file)
        return defaut_conf


    def add_new_server(self, server_id):
        try:
            with connection.cursor() as cursor:
                default_config = get_server_config_template()
                sql1 = 'INSERT INTO queue VALUES ();'
                cursor.execute(sql1)
                created_queue_id = cursor.lastrowid

                config_as_string = json.dumps(default_config)
                sql2 = "INSERT INTO server (server_discord_id,queue_fk, server_configuration_json) VALUES (%s, %s, %s);"
                cursor.execute(sql2, (server_id, created_queue_id, config_as_string))
            connection.commit()
        finally:
            print("added new server")


    def update_server_config(self, server_id, config):
        try:
            with connection.cursor() as cursor:
                config_as_string = json.dumps(config)
                sql = 'UPDATE server SET server_configuration_json = %s WHERE server_discord_id = %s;'
                cursor.execute(sql, (config_as_string, server_id))
            connection.commit()
        except MySQLError as e:
            print('MYSQL error: {!r}, errno is {}'.format(e, e.args[0]))


    def update_last_invite_info(self, server_id, info_jid):
        try:
            with connection.cursor() as cursor:
                info_jid_as_string = json.dumps(info_jid)
                sql = 'UPDATE server SET last_invite_info_json = %s WHERE server_discord_id = %s;'
                cursor.execute(sql, (info_jid_as_string, server_id))
            connection.commit()
        finally:
            pass


    def update_steam_id(self, user_id, steam_id):
        try:
            with connection.cursor() as cursor:
                sql = 'UPDATE member SET steam_id = %s WHERE discord_id = %s;'
                cursor.execute(sql, (steam_id, user_id))
            connection.commit()
        finally:
            pass


    def update_afk_flag(self, user_id, value):
        try:
            with connection.cursor() as cursor:
                sql = 'UPDATE member SET do_not_invite = %s WHERE discord_id = %s;'
                cursor.execute(sql, (value, user_id))
            connection.commit()
        finally:
            pass


    def append_sub_to_queue(self, server_id, user_id):
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT queue_fk FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))

                q_id = cursor.fetchone()

                sql2 = 'INSERT IGNORE INTO member (discord_id) VALUES (%s);'
                cursor.execute(sql2, (user_id,))

                if not get_member_stats(server_id, user_id):
                    update_member_stats(server_id, user_id, get_member_stats_template())
                sql3 = 'INSERT INTO member_queue (queue_fk, member_fk, join_date) VALUES (%s, %s, %s);'
                cursor.execute(sql3, (q_id, user_id, datetime.datetime.now()))
            connection.commit()
        finally:
            pass


    def append_sub_to_banlist(self, server_id, user_id):
        try:
            with connection.cursor() as cursor:
                banlist = get_banlist(server_id)
                banlist.append(user_id)
                jbanlist = json.dumps(banlist)
                sql = 'UPDATE server SET ban_list_json = %s WHERE server_discord_id = %s'
                cursor.execute(sql, (jbanlist, server_id))
            connection.commit()
        finally:
            pass


    def append_sub_to_invite_list(self, server_id, user_id):
        try:
            with connection.cursor() as cursor:
                invite_list = get_invite_list(server_id)
                invite_list.append(user_id)
                jinvite_list = json.dumps(invite_list)
                sql = 'UPDATE server SET invite_list_json = %s WHERE server_discord_id = %s'
                cursor.execute(sql, (jinvite_list, server_id))
            connection.commit()
        finally:
            pass


    def append_sub_to_accept_list(self, server_id, user_id):
        try:
            with connection.cursor() as cursor:
                accept_list = get_accepted_list(server_id)
                accept_list.append(user_id)
                jaccept_list = json.dumps(accept_list)
                sql = 'UPDATE server SET accept_list_json = %s WHERE server_discord_id = %s'
                cursor.execute(sql, (jaccept_list, server_id))
            connection.commit()
        finally:
            pass


    def remove_sub_from_queue(self, server_id, user_id):
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT queue_fk FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))
                q_id = cursor.fetchone()

                sql2 = 'DELETE FROM member_queue WHERE member_fk = %s AND queue_fk = %s;'
                cursor.execute(sql2, (user_id, q_id))
            connection.commit()
        finally:
            pass


    def remove_sub_from_banlist(self, server_id, user_id):
        try:
            with connection.cursor() as cursor:
                banlist = get_banlist(server_id)
                banlist.remove(user_id)
                jbanlist = json.dumps(banlist)
                sql = 'UPDATE server SET ban_list_json = %s WHERE server_discord_id = %s;'
                cursor.execute(sql, (jbanlist, server_id))
            connection.commit()
        finally:
            pass


    def wipe_queue(self, server_id):
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT queue_fk FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))
                q_id = cursor.fetchone()

                sql2 = 'DELETE FROM member_queue WHERE queue_fk=%s;'
                cursor.execute(sql2, (q_id,))
            connection.commit()
        finally:
            print("wiped queue")


    def wipe_invite_list(self, server_id):
        try:
            with connection.cursor() as cursor:
                sql = 'UPDATE server SET invite_list_json = %s WHERE server_discord_id = %s'
                cursor.execute(sql, ("[]", server_id))
            connection.commit()
        finally:
            print("wiped invite list")


    def wipe_accept_list(self, server_id):
        try:
            with connection.cursor() as cursor:
                sql = 'UPDATE server SET accept_list_json = %s WHERE server_discord_id = %s'
                cursor.execute(sql, ("[]", server_id))
            connection.commit()
        finally:
            print("wiped accept list")


    def wipe_last_invite_info(self, server_id):
        try:
            with connection.cursor() as cursor:
                sql = 'UPDATE server SET last_invite_info_json = %s WHERE server_discord_id = %s'
                cursor.execute(sql, ("[]", server_id))
            connection.commit()
        finally:
            print("wiped last invite info")


    def get_queue(self, server_id, afk_cleared=False):
        queue = []
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT queue_fk FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (int(server_id),))
                c = cursor.fetchone()
                if c:
                    q_id = c[0]
                else:
                    log.error("failed fetching the queue!")

                sql2 = 'SELECT member_fk, do_not_invite FROM member_queue LEFT JOIN member ON member_queue.member_fk = member.discord_id WHERE member_queue.queue_fk=%s ORDER BY join_date ASC;'
                cursor.execute(sql2, (q_id,))
                c = cursor.fetchall()
                for row in c:
                    if afk_cleared:
                        if row[1] == 0 or row[1] == "FALSE":
                            queue.append(str(row[0]))
                    else:
                        queue.append(str(row[0]))
        finally:
            pass
        return queue


    def get_queue_with_date(self, server_id):
        queue = []
        date = []
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT queue_fk FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))
                q_id = cursor.fetchone()

                sql2 = 'SELECT member_fk, join_date FROM member_queue WHERE queue_fk = %s ORDER BY join_date ASC;'
                cursor.execute(sql2, (q_id,))
                c = cursor.fetchall()

                for row in c:
                    queue.append(str(row[0]))
                    date.append(datetime.datetime.strptime(str(row[1]), "%Y-%m-%d %H:%M:%S"))
        finally:
            pass
        return queue, date


    def get_banlist(self, server_id):
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT ban_list_json FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))
                c = cursor.fetchone()
                if c[0]:
                    if isinstance(c[0], dict):
                        banlist = c[0]
                    else:
                        banlist = json.loads(c[0])
                else:
                    return []
        finally:
            pass
        return banlist


    def get_invite_list(self, server_id):
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT invite_list_json FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))
                c = cursor.fetchone()
                if c:
                    if isinstance(c[0], dict):
                        invites = c[0]
                    else:
                        invites = json.loads(c[0])
                else:
                    return []
        finally:
            pass
        return invites


    def get_accepted_list(self, server_id):
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT accept_list_json FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))
                c = cursor.fetchone()
                if c:
                    if isinstance(c[0], dict):
                        accepts = c[0]
                    else:
                        accepts = json.loads(c[0])
                else:
                    return []
        finally:
            pass
        return accepts


    def get_server_config(self, server_id):
        config = None
        i_server_id = int(server_id)
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT server_configuration_json FROM server WHERE server_discord_id = %s;'
                cursor.execute(sql, (i_server_id,))
                c = cursor.fetchone()
                if c:
                    if isinstance(c[0], dict):
                        config = c[0]
                    else:
                        config = json.loads(c[0])
        except MySQLError as e:
            print('MYSQL error: {!r}, errno is {}'.format(e, e.args[0]))
        return config


    def get_last_invite(self, server_id):
        msg = None
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT last_invite_info_json FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))
                c = cursor.fetchone()
                if c:
                    if isinstance(c[0], dict):
                        msg = c[0]
                    else:
                        if c[0] is not None:
                            msg = json.loads(c[0])
                        else:
                            msg = ""
        finally:
            pass
        return msg


    def add_sub_at(self, server_id, user_id, position):
        queue, date = get_queue_with_date(server_id)

        if user_id in queue:
            remove_sub_from_queue(server_id, user_id)

        if not position <= 0 and not position > len(queue):
            user_at_pos_date = date[int(position)]
            user_above_pos_date = date[int(position) - 1]
            delta = user_at_pos_date - user_above_pos_date
            half_delta = delta / 2
            new_user_date = user_at_pos_date - half_delta
        elif position == 0:
            user_at_pos_date = date[0]
            new_user_date = user_at_pos_date - datetime.timedelta(seconds=10)
        else:
            new_user_date = datetime.datetime.now()

        try:
            with connection.cursor() as cursor:
                sql = 'SELECT queue_fk FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))
                c = cursor.fetchone()
                q_id = c

                sql2 = 'INSERT IGNORE INTO member (discord_id) VALUES (%s);'
                cursor.execute(sql2, (user_id,))
                sql3 = 'INSERT INTO member_queue (queue_fk, member_fk, join_date) VALUES (%s, %s, %s);'
                cursor.execute(sql3, (q_id, user_id, new_user_date))

            connection.commit()
        finally:
            pass


    def set_steam_id(self, user_id, steam_id):
        try:
            with connection.cursor() as cursor:
                sql = 'INSERT IGNORE INTO member (discord_id) VALUES (%s);'
                cursor.execute(sql, (user_id,))
                sql2 = 'UPDATE member SET steam_id = %s, verified_steam = %s WHERE discord_id = %s;'
                cursor.execute(sql2, (steam_id, 0, user_id))
            connection.commit()
        finally:
            pass


    def get_steam_id(self, user_id):
        steam_id = None
        verified = False
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT steam_id, verified_steam FROM member WHERE discord_id=%s;'
                cursor.execute(sql, (user_id,))
                c = cursor.fetchone()
                if c:
                    steam_id = c[0]
                    if c[1] == '1' or c[1] == 1:
                        verified = True
                else:
                    print("user not found, creating new")
                    sql2 = 'INSERT IGNORE INTO member (discord_id) VALUES (%s);'
                    cursor.execute(sql2, (user_id,))
        finally:
            pass
        return steam_id, verified


    async def fetch_match_details(self, match_id):
        # return local match data if available
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT match_id, content_json FROM dota_matches WHERE match_id=%s;'
                cursor.execute(sql, (match_id,))
                c = cursor.fetchone()
                found_id = None
                found_data = None
                if c:
                    if c[0]:
                        found_id = c[0]
                        found_data = c[1]
                if found_data:
                    if isinstance(found_data, dict):
                        return found_data
                    else:
                        return json.loads(found_data)
        finally:
            pass

        try:
            r = requests.get('http://localhost:3005/matchdetails/' + str(match_id))
            match_details = r.json()
            add_match_data(match_id, match_details)
            return match_details
        except:
            print("Failed fetching match details for: " + str(match_id))
            return False


    def get_queue_with_steam_ids(self, server_id):
        queue = []
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT queue_fk FROM server WHERE server_discord_id=%s;'
                cursor.execute(sql, (server_id,))
                c = cursor.fetchone()
                q_id = None
                if c:
                    q_id = c[0]

                sql = 'SELECT discord_id, steam_id, join_date FROM member_queue LEFT JOIN member ON member_queue.member_fk = member.discord_id WHERE queue_fk=%s ORDER BY join_date ASC;'
                cursor.execute(sql, (q_id,))
                c2 = cursor.fetchall()
                for row in c2:
                    if str(row[1]):
                        queue.append([str(row[0]), str(row[1])])
                    else:
                        queue.append([str(row[0]), "None"])
        finally:
            pass
        return queue


    def add_match_data(self, match_id, j_match_data):
        try:
            with connection.cursor() as cursor:
                js_match_data = json.dumps(j_match_data)
                sql = 'INSERT IGNORE INTO dota_matches (match_id, content_json) VALUES (%s, %s);'
                cursor.execute(sql, (int(match_id), js_match_data))
            connection.commit()
        finally:
            print("added match data")


    async def verify_steam(self, user_id):
        steam_id, verif_status = get_steam_id(user_id)
        if steam_id:
            try:
                r = requests.post('http://localhost:3005/addfriend/', json={"steam_id": str(steam_id)})
                return True
            except:
                print("Failed sending verification request to steam bot: " + str(steam_id))
                return False
        else:
            return False


    def update_member_stats(self, server_id, member_id, j_stats):
        try:
            with self.connection.cursor() as cursor:
                sql = 'SELECT stats_json FROM member_stats WHERE member_fk=%s AND server_fk=%s;'
                cursor.execute(sql, (member_id, server_id))
                c = cursor.fetchone()
                found_data = None
                if c:
                    found_data = c[0]
                if found_data:
                    js_stats = json.dumps(j_stats)
                    sql2 = 'UPDATE member_stats SET stats_json = %s WHERE server_fk= %s AND member_fk = %s;'
                    cursor.execute(sql2, (js_stats, server_id, member_id))
                else:
                    js_stats = json.dumps(j_stats)
                    sql3 = 'INSERT INTO member_stats (member_fk, server_fk, stats_json) VALUES (%s, %s, %s);'
                    cursor.execute(sql3, (member_id, server_id, js_stats))
            self.connection.commit()
        finally:
            pass


    def get_member_stats(self, server_id, member_id):
        found_data = self.get_member_stats_template()
        try:
            with self.connection.cursor() as cursor:
                sql = 'SELECT stats_json FROM member_stats WHERE member_fk=%s AND server_fk=%s;'
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

    def get_all_message_logs(self, server_id):
        class MessageLogMember:
            def __init__(self, discord_id, message_log):
                self.discord_id = discord_id
                self.message_log = message_log

        try:
            with self.connection.cursor() as cursor:
                sql = 'SELECT member_fk, stats_json FROM member_stats WHERE server_fk=%s;'
                cursor.execute(sql, (server_id,))
                c = cursor.fetchall()
        finally:
            processed_data = []
            if c:
                for m in c:
                    if isinstance(m[1], dict):
                        processed_data.append(MessageLogMember(m[0], m[1]))
                    else:
                        processed_data.append(MessageLogMember(m[0], json.loads(m[1])))
            return processed_data

    def get_days_since_last_game(self, server_id, member_id):
        stats = get_member_stats(server_id, member_id)
        period = "none"
        for i in reversed(stats["log"]):
            if i[1].startswith("participated in a subgame") and "public pw" in i[1]:
                last_game = datetime.datetime.strptime(str(i[0]), "%Y-%m-%d %H:%M:%S")
                period = (datetime.datetime.now() - last_game).days
                break
        return period


    def get_afk_flag(self, server_id, member_id):
        result = False
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT do_not_invite FROM member WHERE discord_id=%s;'
                cursor.execute(sql, (member_id,))
                c = cursor.fetchone()
                result = False
                if c:
                    if c[0] == "TRUE" or c[0] == 1:
                        result = True
        finally:
            pass
        return result


    def get_all_registered_subs(self):
        subs = []
        try:
            with connection.cursor() as cursor:
                sql = 'SELECT discord_id, steam_id FROM member;'
                cursor.execute(sql)
                c = cursor.fetchall()
                for row in c:
                    if row[1]:
                        subs.append([row[0], row[1]])
        finally:
            pass
        return subs


    # ---------- Giveaway --------------
    giveaway_path = 'data/giveaway/giveaway.json'


    def get_sub_in_giveaway(self, user_id):
        list = []
        try:
            with open(giveaway_path) as data_file:
                lines = data_file.readlines()
                for l in lines:
                    list.append(l)
        except FileNotFoundError:
            print("File not found...")
        if user_id+"\n" in list:
            return True
        else:
            return False


    def wipe_giveaway(self):
        if os.path.exists(giveaway_path):
            os.rename(giveaway_path, 'data/giveaway/giveaway_' + str(datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S')) + '.json')
        open(giveaway_path, 'w+').close()


    def append_sub_to_giveaway(self, user_id, tickets):
        with open(giveaway_path, "a") as myfile:
            myfile.write(user_id + "\n")


    def get_random_sub_from_giveaway(self):
        list = []
        try:
            with open(giveaway_path) as data_file:
                lines = data_file.readlines()
                for l in lines:
                    l = l.replace("\n", "")
                    if l:
                        list.append(l)
        except FileNotFoundError:
            print("File not found...")
        if list:
            winner = random.choice(list)
            return winner
        else:
            return None
