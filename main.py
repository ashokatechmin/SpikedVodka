"""
Puts together the 'FB automation' & 'email verification' modules and runs the combined program

@author: Adhiraj Singh

"""
import json
import time
import signal
from sys import argv
from fb_automation import create_browser, handle_requests
from verification import Verifier

def load_json (filename: str):
    """ loads a JSON stored at given file """
    with open (filename, "r") as f:
        data = f.read ()
    return json.loads (data)
def close_browser (signum, frame):
    browser.quit ()
    exit (0)

config_file = argv[-1] # argument to know where the configuration file is

config = load_json (config_file) # load the config (credentials and all)
verifier = Verifier (config) # fetches emails, generates codes & validates requests
print (f"registered emails: {len(verifier.data)}, accepted emails: {len(verifier.data)}")

browser = create_browser (argv[-2] == "gui") # create an instance of a browser
signal.signal (signal.SIGINT, close_browser) # close on keyboard interrupt (ctrl + c)

# loop forever & accept requests
while True:
    try:
        print ("fetching emails...")
        verifier.fetch ()

        print ("responding to FB requests...")
        handle_requests (browser, config["fb"], lambda name, answer : verifier.validate(name, answer))
    except Exception as error:
        print (f"exception in cycle: {error}")

    time.sleep (1*60 + 30) # wait a few minutes before restarting the cycle

    
    

