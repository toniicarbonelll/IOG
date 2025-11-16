from flask import Flask, jsonify, request
import base64
import os
import sys
import json
sys.path.append(os.path.abspath("C:/Users/A200348545/Escritorio 2/Personal-Projects/IOG"))
sys.path.append(os.path.abspath("C:/Users/A200348545/Escritorio 2/Personal-Projects/IOG/pyfuncs"))
from press_releases import *
from credentials import Credentials
from press_releases import start_driver
from tickernerd import tickernerd, danelfin
from iog import *

app = Flask(__name__)


@app.route('/iog/get_press_releases_list', methods=['POST'])
def get_press_releases_list():
    data = request.get_json()  # Parse incoming JSON data
    if not data or 'ticker' not in data:
        return jsonify({"error": "Missing 'ticker' field in JSON body"}), 400

    ticker = data['ticker']
    driver = start_driver(credentials=Credentials(), headless=False, verbose=True)
    df = get_press_releases_df(driver, ticker, verbose=True)
    json = df_to_json(df)
    return json


@app.route('/iog/scrap_press_releases', methods=['POST'])
def scrap_press_releases():
    data = request.get_json()  # Parse incoming JSON data
    if not data or 'urls' not in data:
        return jsonify({"error": "Missing 'urls' field in JSON body"}), 400
    urls = data['urls']
    driver = start_driver(credentials=Credentials(), headless=False, verbose=True)
    batch = get_articles_batch(driver, urls, verbose=True)
    output = dict()
    for i, url in enumerate(urls):
        output[url]=batch[i]
    return json.dumps(output)


@app.route('/iog/scrap_tickers_in_others', methods=['POST'])
def scrap_tickers_in_others():
    data = request.get_json()  # Parse incoming JSON data
    if not data or 'ticker' not in data:
        return jsonify({"error": "Missing 'ticker' field in JSON body"}), 400
    
    ticker = data['ticker']

    # Scrapping
    driver = start_driver(credentials=Credentials(), headless=False, verbose=True)
    print("scrapping tickernerd")
    output_1 = tickernerd(driver, ticker)
    print("scrapping danelfin")
    driver = start_driver_undetected(driver_path='../chromedriver.exe', credentials=Credentials(), verbose=True)
    driver.get(url="https://www.google.com")
    output_2 = danelfin(driver, ticker)

    # Output
    output_dict = dict()
    output_dict["tickernerd_investment_strategy"] = output_1[0]
    output_dict["tickernerd_company_summary"] = output_1[1]
    output_dict["danelfin_investment_strategy"]= output_2

    # Moving the generated image to assets...
    #os.system(r'move "C:\Users\A200348545\Escritorio 2\Personal-Projects\IOG\APIs\priceChart.jpg" "C:\Users\A200348545\Escritorio 2\Personal-Projects\IOG\frontend\src\assets\priceChart.jpg"')
    # --- Add image as base64 ---
    with open("./priceChart.jpg", "rb") as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
    output_dict["image"] = encoded_image
    return json.dumps(output_dict)


@app.route('/iog/generate_opportunities', methods=['GET', 'POST'])
def generate_opportunities():
    top = int(request.args.get('top', 10))  # default = '10'

    # Getting the windows or setting the default
    data = request.get_json() 
    if not data or 'windows' not in data:
        windows = [7, 30, 90, 365]
    else:
        windows = data['windows']
    
    print(f"Returned parameters are --> top: {top} and windows: {windows}")
    # Setting URLs
    urls = [
    "https://finance.yahoo.com/markets/stocks/52-week-gainers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/52-week-losers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/gainers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/losers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/trending/"
    ]

    print(f"Getting all tickers...")
    driver = start_driver(credentials=Credentials(), headless=True, verbose=True)
    tickers = get_all_tickers_from_all_urls(driver, urls, verbose=True)

    print(f"\nGetting the winners list...")
    json_output = get_winners_list(tickers, Credentials(), top=top, days=365, windows_in_days=windows, verbose=True)


    print(f"\nSaving the winners list...")
    with open('winners.json', 'w+') as file:
        file.write(json_output)
        
    return json_output


@app.route('/iog/read_opportunities', methods=['GET'])
def read_opportunities():
    with open('winners.json', 'r') as file:
        json_str = file.read()
    return json_str


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
