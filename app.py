# ============================================================
# Mini Finance Dashboard — Crypto vs. Traditional Equity
# Team: Group 3
# Members: Chase LaRose, Gavin Zborowski, Evie Trinh, Alex Bailey
#
# Question / Story:
#   The purpose of this dashboard is to visualize Bitcoin, Apple, and
#   the S&P500 price price changes over the past 12 months. Apple’s prices 
#   are much more stable compared to Bitcoin’s prices which are more 
#   volatile. 
#
# Data Choices:
#   BTC-USD (Bitcoin) and AAPL (Apple Inc.) over the past 1 year,
#   pulled live via yfinance. SPY (S&P 500 ETF) is included as an
#   another third series so the viewer can see how the broader
#   market compares as well.
#
# Interactivity:
#   - A date-range slider lets the viewer zoom into a specific window
#     and compare how each asset reacted. (Initial anticipated callback)
#   
#   We prompted Claude to implement these after the intial run for a 
#   more polished and interactive dashboard experience.
#   - A dropdown lets the viewer switch the chart between two views:
#     "Normalized % Price Change" and "30-Day Rolling Volatility."
#   - A second dropdown lets the viewer add/remove specific stocks from 
#     the chart.
#   
#
# Takeaway:
#   Bitcoin's volatility gap continues to show up every month even when 
#   Apple’s stock prices are barely moving. Visually, Apple is perceived 
#   as almost flat while Bitcoin’s prices are continuously jagged peaks.
#
# AI assistance:
#   We used Claude Pro to help us brainstorm ideas for our story angle, 
#   structure data calculations and percent changes, write the callback 
#   code on how to connect our interactive element with the chart, and 
#   to write code for our style sheet and various labeling. Additionally, 
#   Claude Pro was especially useful for problem solving for generating 
#   the correct connection to Yahoo Finance. After Claude would provide 
#   code, we made sure to review and understand each line before submission.  
#
#   All code was reviewed and understood before submission.
# ============================================================

from dash import Dash, html, dcc, Input, Output

# Claude used these libraries to fetch, process, and visualize financial data
import os
import datetime as dt

import numpy as np
import pandas as pd
import yfinance as yf 
import matplotlib
matplotlib.use("Agg")  # Render without a GUI backend
import matplotlib.pyplot as plt

# 1. Fetch data from the API

TICKERS = ["BTC-USD", "AAPL", "SPY"]
PERIOD = "1y"

raw = yf.download(TICKERS, period=PERIOD, auto_adjust=True)["Close"]
raw = raw.dropna(how="all").ffill().dropna()

# 2. Analytics touches
# We used Claude to help us implement the analytics touches, 
# including calculating daily returns,
# calculating normalized percent changes, 
# and rolling volatility.

# (a) Daily % return
daily_returns = raw.pct_change().dropna()

# (b) Normalized % change from the start of the window (all series start at 0%)
normalized = (raw / raw.iloc[0] - 1) * 100

# (c) Rolling 30-day volatility (std dev of daily returns)
ROLL_WINDOW = 30
rolling_vol = daily_returns.rolling(ROLL_WINDOW).std() * 100  # in %

# Annualized volatility summary (for the static image)
annualized_vol = daily_returns.std() * np.sqrt(252) * 100  # in %

# 3. Static image — matplotlib bar chart, saved to assets
# We used Claude to help us create a static image summarizing the annualized volatility of BTC and AAPL.
os.makedirs("assets", exist_ok=True)
IMG_PATH = os.path.join("assets", "volatility_summary.png")

fig, ax = plt.subplots(figsize=(5, 4))
bars = ax.bar(
    ["BTC-USD", "AAPL"],
    [annualized_vol["BTC-USD"], annualized_vol["AAPL"]],
    color=["#dc6e6e", "#6699F1"],
)
ax.set_title("Annualized Volatility: BTC vs. AAPL")
ax.set_ylabel("Annualized Volatility (%)")
for b in bars:
    height = b.get_height()
    ax.annotate(f"{height:.1f}%", (b.get_x() + b.get_width() / 2, height),
                textcoords="offset points", xytext=(0, 4), ha="center")
ax.text(0.5, -0.22, "Source: Yahoo Finance", transform=ax.transAxes,
        ha="center", fontsize=8, color="gray")
fig.tight_layout()
fig.savefig(IMG_PATH, dpi=150)
plt.close(fig)

# 4. Dash app layout
# We used Claude to help us set up the Dash app layout,
# especially organizing the layout into aesthetic sections 
# and adding user-friendly labels for the dropdowns and controls.

FONT_URL = "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Manrope:wght@400;500;600;700&display=swap"

app = Dash(__name__, external_stylesheets=[FONT_URL])
app.title = "Crypto Vs. Traditional Equity"

date_min = raw.index.min()
date_max = raw.index.max()
date_marks = {
    int(d.timestamp()): d.strftime("%b %Y")
    for d in pd.date_range(date_min, date_max, periods=6)
}

# Plain-language names so people who don't follow the stock market
# can still tell what's being compared

FRIENDLY = {
    "BTC-USD": "Bitcoin",
    "AAPL": "Apple",
    "SPY": "The overall stock market (S&P 500)",
}

app.layout = html.Div(
    className="page",
    children=[
        html.Div(
            className="wrap",
            children=[
                html.H1("Bitcoin vs. Apple — A Tale of Two Volatilities", className="page-title"),

                html.Div(
                    className="box intro-box",
                    children=[
                        html.P(
                            "The purpose of this dashboard is to visualize Bitcoin’s price to "
                            "Apple’s Stock price over a 12 month period. Apple’s prices are "
                            "much more stable compared to Bitcoin’s prices which are more volatile."
                        ),
                    ],
                ),

                html.Div(
                    className="box controls-box",
                    children=[
                        html.Div(
                            style={"display": "flex", "gap": "24px", "flexWrap": "wrap", "marginBottom": 16},
                            children=[
                                html.Div([
                                    html.Label("View:", title="Choose how you want to compare the two"),
                                    dcc.Dropdown(
                                        id="view-dropdown",
                                        options=[
                                            {"label": "📈 Price change over time", "value": "normalized"},
                                            {"label": "🎢 How bumpy the ride was", "value": "volatility"},
                                        ],
                                        value="normalized",
                                        clearable=False,
                                        style={"width": 280},
                                    ),
                                ]),
                                html.Div([
                                    html.Label("Assets to show:", title="Pick which ones appear on the chart"),
                                    dcc.Dropdown(
                                        id="asset-dropdown",
                                        options=[
                                            {"label": f"{FRIENDLY[t]} ({t})", "value": t} for t in TICKERS
                                        ],
                                        value=["BTC-USD", "AAPL"],
                                        multi=True,
                                        style={"width": 320},
                                    ),
                                ]),
                            ],
                        ),

                        html.Label("Quick jump:"),
                        dcc.RadioItems(
                            id="preset-range",
                            options=[
                                {"label": "Full year", "value": "full"},
                                {"label": "Last 3 months", "value": "3m"},
                                {"label": "Last month", "value": "1m"},
                            ],
                            value="full",
                            inline=True,
                            className="preset-radio",
                        ),

                        html.Label("Date range:", style={"marginTop": 14}),
                        dcc.RangeSlider(
                            id="date-slider",
                            min=int(date_min.timestamp()),
                            max=int(date_max.timestamp()),
                            value=[int(date_min.timestamp()), int(date_max.timestamp())],
                            marks=date_marks,
                            step=86400,
                        ),
                    ],
                ),

                html.Div(
                    className="box chart-box",
                    children=[
                        dcc.Graph(id="main-chart"),
                    ],
                ),

                html.Div(
                    className="box insight-box",
                    children=[
                        html.H3("🔎 What does this mean?"),
                        html.Div(id="insight-text"),
                    ],
                ),

                html.Div(
                    className="box image-box",
                    children=[
                        html.H3("Annualized Volatility Summary"),
                        html.Img(src="/assets/volatility_summary.png"),
                    ],
                ),

                html.Div(
                    className="box source-box",
                    children=[
                        html.P("Source: Yahoo Finance (via yfinance)", className="source-text"),
                    ],
                ),
            ],
        ),
    ],
)

# 5. Callbacks
# We used Claude to help us set up 3 callbacks for adjusting the 
# date range for the interactive chart. Claude came up with one
# which was very interesting: letting the user change the view
# being either price percentage changes or average daily swing

# Callback — quick-jump preset buttons control the date slider
@app.callback(
    Output("date-slider", "value"),
    Input("preset-range", "value"),
)
def apply_preset(preset):
    end = date_max
    if preset == "3m":
        start = max(date_min, end - pd.Timedelta(days=90))
    elif preset == "1m":
        start = max(date_min, end - pd.Timedelta(days=30))
    else:
        start = date_min
    return [int(start.timestamp()), int(end.timestamp())]

# Callback — connects both dropdowns and the slider to the chart
@app.callback(
    Output("main-chart", "figure"),
    Input("view-dropdown", "value"),
    Input("asset-dropdown", "value"),
    Input("date-slider", "value"),
)
def update_chart(view, assets, date_range):
    if not assets:
        assets = ["BTC-USD"]

    start = dt.datetime.fromtimestamp(date_range[0])
    end = dt.datetime.fromtimestamp(date_range[1])

    if view == "normalized":
        window = raw.loc[start:end]
        window = (window / window.iloc[0] - 1) * 100
        y_title = "% Change from Start"
        title = "How each price moved over time"
    else:
        window = rolling_vol.loc[start:end]
        y_title = "Average Daily Swing (%)"
        title = "How bumpy each ride was, day to day"

    fig = {
        "data": [
            {
                "x": window.index,
                "y": window[a],
                "type": "scatter",
                "mode": "lines",
                "name": FRIENDLY.get(a, a),
            }
            for a in assets if a in window.columns
        ],
        "layout": {
            "title": {"text": title},
            "xaxis": {"title": {"text": "Date"}},
            "yaxis": {"title": {"text": y_title}, "rangemode": "tozero"},
            "legend": {"title": {"text": ""}},
            "annotations": [{
                "text": "Source: Yahoo Finance",
                "xref": "paper", "yref": "paper",
                "x": 1, "y": -0.18,
                "showarrow": False,
                "font": {"size": 10, "color": "gray"},
            }],
            "margin": {"b": 80},
        },
    }
    return fig

# Callback — plain-English explanation of what's on screen
@app.callback(
    Output("insight-text", "children"),
    Input("view-dropdown", "value"),
    Input("asset-dropdown", "value"),
    Input("date-slider", "value"),
)
def update_insight(view, assets, date_range):
    if not assets:
        return html.P("Pick at least one asset above to see what's going on.")

    start = dt.datetime.fromtimestamp(date_range[0])
    end = dt.datetime.fromtimestamp(date_range[1])

    lines = []
    metrics = {}

    if view == "normalized":
        window = raw.loc[start:end]
        window = (window / window.iloc[0] - 1) * 100
        for a in assets:
            if a in window.columns:
                val = window[a].iloc[-1]
                metrics[a] = val
                direction = "up" if val >= 0 else "down"
                lines.append(html.P(f"{FRIENDLY.get(a, a)} went {direction} about {abs(val):.0f}% over this period."))
    else:
        window = rolling_vol.loc[start:end]
        for a in assets:
            if a in window.columns and window[a].notna().any():
                val = window[a].mean()
                metrics[a] = val
                lines.append(html.P(
                    f"{FRIENDLY.get(a, a)}'s price bounced around by about {val:.1f}% a day, on average."
                ))

    if "BTC-USD" in metrics and len(metrics) > 1:
        other = next(a for a in metrics if a != "BTC-USD")
        btc_val = abs(metrics["BTC-USD"]) or 0.01
        other_val = abs(metrics[other]) or 0.01
        ratio = btc_val / other_val
        if ratio >= 1:
            lines.append(html.P(
                f"👉 Bottom line: Bitcoin was roughly {ratio:.1f}× more dramatic than "
                f"{FRIENDLY.get(other, other)} over this stretch.",
                className="insight-highlight",
            ))

    if not lines:
        lines = [html.P("Not enough data in this range — try widening the date slider.")]

    return lines

if __name__ == "__main__":
    app.run(debug=True)
