from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import mysql.connector
import pandas as pd
import datetime
from sql_grabbers import sql_info_grabber


app = Dash(external_stylesheets=[dbc.themes.DARKLY])
load_figure_template('DARKLY')

def sql_connect():
    cnx = mysql.connector.connect(user='root', password='password@12',
                                  host='localhost', database='steam')
    cursor = cnx.cursor()
    return cnx, cursor

def get_names():
    cnx, cursor = sql_connect()
    query = sql_info_grabber(cnx,cursor)
    names = query.get_sql_names()
    names.append('All')

    return names

app.layout = html.Div([
    html.H1('Steam Game Playercount'),
    dcc.Dropdown(id='dropdown', options=[
        {'label':i, 'value':i} for i in get_names()
            ], style={'color':'Black'},

        value='All',
        placeholder='Select a game',
        searchable=True),


    html.Div(className='mainsets',children=[
        html.P('Time Period'),
        dcc.RadioItems(id = 'time_period', options=[
                {'label':'Day', 'value':1},
                {'label':'Week','value':7},
                {'label':'Month','value':30},
                {'label':'Year','value':365},
                {'label':'All Time','value':'All'}
        ],
            value='All'
        ),
        html.Div(children=[
            html.Div(dcc.Graph(id='player_count')),
            html.Div(className='statdiv',children=[
                html.H3('Player Count Stats'),
                html.Span(className='infospan',children=[
                    html.Strong(id='current', className='pcstat'),
                    html.Br(),
                    html.Strong(id='24_hours', className='pcstat'),
                    html.Br(),
                    html.Strong(id='all_time', className='pcstat')
                ], style={'width':'50%'}),
                html.Br(),
                html.Span(className='infospan',children=[
                    html.Strong(id='average', className='pcstat')
                ],style={"width":"50%"})

            ], style={'display':'flex', 'flex':1})
        ])
    ]),
    html.Div(className='mainsets',children=[
        html.Div([dcc.Graph(id='price_count')], style={'width':'70%'}),
        html.Div(className='statmisc',children=[
            html.Div([
                dcc.Markdown(
                    """
                    ** Initial Price(In USD) **
                    """
                ),
                html.P(id='initial_price'),]
            ),
            html.Div([
                dcc.Markdown(
                    """
                    ** Current Price(IN USD) **
                    """
                ),
                html.P(id='current_price')
            ]),
             html.Div([
                dcc.Markdown(
                    """
                    ** Percent Discount **
                    """
                ),
                html.P(id='discount')
             ]),
            ], style={'width':'30%'}
        ),
    ],style={'flex':1, 'display':'flex'}),
    html.Div(className='mainsets',children=[
        html.Div([dcc.Graph(id='play_graph')],style= {'width':'70%'}),
        html.Div(className='statmisc',children=[
            html.Div([
                dcc.Markdown(
                    """
                    ** Average Playtime Per Session **
                    """
                ),
                html.P(id='avg_play')
            ]),
            html.Div([
                dcc.Markdown(
                    """
                    ** Total Hours Played **
                    """
                ),
               html.P(id='total_played')
            ]),
        ], style={'width':'30%'})
    ], style={'display':'flex'}),

    dcc.Interval(
        id='intervals',
        interval=1 * 3600000,
        n_intervals= 0
    )],
)

@app.callback(Output(component_id='player_count', component_property='figure'),
              [Input(component_id='dropdown', component_property='value'),
               Input(component_id='intervals', component_property='n_intervals'),
               Input(component_id='time_period', component_property='value')])

def get_player_count(game, n, period):
    cnx = mysql.connector.connect(user='root', password='password@12',
                                  host='localhost', database='steam')

    player = 'SELECT current_hourly.time_stamp, current_hourly.current_playercount, game_list.game_name \
                From current_hourly JOIN game_list ON current_hourly.app_id = game_list.steam_id'

    playerdf = pd.read_sql(player, cnx)

    if period == 'All':
        period_played = playerdf
    else:
        period = ((playerdf['time_stamp'] > datetime.datetime.now()- datetime.timedelta(period)) &
                  ((playerdf)['time_stamp'] < datetime.datetime.now()))
        period_played = playerdf[period]

    if game == 'All':
        fig = px.line(period_played, x='time_stamp', y='current_playercount',
                      color='game_name', markers=True, title='Playercount Over Time')
        return fig
    else:
        playerdf_game = period_played.loc[playerdf['game_name'] == game]
        fig = px.line(playerdf_game, x='time_stamp', y='current_playercount',
                      color='game_name', markers=True, title=f'Playercount Over Time of {game}')
        return fig

@app.callback(Output(component_id='current', component_property='children'),
              Input(component_id='dropdown', component_property='value'))
def get_current_players(game):
    cnx, cursor = sql_connect()
    if game == 'All':
        query = 'SELECT SUM(current_playercount) as current FROM current_hourly ' \
                'group by day(time_stamp), hour(time_stamp) ' \
                'ORDER BY day(time_stamp) DESC, hour(time_stamp) DESC LIMIT 1'
        cursor.execute(query)
        for current in cursor:
            sum = current[0]
        return f"Current players of all games in library: {sum}"
    else:
        query = f"""SELECT current_playercount as current FROM current_hourly WHERE app_id =
                (SELECT steam_id FROM game_list WHERE game_name = "{game}") ORDER BY time_stamp DESC LIMIT 1"""
        cursor.execute(query)
        for current in cursor:
            cur = current[0]
        return f"Current player count of {game}: {cur}"

@app.callback(Output(component_id='24_hours', component_property='children'),
              Input(component_id='dropdown', component_property='value'))
def get_24_max(game):
    cnx, cursor = sql_connect()
    if game == 'All':
        query = "SELECT MAX(current) as max_cur FROM " \
                "(SELECT time_stamp, SUM(current_playercount) as current FROM current_hourly as ch " \
                "group by day(time_stamp), hour(time_stamp) ORDER BY day(time_stamp) DESC, hour(time_stamp) DESC) as sub " \
                "GROUP BY day(time_stamp) LIMIT 1"
        cursor.execute(query)
        for max_cur in cursor:
            max_current = max_cur[0]
        return f'Max concurrent player recorded today: {max_current}'
    else:
        query = f"""SELECT max_daily FROM current_daily WHERE app_id = 
                (SELECT steam_id from game_list WHERE game_name = "{game}") LIMIT 1"""
        cursor.execute(query)
        for max_daily in cursor:
            daily = max_daily[0]
        return f"Max players in {game} in the last day: {daily}"

@app.callback(Output(component_id='all_time', component_property='children'),
              Input(component_id='dropdown', component_property='value'))
def get_all_time_max(game):
    cnx, cursor = sql_connect()
    if game == 'All':
        query = 'SELECT MAX(current) FROM (SELECT time_stamp, SUM(current_playercount) as current FROM current_hourly as ch ' \
                'GROUP BY day(time_stamp), hour(time_stamp) ORDER BY day(time_stamp) DESC, hour(time_stamp) DESC) as sub'
        cursor.execute(query)
        for all_max in cursor:
            all_time_curr = all_max[0]
        return f'All time Max recorded: {all_time_curr}'
    else:
        query = f"""SELECT MAX(max_daily) FROM current_daily WHERE app_id =
                (SELECT steam_id from game_list WHERE game_name = "{game}")"""
        cursor.execute(query)
        for all_max in cursor:
            all_time_curr = all_max[0]
        return f"All time max player count of {game}: {all_time_curr}"

@app.callback(Output(component_id='average', component_property='children'),
              Input(component_id='dropdown', component_property='value'))
def get_avg_players(game):
    cnx, cursor = sql_connect()
    if game == 'All':
        query = 'SELECT AVG(current) FROM (SELECT time_stamp, SUM(current_playercount) as current FROM current_hourly as ch ' \
                'GROUP BY day(time_stamp), hour(time_stamp) ORDER BY day(time_stamp) DESC, hour(time_stamp) DESC) as sub;'
        cursor.execute(query)
        for all_avg in cursor:
            all_time_avg = all_avg[0]
        return f'All time average recorded for all games: {all_time_avg}'
    else:
        query = f"""SELECT AVG(current_playercount) FROM current_hourly WHERE app_id =
                (SELECT steam_id from game_list WHERE game_name = "{game}")"""
        cursor.execute(query)
        for all_avg in cursor:
            all_time_avg = all_avg[0]
        return f"All time average player count of {game}: {all_time_avg}"

@app.callback(Output(component_id='price_count', component_property='figure'),
              Input(component_id='dropdown', component_property='value'))

def get_price(game):
    cnx = mysql.connector.connect(user='root', password='password@12',
                                  host='localhost', database='steam')

    price = 'SELECT price_count.day, game_list.initial_price, price_count.current_price, price_count.percent_discount, game_list.game_name \
            FROM price_count JOIN game_list ON price_count.app_id = game_list.steam_id \
            WHERE DATE(day) BETWEEN (SELECT date_sub(curdate(), INTERVAL 1 YEAR)) and (SELECT curdate())'

    pricedf = pd.read_sql(price, cnx)

    if game == 'All':
        fig = px.line(pricedf, x='day', y='current_price',color='game_name',markers=True,
                      title='Yearly pricing of all games')
        return fig
    else:
        pricedf_game = pricedf.loc[pricedf['game_name'] == game]
        fig = px.line(pricedf_game, x='day', y='current_price', markers=True,
                      title=f'Yearly pricing of {game}')
        return fig

@app.callback(Output(component_id='initial_price', component_property='children'),
              Input(component_id='dropdown', component_property='value'))
def get_initial_price(game):
    cnx, cursor = sql_connect()
    i_price = None

    if game == 'All':
        return 'Select a Game'
    else:
        initial = f"""SELECT initial_price FROM game_list WHERE game_name = "{game}" """
        cursor.execute(initial)
        for initial_price in cursor:
            i_price = initial_price[0]
        return f'Initial Price:${i_price}'

@app.callback(Output(component_id='current_price', component_property='children'),
              Input(component_id='dropdown', component_property='value'))
def get_current_price(game):
    cnx, cursor = sql_connect()

    c_price = None

    if game == 'All':
        return 'Select a Game'
    else:
        current = f"""SELECT current_price FROM price_count WHERE app_id = 
        (SELECT steam_id from game_list WHERE game_name = "{game}")"""
        cursor.execute(current)
        for current_price in cursor:
            c_price = current_price[0]
        return f'Current Price:${c_price}'

@app.callback(Output(component_id='discount', component_property='children'),
              Input(component_id='dropdown', component_property='value'))
def get_discount(game):
    cnx, cursor = sql_connect()

    dis = None
    if game == 'All':
        return 'Select a Game'
    else:
        discount = f"""SELECT percent_discount FROM price_count WHERE app_id = 
                   (SELECT steam_id from game_list WHERE game_name = "{game}")"""
        cursor.execute(discount)
        for discount_percent in cursor:
            dis = discount_percent[0]
        return f'Percent Discount:{dis}%'

@app.callback(Output(component_id='play_graph', component_property='figure'),
              Input(component_id='dropdown', component_property='value'))
def get_hours(game):
    cnx = mysql.connector.connect(user='root', password='password@12',
                                  host='localhost', database='steam')

    query = 'SELECT play_count.day, play_count.hours_played, game_list.game_name FROM play_count JOIN game_list ON play_count.app_id = game_list.steam_id'
    game_hours = pd.read_sql(query, cnx)
    if game == 'All':
        fig =px.line(game_hours, x='day', y='hours_played', color='game_name',markers=True,
                title='Daily Hours played of All Games (Since Recording)')
        return fig
    else:
        spec_game_hours = game_hours.loc[game_hours['game_name'] == game]
        fig= px.line(spec_game_hours, x='day', y='hours_played', markers=True,
                title= f'Daily Hours played of {game} (Since Recording)')
        return fig

@app.callback(Output(component_id='avg_play', component_property='children'),
              Input(component_id='dropdown', component_property='value'))
def get_avg_hours(game):
    cnx, cursor = sql_connect()

    average = None

    if game == 'All':
        return 'Select a Game'
    else:
        query = f"""SELECT AVG(hours_played) AS session FROM play_count WHERE app_id = 
                (SELECT steam_id from game_list WHERE game_name = "{game}")"""
        cursor.execute(query)
        for session in cursor:
            average = session[0]
            if average == None:
                return 'Hours played have not been recorded'
        return f'Average: {average} hours'

@app.callback(Output(component_id='total_played', component_property='children'),
              Input(component_id='dropdown', component_property='value'))
def get_total_hours(game):
    cnx, cursor = sql_connect()
    total = None
    if game == 'All':
        return 'Select a Game'
    else:
        query = f"""(SELECT hours_played from game_list WHERE game_name = "{game}")"""
        cursor.execute(query)
        for new_total_hours in cursor:
            total = new_total_hours[0]
        return f'Total Hours Played: {total} hours'

if __name__ == '__main__':
    app.run_server(debug=True, port=8050, host='192.168.1.246')