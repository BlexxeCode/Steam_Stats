import mysql.connector
import pandas as pd
from datetime import date
import time
from steam import Steam
import json
import requests
from sql_grabbers import sql_info_grabber

key = 'C63D2BA4A6622E4B01587B43DEC2F55E'




def get_steam_info():
    cnx = mysql.connector.connect(user='root', password='password@12',
                                  host='localhost', database='steam')
    cursor = cnx.cursor()

    steam = Steam(key)
    user = steam.users.get_owned_games("76561198253206281")

    ids = sql_info_grabber(cnx, cursor)
    current_ids = ids.get_sql_ids()

    ids = []
    for id in user['games']:
        print('-' * 20)
        if id['appid'] not in current_ids:
            ids.append(id['appid'])
            print(id['appid'])
            print(id['name'])
            print(id['playtime_forever'])
            print('-' * 20)

            #insert_steam_info(cnx, cursor, ids)

def insert_steam_info(cnx, cursor, ids):
    cnx = cnx
    cursor = cursor
    add_game = "INSERT INTO game_list(steam_id, game_name, developer, publisher, initial_price)" \
               "VALUES(%(steam_id)s, %(game_name)s, %(developer)s, %(publisher)s, %(initial_price)s)"

    for id_num in ids:
        id_num = str(id_num)
        app_details = requests.get('https://steamspy.com/api.php?request=appdetails&appid=' + id_num).json()
        if app_details['publisher'] != "":
            app_id = int(app_details['appid'])
            name = app_details['name']
            developers = app_details['developer']
            publsihers = app_details['publisher']
            initial_price = float(app_details['initialprice']) * .01
            initial_price = round(initial_price, 2)

        app_data = {
            "steam_id": app_id,
            'game_name': name,
            'developer': developers,
            'publisher': publsihers,
            'initial_price': initial_price

        }
        cursor.execute(add_game, app_data)
        cnx.commit()

        print('Name:', name)
        print('steam_id:', app_id)
        print('developer:', developers)
        print('publisher:', publsihers)
        print('initial_price:', initial_price)
        print('-' * 20)





get_steam_info()