import mysql.connector
import pandas as pd
import datetime
import time
from steam import Steam
import schedule
import json
import requests
from sql_grabbers import sql_info_grabber




def price_count():
    cnx = mysql.connector.connect(user='root', password='',
                                  host='localhost', database='steam')
    cursor = cnx.cursor()

    ids = sql_info_grabber(cnx, cursor)
    app_list = ids.get_sql_ids()

    for id in app_list:
        app_details = requests.get(f'https://steamspy.com/api.php?request=appdetails&appid={id}').json()
        current = round(float(app_details['price'])*.01,2)
        initial_query = f'SELECT initial_price FROM game_list WHERE steam_id = {id}'
        cursor.execute(initial_query)
        for initial_price in cursor:
            initial = float(initial_price[0])
            initial = round(initial,2)
        if initial != 0:
            percent_change = (abs(initial - current)/initial) *100
            price_query = "INSERT INTO price_count VALUES(%(day)s,%(current_price)s,%(percent_discount)s,%(app_id)s)"
            data = {
                'day':datetime.date.today(),
                'current_price':current,
                'percent_discount':percent_change,
                'app_id': id
            }
            cursor.execute(price_query,data)
            cnx.commit()
        print('-')
    print('Done')





schedule.every().day.at("00:00").do(price_count)

while True:
    schedule.run_pending()
    time.sleep(1)
