import mysql.connector
import pandas as pd
import datetime
import time
from steam import Steam
import schedule
import json
import requests
from sql_grabbers import sql_info_grabber

cnx = mysql.connector.connect(user='root', password='',
                                 host='localhost', database='steam')
cursor = cnx.cursor()


def collect_count():
    ids = sql_info_grabber(cnx, cursor)
    id_list = ids.get_sql_ids()
    for id in id_list:
        player_details = requests.get("https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?format=json&appid="+str(id)).json()
        player_count = player_details['response']['player_count']
        print(player_details['response']['player_count'])
        print(id)
        player_count_insert(id, player_count)
    print('Done')
    print('Next collection:' + str(datetime.datetime.now() + datetime.timedelta(hours=1)))


def player_count_insert(id, player_count):

    add_count = "INSERT INTO current_hourly VALUES(%(time_stamp)s, %(current_playercount)s, %(app_id)s)"
    count_data = {
        'time_stamp': datetime.datetime.now(),
        'current_playercount': player_count,
        'app_id': id
    }
    cursor.execute(add_count, count_data)
    cnx.commit()


def daily_count():
    ids = sql_info_grabber(cnx, cursor)
    id_list = ids.get_sql_ids()
    for id in id_list:
        get_sum = f"SELECT AVG(current_playercount) as avgcount, MAX(current_playercount) as maxcount FROM current_hourly " \
                  f"WHERE app_id = {id} and DATE(time_stamp) = (SELECT date_sub(curdate(), INTERVAL 1 DAY))"
        cursor.execute(get_sum)
        for avgcount, maxcount in cursor:
            average = avgcount
            max = maxcount
            insert_new_count(average, max, id, 'daily')
    print('Daily Done')

def weekly_count():
    ids = sql_info_grabber(cnx, cursor)
    id_list = ids.get_sql_ids()
    for id in id_list:
        get_sum = f"SELECT AVG(current_playercount) as avgcount, MAX(current_playercount) as maxcount FROM current_hourly " \
                  f"WHERE app_id = {id} and " \
                  f"DATE(time_stamp) between " \
                  f"(SELECT date_sub(curdate(), INTERVAL 1 WEEK)) and (SELECT date_add(curdate(), INTERVAL(1-DAYOFWEEK(curdate())) DAY))"
        cursor.execute(get_sum)
        for avgcount, maxcount in cursor:
            average = avgcount
            max = maxcount
            insert_new_count(average, max, id, 'weekly')
    print('Weekly Done')

def insert_new_count(average, max, id, format):
    if format == 'daily':
        add_count = "INSERT INTO current_daily VALUES(%(day)s, %(average_daily)s, %(max_daily)s, %(app_id)s)"
        date = datetime.date.today()- datetime.timedelta(1)
    elif format == 'weekly':
        add_count = "INSERT INTO current_weekly VALUES(%(day)s, %(average_weekly)s, %(max_weekly)s, %(app_id)s)"
        date = datetime.date.today()- datetime.timedelta(7)

    data = {
        'day': date,
        f'average_{format}': average,
        f'max_{format}': max,
        'app_id': id
    }
    cursor.execute(add_count, data)
    cnx.commit()



schedule.every().hour.at(":00").do(collect_count)
schedule.every().day.at("00:00").do(daily_count)
schedule.every().sunday.at("00:01").do(weekly_count)

while True:
    schedule.run_pending()
    time.sleep(1)
