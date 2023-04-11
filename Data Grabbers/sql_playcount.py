import mysql.connector
import pandas as pd
import datetime
import time
from steam import Steam
import schedule
import json
import requests
from decimal import Decimal
from sql_grabbers import sql_info_grabber


cnx1 = mysql.connector.connect(user='root', password='password@12',
                                 host='localhost', database='steam')
cursor1 = cnx1.cursor()
app_list = []
app_id = "SELECT steam_id from game_list";

cursor1.execute(app_id)
for steam_id in cursor1:
    app_list.append(steam_id[0])

key = 'C63D2BA4A6622E4B01587B43DEC2F55E'
steam = Steam(key)

def insert_hours(steam_id=app_list):
    cnx = mysql.connector.connect(user='root', password='password@12',
                                  host='localhost', database='steam')
    cursor = cnx.cursor()
    user = steam.users.get_owned_games('76561198253206281')
    for id in user['games']:
        for app in steam_id:
            #print(id['appid'])
            #print(app)
            if id['appid'] == app:
                daily_hours_played(app, id, cnx, cursor)
                update = F"UPDATE game_list SET hours_played = {id['playtime_forever']/60} WHERE steam_id = {app}"
                cursor.execute(update)
                cnx.commit()
    print('done')

def daily_hours_played(app_id, id, cnx, cursor):
    hours = f'SELECT hours_played FROM game_list WHERE steam_id ={app_id}'
    cursor.execute(hours)
    for hours_played in cursor:
        hour = hours_played[0]
    time_played = id['playtime_forever']/60 - float(hour)
    if time_played >= 0.1:
        insert = "INSERT INTO play_count VALUES(%(day)s,%(old_total_hours)s,%(new_total_hours)s,%(hours_played)s,%(app_id)s)"
        data = {
            'day': datetime.date.today() - datetime.timedelta(1),
            'old_total_hours': hour,
            'new_total_hours': id['playtime_forever'] / 60,
            'hours_played': abs(time_played),
            'app_id': app_id
        }
        cursor.execute(insert,data)
        cnx.commit()
        print(abs(time_played))


schedule.every().day.at("00:00").do(insert_hours)

while True:
    schedule.run_pending()
    time.sleep(1)