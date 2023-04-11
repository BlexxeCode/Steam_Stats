import pymysql
from app import app
from config import mysql
from flask import  jsonify
from flask import flash, request
from sql_grabbers import sql_info_grabber

@app.route('/names')
def get_names():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT game_name FROM game_list')
        names = cursor.fetchall()
        reponse = jsonify(names)
        reponse.status_code = 200
        return reponse
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

@app.route('/summary/<game_name>')
def get_summary(game_name):
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = f"""SELECT game_list.* , price_count.current_price, price_count.day from game_list 
        JOIN price_count ON game_list.steam_id = price_count.app_id WHERE game_list.game_name = '{game_name}' 
        ORDER BY price_count.day DESC LIMIT 1;"""
        cursor.execute(query)
        summary = cursor.fetchall()
        response = jsonify(summary)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/playercount')
def get_player_count_all():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        player = 'SELECT current_hourly.time_stamp, current_hourly.current_playercount, game_list.game_name \
                    From current_hourly JOIN game_list ON current_hourly.app_id = game_list.steam_id'

        cursor.execute(player)
        playerdf = cursor.fetchall()
        reponse = jsonify(playerdf)
        reponse.status_code = 200
        return reponse
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/playercount/<game_name>')
def get_player_count_game(game_name):
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        player_game = f"""SELECT current_hourly.time_stamp, current_hourly.current_playercount, game_list.game_name 
                    From current_hourly JOIN game_list ON current_hourly.app_id = game_list.steam_id
                    WHERE game_list.game_name = '{game_name}'"""
        cursor.execute(player_game)
        playerdf_game = cursor.fetchall()
        reponse = jsonify(playerdf_game)
        reponse.status_code = 200
        return reponse
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

@app.route('/price')
def get_price_all():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = 'SELECT price_count.day, game_list.initial_price, price_count.current_price, price_count.percent_discount, game_list.game_name \
            FROM price_count JOIN game_list ON price_count.app_id = game_list.steam_id \
            WHERE DATE(day) BETWEEN (SELECT date_sub(curdate(), INTERVAL 1 YEAR)) and (SELECT curdate())'

        cursor.execute(query)
        price = cursor.fetchall()
        response = jsonify(price)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


@app.route('/price/<game_name>')
def get_price_game(game_name):
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = f"""SELECT price_count.day, game_list.initial_price, price_count.current_price, price_count.percent_discount, game_list.game_name 
            FROM price_count JOIN game_list ON price_count.app_id = game_list.steam_id 
            WHERE DATE(day) BETWEEN (SELECT date_sub(curdate(), INTERVAL 1 YEAR)) and (SELECT curdate()) and game_list.game_name = '{game_name}'"""

        cursor.execute(query)
        price = cursor.fetchall()
        response = jsonify(price)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

@app.route('/playlength')
def get_hours_all():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = 'SELECT play_count.day, play_count.hours_played, game_list.game_name FROM play_count JOIN game_list ON play_count.app_id = game_list.steam_id'
        cursor.execute(query)
        playcount = cursor.fetchall()
        response = jsonify(playcount)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)

    finally:
        cursor.close()
        conn.close()

@app.route('/playlength/<game_name>')
def get_hours_game(game_name):
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = f"""SELECT play_count.day, play_count.hours_played, game_list.game_name FROM play_count 
        JOIN game_list ON play_count.app_id = game_list.steam_id WHERE game_list.game_name = '{game_name}'"""
        cursor.execute(query)
        playcount = cursor.fetchall()
        response = jsonify(playcount)
        response.status_code = 200

        return response
    except Exception as e:
        print(e)

    finally:
        cursor.close()
        conn.close()

@app.errorhandler(404)
def if_error(error=None):
    message = {'message': request.url + ' Not Found'}
    response = jsonify(message)
    response.status_code = 404
    return response

if __name__ == '__main__':
    app.run(port=8040, host='192.168.1.246')
