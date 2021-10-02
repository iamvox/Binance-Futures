import json
import os
import dash_html_components as html
import random
import dash_core_components as dcc
import plotly.graph_objects as go
from gevent import sleep
from dash import Dash
from dash.dependencies import Input, Output, State
from dash_extensions import WebSocket
from dash_extensions.websockets import SocketPool, run_server
import logging

import threading
import queue

logging.basicConfig(level=logging.DEBUG,
                    filename=os.path.basename(__file__) + '.log',
                    format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                    style="{")


def genData(q):
    while True:
        q.put(random.uniform(0, 1))  # the data value


# This block runs asynchronously.
def ws_handler(ws, q):
    # for data in data_feed():
    #     ws.send(json.dumps(data))  # send data
    while len(list(q.queue)) != 0:
        data = q.get()
        sleep(random.uniform(0, 2))  # delay between data events
        ws.send(json.dumps(data))
        q.task_done()


q = queue.Queue()

# Create example app.
app = Dash(prevent_initial_callbacks=True)
socket_pool = SocketPool(app, handler=lambda x: ws_handler(x, q))
app.layout = html.Div([
    dcc.Graph(id="graph", figure=go.Figure(go.Scatter(x=[], y=[]))),
    WebSocket(id="ws")
])


@app.callback(Output("graph", "figure"), [Input("ws", "message")], [State("graph", "figure")])
def update_graph(msg, figure):
    x, y = figure['data'][0]['x'], figure['data'][0]['y']
    return go.Figure(data=go.Scatter(x=x + [len(x)], y=y + [float(msg['data'])]))


if __name__ == '__main__':
    threading.Thread(target=genData, daemon=True, args=(q,)).start()
    run_server(app, port=5000)  # 5000 if the default port
