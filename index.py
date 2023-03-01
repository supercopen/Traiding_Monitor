import os, environ
import websocket
import json
import pandas as pd
from plotly.graph_objs import Scatter, Layout, Figure
import plotly.offline as pyo
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()

env = environ.Env(
    # set casting, default value
    API_KEY=(str, ""),
    API_SECRET=(str, ""),
    F_NAME = (str, "")
)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
API_KEY = env("API_KEY")
API_SECRET = env("API_SECRET")
F_NAME = env("F_NAME")

# Create a websocket connection
WS_URL = "wss://stream.binance.com:9443/ws"
HEADERS = {"X-MBX-APIKEY": API_KEY}
SUBSCRIPTION_PARAMS = ["btcusdt@kline_1m"]

def on_open(ws):
    # Subscribe to channel
    subscription_data = {
        "method": "SUBSCRIBE",
        "params": SUBSCRIPTION_PARAMS,
        "id": 1
    }
    ws.send(json.dumps(subscription_data))

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws):
    print("Closed")

# Lists to store received data
times = [] 
opens = []
highs = []
lows = []
closes = []
volumes = []

def on_message(ws, message):
    # Get the received data
    data = json.loads(message)

    # Store the data in lists
    times.append(data['k']['t'])
    opens.append(float(data['k']['o']))
    highs.append(float(data['k']['h']))
    lows.append(float(data['k']['l']))
    closes.append(float(data['k']['c']))
    volumes.append(float(data['k']['v']))
    
    # Create a DataFrame
    df = pd.DataFrame({'Time': times, 'Close': closes, 'High': highs, 'Low': lows, 'Open': opens, 'Volume': volumes})
    
    # Compute the Simple Moving Average (SMA)
    df["SMA"] = df["Close"].rolling(window=20).mean()
    
    # Create traces for the plot
    close_trace = Scatter(x=df["Time"], y=df["Close"], name="Close")
    sma_trace = Scatter(x=df["Time"], y=df["SMA"], name="SMA")
    # Create a layout object
    layout = Layout(title = 'BTCUSDT Candles',
                    xaxis= dict(
                        rangeselector=dict(
                            buttons=list([
                                dict(count=1,
                                     label='1m',
                                     step='month',
                                     stepmode='backward'),
                                dict(count=6,
                                     label='6m',
                                     step='month',
                                     stepmode='backward'),
                                dict(count=1,
                                    label='YTD',
                                    step='year',
                                    stepmode='todate'),
                                dict(count=1,
                                    label='1y',
                                    step='year',
                                    stepmode='backward'),
                                dict(step='all')
                            ])
                        ),
                        rangeslider=dict(
                            visible = True
                        ),
                        type='date'
                    )
                   )
    
    # Plot Plotly Figure
    data = [close_trace, sma_trace]
    fig = Figure(data=data, layout=layout)
    pyo.plot(fig, filename=F_NAME, auto_open=False)
    
ws = websocket.WebSocketApp(WS_URL,header = HEADERS,
                            on_open = on_open,on_message = on_message,
                            on_error = on_error,on_close = on_close,
                            keep_running = True)
# Run the websocket
ws.run_forever()