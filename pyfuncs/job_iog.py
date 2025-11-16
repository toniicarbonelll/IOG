from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import os
import time
from bs4 import BeautifulSoup
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import requests
import sys
import json
sys.path.append(os.path.abspath("C:/Users/A200348545/Escritorio 2/Personal-Projects/IOG"))
sys.path.append(os.path.abspath("C:/Users/A200348545/Escritorio 2/Personal-Projects/IOG/pyfuncs"))
from iog import *
from credentials import Credentials


###################################################################################
# This file contains the job to generate the winners list. It will be
# executed every day.
###################################################################################


urls = [
    "https://finance.yahoo.com/markets/stocks/52-week-gainers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/52-week-losers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/gainers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/losers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/trending/"

]

print(f"Getting all tickers...")
tickers = get_all_tickers_from_all_urls(urls, verbose=True)

print(f"\nGetting the winners list...")
json_output = get_winners_list(tickers, top=10, days=365, windows_in_days=[7, 30, 90, 365], verbose=True)


print(f"\nSaving the winners list...")
with open('../data/winners.json', 'w+') as file:
    file.write(json_output)


