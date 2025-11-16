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
from credentials import Credentials
import json



################################################################################
urls = [
    "https://finance.yahoo.com/markets/stocks/52-week-gainers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/52-week-losers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/gainers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/losers/?start=0&count=25",
    "https://finance.yahoo.com/markets/stocks/trending/"

]

# 1.  Getting the list of tickers from an URL
def get_tickers_from_url(driver, url: str, reject_cookies:bool = False, verbose:bool = False) -> list[str]:
    """Given a yahoo finance URL (top gainers, top losers...), it returns the list of all tickers for that table

    Args:
        driver (driver): Driver
        url (str): Yahoo Finance URL
        reject_cookies (bool): Reject cookies
        verbose (bool): Print statements

    Returns:
        list[str]: List of tickers
    """

    # set url
    url = url

    # get top tickers from table
    # Ir a la url
    driver.get(url)

    # Initialize arrays (add tickers)
    tickers = []

    # 1. Reject all cookies
    if reject_cookies:
        verbose and print("Rejecting cookies")
        buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".actions.couple"))
        )
        rechazar_button = buttons.find_element(by=By.CSS_SELECTOR, value=".btn.secondary.reject-all")
        rechazar_button.click()

    # 2. Get all tickers from the table
    verbose and print("Getting all tickers...")
    container = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "table"))
    )

    table_html = container.get_attribute('outerHTML')
    soup = BeautifulSoup(table_html, 'html.parser')
    rows = soup.select("tbody tr")
    for row in rows:
        ticker = (row.find('td').find('a').text.strip())
        tickers.append(ticker)
    verbose and print("Tickers retrieved successfully!")
    return tickers


def get_all_tickers_from_all_urls(driver, urls: list[str], verbose:bool=False) -> list[str]:
    """Getting all tickers from a list of yahoo finance URLs.

    Args:
        driver (driver): Driver
        urls (list[str]): List of yahoo finance URLs.
        verbose (bool, optional): If you want to print the process. Defaults to False.

    Returns:
        list[str]: List of tickers.
    """
    # Getting all tickers
    tickers_from_url = {}
    # first one... (reject cookies)
    verbose and print(f"url : {1} of {len(urls)}... --> {urls[0]}")
    tickers = get_tickers_from_url(driver, urls[0], reject_cookies=True, verbose=verbose)
    tickers_from_url[urls[0]] = list(tickers)
    # rest of them... (dont reject cookies)
    for idx, url in enumerate(urls[1:]):
        verbose and print(f"url : {idx+2} of {len(urls)}... --> {url}")
        tickers = get_tickers_from_url(driver, url, reject_cookies=False, verbose=verbose)
        tickers_from_url[url] = list(tickers)

    # Doing a set from all said tickers and returning it
    verbose and print("Creating the set of different tickers...")
    final_list = list()
    for tickers in tickers_from_url.values():
        final_list += tickers

    return list(set(final_list))

##########################################################################################################
##########################################################################################################
# 2. Getting stock data info

def get_stock_data_for_last_x_days(ticker:str, days:int=365, credentials:Credentials=Credentials()):
    """Getting stock data for a ticker for the last "x" days.

    Args:
        ticker (str): _description_
        days (int, optional): Total window of days for which you want to retrieve the data. Defaults to 365.
        credentials (Credentials, optional): Credentials for proxy connection. Defaults to Credentials().

    Returns:
        _type_: _description_
    """
    os.environ["http_proxy"] = credentials.http_proxy
    os.environ["https_proxy"] = credentials.https_proxy
    # Calculate date 1 year ago from today
    end_date = datetime.today()
    start_date = end_date - timedelta(days+7)  # one year and one week
    
    # Download historical stock data
    stock_data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), auto_adjust=True, progress=False)
    
    return stock_data


def filter_stock_data_by_windows(df: pd.DataFrame, windows_in_days:list[int] = [7, 30, 365]):
    """Given a stock_df, it returns only the rows corresponding to today() and a specified windows of dates (ex: 7 days ago, 30 days ago...)

    Args:
        df (pd.DataFrame): Output of get_stock_data_for_last_x_days()
        windows_in_days (list[int], optional): Windows of days to keep. Defaults to [7, 30, 365].

    Returns:
        pd.DataFrame: Filtered df
    """
    today = df.iloc[-1].name #last available date
    references = [today]
    for window in windows_in_days:
        reference = today - pd.Timedelta(days=window) # calculate previous date
        if reference in df.index:
            references.append(reference)
        else: #pick next available date only if the difference between the two is less than
            new_reference = df[reference:].iloc[0].name
            if abs((reference - new_reference).days)<5:
                references.append(new_reference)
    
    df =  df.loc[references][('Close')]
    df.columns = ["Value"]
    return df


def calculate_alfas(df:pd.DataFrame) -> pd.DataFrame:
    """Calculates the "alfa" (diff in %) between todays value and other values of the DataFrame. Returns the DataFrame with a new column ('Diff').

    Args:
        df (pd.DataFrame): Output of filter_stock_data_by_windows()

    Returns:
        pd.DataFrame: DataFrame with new column ('Diff').
    """
    # PRE: output of get_important_dates
    df['Today'] = df.iloc[0].item()
    df['Diff'] = round((df['Today']-df['Value'])/(df['Value']), 4)
    return df.iloc[1:]

def get_processed_stock_info_for_ticker(ticker:str, credentials=Credentials(), days:int = 365, windows_in_days:list[int] = [7, 30, 365]) -> pd.DataFrame:
    """Gets the processed stock info (calculated alfas for specified time windows) for a ticker.

    Args:
        ticker (str): Ticker name.
        credentials (Credentials()): Credentials for proxy connection.
        days (int, optional): Max window of days for the stock. Defaults to 365.
        windows_in_days (list[int], optional): Windows of days. Defaults to [7, 30, 365].

    Returns:
        pd.DataFrame: DataFrame containing 'Date' index and 'ticker' column with all the alfas for all dates
    """
    df = get_stock_data_for_last_x_days(ticker, days, credentials=credentials)
    df = filter_stock_data_by_windows(df, windows_in_days)
    df = calculate_alfas(df)
    df = df.rename(columns={'Diff':ticker})
    return df[[ticker]]

def get_merged_df(tickers:list[str], credentials=Credentials(), days:int = 365, windows_in_days:list[int] = [7, 30, 365], verbose:bool=False) -> pd.DataFrame:
    """Gets the merged dataframe of all processed stock_info for all tickers on a list and the specified windows of days

    Args:
        tickers (list[str]): List of tickers.
        credentials (Credentials): Credentials for proxy connection
        days (int, optional): Max window of days for the stocks. Defaults to 365.
        windows_in_days (list[int], optional): Windows of days. Defaults to [7, 30, 365].
        verbose (bool): Print statements.

    Returns:
        pd.DataFrame: Merged DataFrame
    """

    final_df = get_processed_stock_info_for_ticker(tickers[0], credentials, days, windows_in_days)
    for i in range(1, len(tickers)):
        if i%10==0:
            verbose and print(f"Getting ticker {i} of {len(tickers)}...")
        try:
            df = get_processed_stock_info_for_ticker(tickers[i], credentials, days, windows_in_days)
            final_df = pd.concat([df, final_df], axis=1, ignore_index=False)
        except:
            print(f"Ticker: {tickers[i]} not possible to merge due to missing data or impossible download...")
    final_df = final_df.fillna(0) #we can do this so that they won't bother us on the "get_winners_function"
    return final_df


def get_winners_list(tickers:list[str], credentials=Credentials(), top:int=3, days:int = 365, windows_in_days:list[int] = [7, 30, 90, 365], verbose:bool=False) -> str:
    """Print the winners 

    Args:
        tickers (list[str]): List of tickers.
        credentials (Credentials): Credentials for proxy connection
        top (int, optional): Top tickers to print the info for. Defaults to 3.
        days (int, optional): Max window of days for the stocks. Defaults to 365.
        windows_in_days (list[int], optional): _description_. Defaults to [7, 30, 365].
        verbose (bool): Print statements.
    
    Returns:
        str: JSON String 
    """
    # Getting the merged df
    verbose and print("Getting all tickers...")
    merged_df = get_merged_df(tickers, credentials, days, windows_in_days, verbose)
    print(merged_df.head())
    # Getting the winners
    winners = {}
    for index in merged_df.index:
        w = merged_df.loc[index].apply(lambda x: abs(x)).sort_values(ascending=False).iloc[0:top].index.values
        winners[index] = list(w)
    
    # Printing the winners
    output = dict()
    for index, row in merged_df.iterrows():
        output_date = dict()
        tickers_info = dict()
        for ticker in winners[index]:
            tickers_info[ticker] = f"{row[ticker]*100:.2f}%"
        days_ago = f"{(datetime.today()-index).days}"
        date_of_reference = f"{index.date().strftime('%Y-%m-%d')}"
        output_date["date"] = date_of_reference 
        output_date["tickers_info"] = tickers_info
        output[days_ago]=output_date
    
    return json.dumps(output)





