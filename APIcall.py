# ============================================================
# Mini Finance Dashboard — Crypto vs. Traditional Equity
# Team #: [FILL IN]
# Members: [FILL IN NAMES]
#
# Question / Story:
#   How does Bitcoin's volatility compare to a blue-chip stock
#   like AAPL over the same year? Crypto swings are much bigger,
#   which makes for an easy-to-see, visually dramatic story.
#
# Data Choices:
#   - BTC-USD (Bitcoin) and AAPL (Apple Inc.) over the past 1 year,
#     pulled live via yfinance. SPY (S&P 500 ETF) is included as an
#     optional third series so the viewer can see how the broader
#     market compares as well.
#
# Interactivity:
#   - A dropdown lets the viewer switch the chart between two views:
#     "Normalized % Price Change" and "30-Day Rolling Volatility."
#   - A second dropdown lets the viewer add/remove SPY from the chart.
#   - A date-range slider lets the viewer zoom into a specific window
#     (e.g. a crypto crash or rally) and compare how each asset reacted.
#
# Takeaway:
#   Bitcoin's rolling volatility is consistently several multiples
#   higher than AAPL's (and SPY's) throughout the year, including
#   periods when the equities barely move. Visually, BTC's line looks
#   jagged and mountainous while AAPL/SPY look almost flat by comparison.
#
# AI assistance:
#   Used Claude to brainstorm the story angle (crypto vs. equity
#   volatility), to help structure the normalized % change and rolling
#   volatility calculations, to help write the callback connecting the
#   dropdowns/slider to the chart, and to help write the axis/legend/
#   source labeling and page title styling. All code was reviewed and
#   understood before submission.
# ============================================================

import os
import datetime as dt

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use("Agg")  # render without a GUI backend
import matplotlib.pyplot as plt

from dash import Dash, html, dcc, Input, Output

# ------------------------------------------------------------
# 1. Fetch data from the API (this runs every time the app starts)
# ------------------------------------------------------------
TICKERS = ["BTC-USD", "AAPL", "SPY"]
PERIOD = "1y"

raw = yf.download(TICKERS, period=PERIOD, auto_adjust=True)["Close"]
raw = raw.dropna(how="all").ffill().dropna()

# ------------------------------------------------------------
# 2. Analytics touches
# ------------------------------------------------------------
# (a) Daily % return
daily_returns = raw.pct_change().dropna()

# (b) Normalized % change from the start of the window (all series start at 0%)
normalized = (raw / raw.iloc[0] - 1) * 100

# (c) Rolling 30-day volatility (std dev of daily returns)
ROLL_WINDOW = 30
rolling_vol = daily_returns.rolling(ROLL_WINDOW).std() * 100  # in %

# Annualized volatility summary (for the static image)
annualized_vol = daily_returns.std() * np.sqrt(252) * 100  # in %

# ------------------------------------------------------------
# 3. Static image — matplotlib bar chart, saved to assets/
# ------------------------------------------------------------
os.makedirs("assets", exist_ok=True)
IMG_PATH = os.path.join("assets", "volatility_summary.png")

fig, ax = plt.subplots(figsize=(5, 4))
bars = ax.bar(
    ["BTC-USD", "AAPL"],
    [annualized_vol["BTC-USD"], annualized_vol["AAPL"]],
    color=["#f2a900", "#555555"],
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

# ------------------------------------------------------------
# 4. Dash app layout
# ------------------------------------------------------------
FONT_URL = "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Manrope:wght@400;500;600;700&display=swap"

app = Dash(__name__, external_stylesheets=[FONT_URL])
app.title = "Crypto vs. Traditional Equity"

date_min = raw.index.min()
date_max = raw.index.max()
date_marks = {
    int(d.timestamp()): d.strftime("%b %Y")
    for d in pd.date_range(date_min, date_max, periods=6)
}

app.layout = html.Div(
    className="page",
    children=[
        html.Div(
            className="wrap",
            children=[
                html.H1("Bitcoin vs. Apple — a tale of two volatilities", className="page-title"),

                html.Div(
                    className="box intro-box",
                    children=[
                        html.P(
                            "This dashboard compares Bitcoin's price swings to Apple stock "
                            "(and, optionally, the S&P 500) over the past year, showing how "
                            "much more dramatic crypto volatility is compared to a blue-chip "
                            "equity or the broader market."
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
                                    html.Label("View:"),
                                    dcc.Dropdown(
                                        id="view-dropdown",
                                        options=[
                                            {"label": "Normalized % Price Change", "value": "normalized"},
                                            {"label": "30-Day Rolling Volatility", "value": "volatility"},
                                        ],
                                        value="normalized",
                                        clearable=False,
                                        style={"width": 260},
                                    ),
                                ]),
                                html.Div([
                                    html.Label("Assets to show:"),
                                    dcc.Dropdown(
                                        id="asset-dropdown",
                                        options=[{"label": t, "value": t} for t in TICKERS],
                                        value=["BTC-USD", "AAPL"],
                                        multi=True,
                                        style={"width": 260},
                                    ),
                                ]),
                            ],
                        ),

                        html.Label("Date range:"),
                        dcc.RangeSlider(
                            id="date-slider",
                            min=int(date_min.timestamp()),
                            max=int(date_max.timestamp()),
                            value=[int(date_min.timestamp()), int(date_max.timestamp())],
                            marks=date_marks,
                            step=86400,  # one day
                            tooltip={"placement": "bottom", "always_visible": False},
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

# ------------------------------------------------------------
# 5. Callback — connects both dropdowns and the slider to the chart
# ------------------------------------------------------------
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
        title = "BTC vs. AAPL vs. SPY: Normalized % Price Change"
    else:
        window = rolling_vol.loc[start:end]
        y_title = "30-Day Rolling Volatility (%)"
        title = "BTC vs. AAPL vs. SPY: Rolling 30-Day Volatility"

    fig = {
        "data": [
            {
                "x": window.index,
                "y": window[a],
                "type": "scatter",
                "mode": "lines",
                "name": a,
            }
            for a in assets if a in window.columns
        ],
        "layout": {
            "title": title,
            "xaxis": {"title": "Date"},
            "yaxis": {"title": y_title},
            "legend": {"title": {"text": "Asset"}},
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


if __name__ == "__main__":
    app.run(debug=True)