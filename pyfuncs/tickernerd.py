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
import sys
sys.path.append(os.path.abspath("C:/Users/A200348545/Escritorio 2/Personal-Projects/IOG"))
sys.path.append(os.path.abspath("C:/Users/A200348545/Escritorio 2/Personal-Projects/IOG/pyfuncs"))
from credentials import Credentials
from press_releases import start_driver

def tickernerd(driver, ticker: str) -> str:
    """Gets scrapped information from tickernerd 

    Args:
        driver (driver): Started driver...
        ticker (str): Name of ticker

    Returns:
        [str, str]: Scrapped information 
    """

    ticker = ticker.lower()
    url = f"https://tickernerd.com/stock/{ticker}-forecast/"
    
    try: # Check if we have a 404 error
        driver.get(url)
        error = driver.find_element(by=By.CSS_SELECTOR, value=".error404")

    except:
        print("Ticker found!")
        # 1. Scrolling down a tiny bit (no)

        # 2. Closing the pop-up
        # if not headless:
        #     popup = WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, ".dialog-widget-content.dialog-lightbox-widget-content.animated"))
        #         )
        #     close_button = popup.find_element(by=By.TAG_NAME, value="a")
        #     close_button.click()

        # 3. Get the analyst ratings description
        analyst_ratings = driver.find_element(by=By.ID, value="analyst-ratings")
        paragraphs = analyst_ratings.find_elements(by=By.TAG_NAME, value="p")[0:2]
        output_text = []
        for paragraph in paragraphs:
            output_text.append(paragraph.text)
        output_text = " ".join(output_text)

        # 4. Get the company summary
        company_details = driver.find_element(by=By.CLASS_NAME, value="stock-forecast-company-details")
        paragraphs = company_details.find_elements(by=By.TAG_NAME, value="p")
        company_summary = paragraphs[1].text
        #print(company_summary)

        # 5. Get the price chart
        price_chart = driver.find_element(by=By.ID, value="price-chart")
        title = driver.find_element(by=By.CSS_SELECTOR, value='.text-xl.font-bold') #scrolling to get a clean screenshot
        driver.execute_script("arguments[0].scrollIntoView();", title) #scrolling to get a clean screenshot
        time.sleep(0.5)
        price_chart = driver.find_element(by=By.ID, value="priceChart") #getting the chart
        price_chart.screenshot('priceChart.jpg') #screenshotting the chart
        driver.quit()

        # combining outputs:
        return [output_text, company_summary]

    else:
        print("Error 404...")
        return ["No results found for your ticker (Error 404...)","No results found for your ticker (Error 404...)"]
    
    

def danelfin(driver, ticker:str) -> str:
    """Gets scrapped information from danelfin with UNDETECTED_CHROMEDRIVER driver

    Args:
        driver (driver): Started driver. NEEDS A UNDETECTED_CHROMEDRIVER DRIVER!!
        ticker (str): Name of ticker
        headless (bool): Headless driver or not

    Returns:
        str: Scrapped information 
    """
    url = f"https://danelfin.com/stock/{ticker}"
    headless = False #hardcoded

    try: # Check if we have a 404 error
        driver.get(url)
        error = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".robot_404")))

    except:
        print("Ticker found!")
        # 1. Scrolling down a tiny bit (no)
        
        # 2. Closing the pop-up
        if not headless:
            popup = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME,"didomi-popup-view"))
                )
            rechazar = popup.find_element(by=By.ID, value="didomi-notice-disagree-button")
            rechazar.click()

        # 3. Closing the other one
        #close_button = WebDriverWait(driver, 10).until(
        #EC.presence_of_element_located((By.CSS_SELECTOR,".closeBtn")))
        #close_button.click()

        # 3. Get the analyst ratings description
        analyst_ratings = driver.find_element(by=By.CLASS_NAME, value="TickerAiAnalysis_scoreWrapper__9seDN")
        output_text = analyst_ratings.find_element(by=By.TAG_NAME, value="p").text
        driver.quit()
        return output_text

    else:
        print("Error 404...")
        driver.quit()
        return ["No results found for your ticker (Error 404...)","No results found for your ticker (Error 404...)"]
