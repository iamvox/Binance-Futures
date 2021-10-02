from datetime import datetime
from numpy import dtype
from numpy.lib.shape_base import column_stack
from pandas.core.frame import DataFrame
from pandas.io.parsers import read_csv
from pandas.io.pytables import IndexCol
import websocket
import json
import time
import pandas as pd
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
from configparser import ConfigParser
import logging
import dash_bootstrap_components as dbc
import threading
import plotly.graph_objects as go
import numpy as np

file = 'config.ini'
config = ConfigParser()
config.read(file)


logging.basicConfig(level=logging.DEBUG,
                    filename=os.path.basename(__file__) + '.log',
                    format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                    style="{")

socket = config.get('websocket', 'websocket_base_url')


global market_data
market_data = pd.read_csv('df.csv', index_col='s')

global market_data_hist
market_data_hist = {}


def on_open(ws):
    print("Websocket connection opened")
    stream_data = config.get('websocket', 'all_market_subscription')
    ws.send(stream_data)

#open websocker function


def on_message(ws, message):
    df = pd.read_json(message)
    df.set_index(df['s'], inplace=True)
    market_data.update(df)
    print(market_data.head(5))
    # print(df.info(verbose=3))
    # print(pd.to_datetime(market_data['E'], unit='ms'))


def on_close(ws):
    print("Websocket connection closed")


ws = websocket.WebSocketApp(
    socket, on_message=on_message, on_open=on_open, on_close=on_close)


app = dash.Dash()


app.layout = html.Div(children=[
    dcc.Dropdown(id="sort-by-dropdown", options=[
        {'label': 'volume', 'value': 'q'},
        {'label': 'change %', 'value': 'P'}
    ], value='P'),

    dcc.Graph(id="bar-graph", figure=px.bar(market_data,
              y=market_data['P'], title="Binance-Futures chart", color=market_data.index)),
    # dcc.Graph(id="line-graph", animate=True, figure=px.line(market_data,
    # y=market_data['P'], title="Line Graph", color=market_data.index)),
    # dcc.Graph(id="pchange-bar-btc", figure=px.bar(market_data,
    # x=datetime.now(), y=market_data['P']['BTCUSDT'])),
    dcc.Interval(id="interval", interval=1000, n_intervals=0)
])


@   app.callback(Output("bar-graph", "figure"),
                 Output("pchange-bar-btc", "figure"),
                 [Input('interval', 'n_intervals')],
                 [Input('sort-by-dropdown', 'value')],)
def update_graph(n_intervals, value):
    global market_data
    market_data = market_data.sort_values(by=value, ascending=False)
    return px.bar(market_data, y=market_data['P'], color=market_data.index)
# ,px.line(y=market_data['P'], title="Line Graph", x=datetime.now(), color=market_data.index)


if __name__ == '__main__':
    threading.Thread(target=ws.run_forever, daemon=True).start()
    app.run_server(port=5000)
