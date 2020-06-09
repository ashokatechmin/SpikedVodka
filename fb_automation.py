"""
Uses Selenium to access Facebook, open the url of a group & accept/reject requests

@author: Adhiraj Singh

"""
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from sys import platform
import json
import time

def create_browser (gui: bool=False):
    """ Create a browser instance & return it """
    
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    if not gui:
        options.add_argument('--headless') # comment this line for GUI
        options.add_argument('--disable-gpu') # comment this line for GUI
    prefs = {"profile.default_content_setting_values.notifications": 2}
    
    options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=options)
        

def fb_login (browser: webdriver.Chrome, config: dict):
    """ Login to Facebook; config["email"] & config["password"] must be set """
    browser.get(config['group_url'])

    element_present = EC.presence_of_element_located((By.ID, 'loginbutton'))
    WebDriverWait(browser, 5).until(element_present)

    # finding login input areas
    mail_element= browser.find_element_by_id('email')
    pwd_element = browser.find_element_by_id('pass')
    # filling login form
    mail_element.send_keys(config['email'])
    pwd_element.send_keys(config['password'])
    # login after one second
    time.sleep(1)
    submit_element = browser.find_element_by_id('loginbutton')
    submit_element.click()
def is_fb_logged_in (browser: webdriver.Chrome):
    """ Tries to locate the requests div, if it is found, then we're authenticated successfully """
    try:
        browser.find_element_by_id('member_requests_pagelet')
        return True
    except:
        return False
def view_requests (browser: webdriver.Chrome, config: dict):
    """ Returns the pending requests; ignores requests that have pending answers; config["group_url"] must be set """
    browser.get(config["group_url"]) # load the group url in the browser
    element_present = EC.presence_of_element_located((By.ID, 'member_requests_pagelet'))
    WebDriverWait(browser, 5).until(element_present)
    time.sleep (1)
    
    requests = list ()
   
    reqs_parent = browser.find_element_by_id('member_requests_pagelet') # find the requests container
    # the list of requests
    reqs_list = reqs_parent.find_elements_by_xpath (".//ul[contains(@class, 'uiList')]/child::li/div[contains(@class, 'clearfix')]//div[contains(@class, '_42ef')]")
    
    for element in reqs_list:
        name_element = element.find_element_by_xpath (".//a[contains(@class, '_z_3')]") # name of the person who has requested
        approve_button = element.find_element_by_name ("approve") # the approve button
        decline_button = element.find_element_by_name ("decline") # the decline button
        anchor = element.find_element_by_xpath (".//div[contains(@class, '_50f8')]") # element, when scrolled to makes the entire request visible
        try:
            ques = element.find_element_by_xpath (".//div[contains(text(), 'technology.ministry@')]") # the relevant question; TODO: put into config.json
            ans = ques.find_element_by_xpath ("./following-sibling::text").get_attribute("innerHTML") # answer to the question; innerHTML returns the text
        except Exception as err: # ignore this request if this answer is not present, as it might still be loading
            ans = None 
        # compile all this info
        obj = {
            "name": name_element.get_attribute("innerHTML"), 
            "answer": ans,
            "anchor": anchor,
            "approve": approve_button,
            "decline": decline_button
            }
        requests.append (obj)
    return requests

def handle_requests (browser: webdriver.Chrome, config: dict, validate):
    """
        Goes over all pending requests & based on the 'validate' function accepts/rejects them.
        Also, automatically re-logs in if logged out. 
        Parameters
        ----------
        config : dict
            The credentials & config. Requires config["email"], config["password"] and config["group_url"] to be set
        validate : lambda
            Function to validate the name & answer of the request, return True or False
    """
    browser.get(config["group_url"])
    if not is_fb_logged_in (browser): # log in if not already
        print ("[FB] not logged in, logging in...") 
        fb_login (browser, config)
    reqs = view_requests (browser, config) # view the pending requests
   
    print (f"[FB] got {len(reqs)} requests")

    for req in reqs:
        name = req["name"]
        
        ActionChains(browser).move_to_element(req["anchor"]).perform() # make approve button visible
        time.sleep (2) # sleep for a few seconds before any action
        
        validated = validate (name, req["answer"])
        if validated == True: # if validation succeeded, accept
            print (f"[FB] approving user: {name}")
            req["approve"].click ()
        elif validated == False: # decline otherwise
            print (f"[FB] rejecting user: {name}")
            req["decline"].click ()
        else: # ignore
            pass
