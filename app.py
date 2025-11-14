from flask import Flask, render_template, request
import os
import requests
import pandas as pd
import pygal

app = Flask(__name__)

API_KEY = "0W8V2C7EF7NNQ07C" 

FUNCTION_MAP = {
    "daily": "TIME_SERIES_DAILY",
    "weekly": "TIME_SERIES_WEEKLY",
    "monthly": "TIME_SERIES_MONTHLY"
}

def load_symbols_from_csv():
    csv_path = os.path.join(os.path.dirname(__file__), "stocks.csv")
    df = pd.read_csv(csv_path)

    symbols = df.iloc[:, 0].dropna().astype(str).tolist()
    symbols = sorted(set(symbols))
    return symbols

def fetch_data(symbol: str, series: str):
    """Call Alpha Vantage and return the raw time-series JSON block and function name."""
    function = FUNCTION_MAP.get(series.lower(), "TIME_SERIES_DAILY")

    url = (
        "https://www.alphavantage.co/query"
        f"?function={function}&symbol={symbol}&apikey={API_KEY}"
    )

    resp = requests.get(url)
    data = resp.json()

    print("API response keys:", list(data.keys()))

    ts_key = next((k for k in data.keys() if "Time Series" in k), None)
    if ts_key is None:
        print("No time series key found in response. Full response:", data)
        return None, function

    return data[ts_key], function



def get_stock_dataframe(symbol: str, series: str):
    """Return a cleaned pandas DataFrame with OHLCV data."""
    ts_data, function = fetch_data(symbol, series)

    if ts_data is None:
        return None, function

    df = pd.DataFrame.from_dict(ts_data, orient="index")

    cols = list(df.columns)
    clean_names = []
    for c in cols:
        if ". " in c:
            clean_names.append(c.split(". ", 1)[1])
        else:
            clean_names.append(c)
    df.columns = clean_names

    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    return df, function


def make_pygal_chart(df, symbol, function, start_label, end_label, chart_type="line"):
    """Create a pygal Line or Bar chart and return SVG as a string."""

    dates = [d.strftime("%Y-%m-%d") for d in df.index]
    chart_data = {
        "open": df["open"].tolist() if "open" in df.columns else [],
        "high": df["high"].tolist() if "high" in df.columns else [],
        "low": df["low"].tolist() if "low" in df.columns else [],
        "close": df["close"].tolist() if "close" in df.columns else [],
    }

    if chart_type == "bar":
        chart = pygal.Bar(x_label_rotation=45, show_minor_x_labels=False)
    else:
        chart = pygal.Line(x_label_rotation=45, show_minor_x_labels=False)

    chart.title = (
        f"{symbol.upper()} "
        f"{function.replace('TIME_SERIES_', '').title()} Stock Prices "
        f"({start_label} \u2192 {end_label})"
    )

    chart.x_labels = dates
    if dates:
        step = max(1, len(dates) // 10)
        chart.x_labels_major = dates[::step]

    for category, prices in chart_data.items():
        if prices:  
            chart.add(category, prices)

    svg_bytes = chart.render()
    svg_str = svg_bytes.decode("utf-8")
    return svg_str

@app.route("/", methods=["GET", "POST"])
def index():
    symbols = load_symbols_from_csv()
    chart_svg = None

    if request.method == "POST":
        symbol = request.form.get("symbol")
        series = request.form.get("series", "daily")
        chart_type = request.form.get("chart_type", "line")
        start_date = request.form.get("start")  
        end_date = request.form.get("end")      

        print("Form submitted:", symbol, series, chart_type, start_date, end_date)

        df, function = get_stock_dataframe(symbol, series)

        if df is None or df.empty:
            print("No data returned for symbol/series")
        else:
            if start_date:
                start_ts = pd.to_datetime(start_date)
                df = df[df.index >= start_ts]
            else:
                start_ts = df.index.min()

            if end_date:
                end_ts = pd.to_datetime(end_date)
                df = df[df.index <= end_ts]
            else:
                end_ts = df.index.max()

            if df.empty:
                print("DataFrame became empty after date filter")
            else:
                start_label = start_ts.date().isoformat()
                end_label = end_ts.date().isoformat()

                chart_svg = make_pygal_chart(
                    df,
                    symbol,
                    function,
                    start_label,
                    end_label,
                    chart_type=chart_type,
                )

    return render_template("index.html", symbols=symbols, chart_svg=chart_svg)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

