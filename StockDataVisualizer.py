import requests
import json
import pygal
from datetime import datetime
import os
import webbrowser

API_KEY = "0W8V2C7EF7NNQ07C"
URL = "https://www.alphavantage.co/query"

def fetch_stock_data(symbol, function='TIME_SERIES_DAILY', start_date="", end_date=""):
    parameters = {
        "function": function,
        "symbol": symbol,
        "apikey": API_KEY,
        "datatype": "json"
    }

    if function == "TIME_SERIES_INTRADAY":
        interval = input("Enter the interval (1min, 5min, 15min, 30min, 60min): ")
        parameters["interval"] = interval

    response = requests.get(URL, params=parameters)

    if response.status_code == 200:
        data = response.json()

        if function == "TIME_SERIES_INTRADAY":
            for key in data.keys():
                if key.startswith("Time Series ("):
                    return data[key]

        elif function == "TIME_SERIES_DAILY" and "Time Series (Daily)" in data:
            return data["Time Series (Daily)"]
        elif function == "TIME_SERIES_WEEKLY" and "Weekly Time Series" in data:
            return data["Weekly Time Series"]
        elif function == "TIME_SERIES_MONTHLY" and "Monthly Time Series" in data:
            return data["Monthly Time Series"]
        else:
            print("Error: Data not available for the given stock symbol or function.")
            return None
    else:
        print("Error: Unable to fetch data from Alpha Vantage.")
        return None

def genBar(stock_data, symbol, function, start_date_str, end_date_str):
    chart_data = {
    "open": [],
    "high": [],
    "low": [],
    "close": []
    }

    dates = sorted(stock_data.keys())

    for time in sorted(stock_data):
        chart_data["open"].append(float(stock_data[time]["1. open"]))
        chart_data["high"].append(float(stock_data[time]["2. high"]))
        chart_data["low"].append(float(stock_data[time]["3. low"]))
        chart_data["close"].append(float(stock_data[time]["4. close"]))

    BarChart = pygal.Bar(x_label_rotation=45, show_minor_x_labels=False)
    BarChart.title = f"{symbol.upper()} {function.replace('TIME_SERIES_', '').title()} Stock Prices ({start_date_str} → {end_date_str})"
    BarChart.x_labels = dates
    BarChart.x_labels_major = dates[::max(1, len(dates)//10)]  # Show fewer x-labels if dataset is large

    for category, prices in chart_data.items():
        BarChart.add(category, prices)

    filename = f"{symbol.upper()}_{function.split('_')[-1]}_{start_date_str}_to_{end_date_str}_Bar.svg"
    filepath = os.path.abspath(filename)
    BarChart.render_to_file(filepath)

    print(f"Bar chart saved as {filename}")
    webbrowser.open(f"file://{filepath}")


def genLine(stock_data, symbol, function, start_date_str, end_date_str):

    chart_data = {
    "open": [],
    "high": [],
    "low": [],
    "close": []
    }

    dates = sorted(stock_data.keys())

    for time in sorted(stock_data):
        chart_data["open"].append(float(stock_data[time]["1. open"]))
        chart_data["high"].append(float(stock_data[time]["2. high"]))
        chart_data["low"].append(float(stock_data[time]["3. low"]))
        chart_data["close"].append(float(stock_data[time]["4. close"]))


    LineChart = pygal.Line(x_label_rotation=45, show_minor_x_labels=False)
    LineChart.title = f"{symbol.upper()} {function.replace('TIME_SERIES_', '').title()} Stock Prices ({start_date_str} → {end_date_str})"
    LineChart.x_labels = dates
    LineChart.x_labels_major = dates[::max(1, len(dates)//10)]

    for category, prices in chart_data.items():
        LineChart.add(category, prices)

    filename = f"{symbol.upper()}_{function.split('_')[-1]}_{start_date_str}_to_{end_date_str}_Line.svg"
    filepath = os.path.abspath(filename)
    LineChart.render_to_file(filepath)

    print(f"Line chart saved as {filename}")
    webbrowser.open(f"file://{filepath}")



def filter_by_date(stock_data, start_date, end_date):
    filtered_data = {}
    for date_str, values in stock_data.items():
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue  
        if start_date <= date_obj <= end_date:
            filtered_data[date_str] = values
    return dict(sorted(filtered_data.items()))


def main():
    symbol = input("Enter the Stock Symbol: ")
    
    print("Choose a time series function:")
    print("1. DAILY (Time Series Daily)")
    print("2. WEEKLY (Time Series Weekly)")
    print("3. MONTHLY (Time Series Monthly)")
    print("4. INTRADAY (Time Series Intraday)")
    choice = input("Enter the number corresponding to your choice: ")
    
    if choice == "1":
        function = "TIME_SERIES_DAILY"
    elif choice == "2":
        function = "TIME_SERIES_WEEKLY"
    elif choice == "3":
        function = "TIME_SERIES_MONTHLY"
    elif choice == "4":
        function = "TIME_SERIES_INTRADAY"
    else:
        print("Invalid choice. Defaulting to DAILY.")
        function = "TIME_SERIES_DAILY"

    while True:
        try:
            start_date_str = input("Enter the beginning date (YYYY-MM-DD): ")
            end_date_str = input("Enter the ending date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            if end_date < start_date:
                print("Error: End date cannot be before start date. Try again.")
                continue
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
    
    stock_data = fetch_stock_data(symbol, function)

    if stock_data:
        stock_data = filter_by_date(stock_data, start_date, end_date)

        if not stock_data:
            print("No data found within the given date range.")
            return

        print(f"Stock data for {symbol} retrieved successfully and filtered by date range!")

        while True:
            chartType = input("Would you like your data in a Bar Graph or Line Graph?(enter 1 or 2 respectively) ")
            if chartType == "1":
                genBar(stock_data, symbol, function, start_date_str, end_date_str)
                break
            elif chartType == "2":
                genLine(stock_data, symbol, function, start_date_str, end_date_str)
                break
            else:
                print("Please enter 1 to generate a Bar Graph or 2 to generate a Line Graph")
    else:
        print("Failed to retrieve stock data.")

if __name__ == "__main__":
    main()