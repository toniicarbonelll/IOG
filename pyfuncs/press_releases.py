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
import re
from credentials import Credentials
import json
import undetected_chromedriver as uc



def date_to_month(date:str)->str:
    """Extracting the month from the yahoo finance date

    Args:
        date (str): Yahoo finance date (ex: 11d ago, 1mo ago...)

    Returns:
        str: Month
    """
    mapping = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July',
               8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    date = date.split(" ")[0] #11d, 1mo...
    timeframe = re.findall(r"[a-zA-Z]+", date)[0] #extracting the timeframe (d or mo)
    number = int(re.findall(r"\d+", date)[0]) #extracting the number
    if timeframe != "mo":
        number = 0 #0 because n months have past
    month =  (datetime.today() - pd.Timedelta(days=30*number)).month
    return mapping[month]
    


def date_to_days_ago(date:str)->str:
    """Extracting the total number of days ago from the yahoo finance date

    Args:
        date (str): Yahoo finance date (ex: 11d ago, 1mo ago...)

    Returns:
        str: Total days ago
    """
    date = date.split(" ")[0] #11d, 1mo...
    timeframe = re.findall(r"[a-zA-Z]+", date)[0] #extracting the timeframe (d or mo)
    number = int(re.findall(r"\d+", date)[0]) #extracting the number
    days = number if timeframe!="mo" else 0
    months = 0 if timeframe!="mo" else number
    return 30*months + days
    

def check_valid_title(title:str, company:str)->bool:
    """Checks if a title is valid for the article to be interesting

    Args:
        title (str): Title
        company (str): Name of the company

    Returns:
        bool: Result
    """
    return company.lower() in title.lower()


def filter_by_title(df:pd.DataFrame, company:str) -> pd.DataFrame:
    """Filters the resulting df by the ones whose title is relevant

    Args:
        df (pd.DataFrame): Output of get_press_releases()
        company (str): Company name

    Returns:
        pd.DataFrame: Resulting df
    """
    df['is_valid'] = df['title'].apply(lambda x: check_valid_title(x, company))
    df = df[df['is_valid']]
    return df.drop(columns=['is_valid'])


def get_press_releases_df(driver, ticker: str, credentials: Credentials = Credentials(), verbose:bool = False) -> pd.DataFrame:
    """Gets a dataframe with the press releases dates, title and url for a ticker.

    Args:
        driver (driver): Driver
        ticker (str): ticker name
        credentials (Credentials, optional): Credentials for proxy connection. Defaults to Credentials().
        verbose (bool, optional): Print statements. Defaults to False.

    Returns:
        pd.DataFrame: Resulting DataFrame
    """

    # Ir a la url
    url = f"https://finance.yahoo.com/quote/{ticker}/press-releases"
    driver.get(url)

    # 1. Click "ir al final" button
    ir_al_final = driver.find_element(by=By.ID, value="scroll-down-btn")
    ir_al_final.click()

    # 2. Rechazar todo
    verbose and print("Rejecting cookies...")
    rechazar_todo_container = driver.find_element(by=By.CSS_SELECTOR, value=".actions.couple")
    rechazar_todo = rechazar_todo_container.find_element(by=By.CSS_SELECTOR, value=".btn.secondary.reject-all")
    rechazar_todo.click()

    # Wait until we have the news articles table
    scrollable = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".stream-items"))
    )

    # Get the company name
    company = driver.find_element(by=By.CSS_SELECTOR, value=".yf-4vbjci").text.split(" ")[0]
    company = re.split(r"[.,]", company)[0]

    # 3. Scroll down infinitely --> Bastante cutre pero funciona
    verbose and print("Scrolling down!")
    for i in range(100): #get the last one and go to the last one, do 100 times
        news_block = driver.find_element(by=By.CSS_SELECTOR, value=".stream-items")
        news_containers = news_block.find_elements(by=By.CSS_SELECTOR, value=".content.yf-lfbf5f")
        driver.execute_script("arguments[0].scrollIntoView();", news_containers[-1])


    # 4. Get all news articles
    verbose and print("Getting all news articles info...")
    titles = []
    urls = []
    dates = []
    news_block = driver.find_element(by=By.CSS_SELECTOR, value=".stream-items")
    news_containers = news_block.find_elements(by=By.CSS_SELECTOR, value=".content.yf-lfbf5f")
    for news_container in news_containers:
        title = news_container.find_element(by=By.TAG_NAME, value="a").text
        url = news_container.find_element(by=By.TAG_NAME, value="a").get_attribute("href")
        date = news_container.find_element(by=By.CSS_SELECTOR, value=".publishing.yf-m1e6lz").text.split("•")[-1].strip()
        titles.append(title)
        dates.append(date)
        urls.append(url)

    # Return DataFrame
    df = pd.DataFrame({
        'title': titles,
        'url': urls,
        'date': dates
    })

    df["month"] = df["date"].apply(date_to_month)
    df["days_ago"] = df["date"].apply(date_to_days_ago)
    df = filter_by_title(df, company)
    
    return df


def df_to_json(df: pd.DataFrame) -> str:
    """Turns the resulting DataFrame into a JSON, selecting 10 news articles for each month

    Args:
        df (pd.DataFrame): Output of get_press_releases_df()

    Returns:
        str: JSON STRING with total_rows and months:dict() with [title, url] for 10 random articles for every month
    """
    json_dict = dict() #json final dictionary
    months = {month:[] for month in df['month'].unique()} #initializing the months dictionary 
    json_dict['total_rows'] = df.shape[0] #getting the total number of urls
    for month in df['month'].unique():
        df_month = df[df['month']==month] #getting the rows for month
        # getting a random permutation of the months and select 10
        idxes = np.array(df_month.index) 
        idxes = list(np.random.permutation(idxes))[0:5] 
        df_month = df_month.loc[idxes]
        # fill the months dictionnary
        for index, row in df_month.iterrows():
            months[month].append([row['title'], row['url']])
    json_dict['months'] = months
    return json.dumps(json_dict)


def start_driver_undetected(driver_path:str, credentials = Credentials(), verbose: bool=False):
        # Use webdriver_manager to automatically manage driver (optional)
        verbose and print("loading driver...")
        options = uc.ChromeOptions()
        options.add_argument(f'--proxy-server={credentials.proxy_server}')
        options.add_argument("--start-maximized")
        driver = uc.Chrome(driver_executable_path=driver_path, options=options)
        return driver

def start_driver(credentials = Credentials(), headless:bool=True, verbose: bool=False):
        # Use webdriver_manager to automatically manage driver (optional)
        verbose and print("installing driver...")
        os.environ["http_proxy"] = credentials.http_proxy
        os.environ["https_proxy"] = credentials.https_proxy
        service = Service(ChromeDriverManager().install())

        # removing to start
        del os.environ["http_proxy"]
        del os.environ["https_proxy"]
        options = Options()
        options.add_argument(f'--proxy-server={credentials.proxy_server}')
        if headless:
            options.add_argument('--headless')
        driver = webdriver.Chrome(service=service, options=options)
        return driver


def get_article(driver, url:str, close_cookies:bool, credentials = Credentials(), verbose:bool=False) -> str:
    """Given an article url of Yahoo Finance, it stores it text into a txt file on the 'articles' folder

    Args:
        driver (driver): Driver for scrapping. It needs to already have started.
        url (str): Yahoo Finance press url
        close_cookies (bool): Whether you have to close the cookies of the page
        credentials (Credentials): Credentials for proxy connection. Defaults to Credentials().
        verbose (bool): Print statements. Defaults to True.
    
    Returns:
        str: Article info
    """

    # Ir a la url
    driver.get(url)

    if close_cookies:
        # 1. Click "ir al final" button
        ir_al_final = driver.find_element(by=By.ID, value="scroll-down-btn")
        ir_al_final.click()

        # 2. Rechazar todo
        verbose and print("Rejecting cookies...")
        rechazar_todo_container = driver.find_element(by=By.CSS_SELECTOR, value=".actions.couple")
        rechazar_todo = rechazar_todo_container.find_element(by=By.CSS_SELECTOR, value=".btn.secondary.reject-all")
        rechazar_todo.click()

    # 3. Get all paragraphs and write them on a file
    # Wait until we have the news articles table
    article = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "article"))
    )
    paragraphs = article.find_elements(by=By.TAG_NAME, value="p")
    final_string = []
    for p in paragraphs:
        final_string.append(p.text)
    article =  " ".join(final_string).strip()
    return re.sub(r'[\\\".\n]', '', article).strip() # removing unwanted characters

def get_articles_batch(driver, urls:list[str], credentials:Credentials=Credentials(), verbose:bool=True) -> list[str]:
    """Get a batch of 10 scrapped articles from a list of 10 URLS

    Args:
        driver (driver): Driver
        urls (list[str]): List of press releases urls
        credentials (Credentials, optional): Credentials for proxy connection. Defaults to Credentials().
        verbose (bool, optional): Print statements. Defaults to True.

    Returns:
        list[str]: Batch of 10 articles scrapped
    """
    batch = []
    verbose and print(f"Scrapping article {1}: {urls[0]}")
    batch.append(get_article(driver, urls[0], close_cookies=True))
    for i, url in enumerate(urls[1:]):
        verbose and print(f"Scrapping article {i+2}: {url}")
        batch.append(get_article(driver, url, close_cookies=False))
    return batch