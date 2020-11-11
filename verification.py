"""

@author: Adhiraj Singh

"""
import json
import time
import re
import csv
from aes import encrypt, decrypt
from gmail_utils import get_gmail_service, gmail_fetch, extract_relevant, extract_name_email, send_reply, read_email, send_email

def read_column_of_csv (file, column):
    with open (file) as csv_file:
        reader = csv.DictReader (csv_file)
        rows = [ row[column] for row in reader ]
        return rows
    return []

'''
    To ensure that one person can use their email only once to validate a code, we store their emails in a set. 
    Then, we check if the set contains the email trying to validate, if it does validation fails
'''
class Verifier:
    """ 
        Class that can fetch emails, verify the sender, generate validation codes & validate requests.    
    """
    
    def __init__ (self, config: dict):
        self.encryption_key = config["encryption_key"] # key used to sign the codes
        self.subject_q = config["email_subject"].lower () # the subject that the emails should have
        self.subject_accept = config["accepted_email_subject"]
        self.email_regex = re.compile(config["valid_email_regex"]) # regex to validate an email address
        self.responses = config['responses']

        if "valid_email_list" in config:
            opts = config["valid_email_list"]
            valids = read_column_of_csv(opts["file"], opts["column"])
            self.valid_emails_list = set( filter (lambda x: len(x) > 0, valids) )
            print (f"read {len(self.valid_emails_list)} valid emails in list")
        self.last_fetch = None # when was the last fetch

        self.service = get_gmail_service (config["client_secret"], config["access_token"]) # gmail service
    
    def fetch (self):
        """ Fetch & respond to valid emails """
        # query to fetch the right emails
        q = "is:unread subject:" + self.subject_q.replace (" ", "+") + (" after:" + str(self.last_fetch) if self.last_fetch else "")
        messages = gmail_fetch (self.service, q) # fetch the emails
        self.last_fetch = int (time.time())-5 # refresh last fetch time, subtract five to account for emails received during the fetch

        print (f"got {len(messages)} emails")
        for message in messages:
            if message['subject'].lower() != self.subject_q: # if the subject does not strictly match, ignore the email
                continue 

            name, email = extract_name_email (message['from']) # extract the email from the RF-2822 format (name <email@mail.com>)

            if not self.is_valid_email (email): # if the email is not valid, respond accordingly
                print (email + ', invalid address')
                txt = self.responses['invalid_email']
            elif self.has_sent_acceptance_email(email): # if the email has already been validated, its a duplicate request
                print (email + ', got duplicate email')
                txt = self.responses['duplicate_email']
            else: # all good, otherwise
                print (email + ' requested to join, sending code')
                
                code = encrypt (email, self.encryption_key)
                txt: str = self.responses['valid_email']
                txt = txt.replace('[code]', code)

            txt = (self.responses.get('wrapper') or '[content]').replace('[content]', txt)
            txt = txt.replace('[name]', name)
            
            read_email (self.service, message['id']) # mark the email read
            send_reply (self.service, txt, message) # reply
    def has_sent_acceptance_email (self, email: str):
        m = gmail_fetch (self.service, f'is:sent to:{email} subject:{self.subject_accept.replace (" ", "+")}') 
        return len(m) > 0
    def send_acceptance_email (self, email: str, fbName: str):
        subject = self.subject_accept
        text = self.responses['accept_email']
        text = self.responses['wrapper'].replace('[content]', text)
        text = text.replace('[name]', fbName)
        
        send_email(self.service, email, subject, text)

    def is_valid_email (self, email):
        """ Check if the email is valid"""    
        return self.email_regex.match (email.lower()) != None or (email.lower() in self.valid_emails_list)

    def validate (self, name: str, answer: str):
        """ Verify if the answer is a valid code """
        if not answer:
            return
            
        code = answer.replace ("\n", "").replace (" ", "") # remove whitespace
        try:
            code = decrypt (code, self.encryption_key) # decrypt the code
        except Exception as err:
            print (f"{name} decryption failed for '{code}': {err}") # if decryption failed, then just fail
            return False
        if not self.is_valid_email (code): # if the code is not a valid email, fail
            print (f"{name} email validation failed for '{code}'") 
            return False
        if self.has_sent_acceptance_email(code): # if the code has already been used for validation, fail
            print (f"{name} sent duplicate code: '{code}'") 
            return False
        print (f"{name} successful authentication: '{code}'")
        self.send_acceptance_email(code, name)
        return True
def test_email_verification (verifier):
    """ Small unit test to verify the email regex works for Ashoka """
    def is_valid_email (email):
        return verifier.is_valid_email (email)
    assert is_valid_email ("adhiraj.singh_ug21@ashoka.edu.in")
    assert is_valid_email ("adhiraj.singh_asp20@ashoka.edu.in")
    assert is_valid_email ("adhiraj.a123_asp42@ashoka.edu.in")
    assert not is_valid_email ("adhiraj.singh_yif21@ashoka.edu.in")
    assert not is_valid_email ("adhirajsingh@gmail.com")
    assert not is_valid_email ("ahbkahdadkqdkj")
    assert is_valid_email ("adhiraj1.singh123_ug24@ashoka.edu.in")
    assert not is_valid_email ("adhiraj1.singh123_phd24@ashoka.edu.in")
    assert not is_valid_email ("adhiraj1.singh123_phd24_ug21@ashoka.edu.in")
    assert is_valid_email ("somename_ug20@ashoka.edu.in")
    assert is_valid_email ("shruthisagar@alumni.ashoka.edu.in")
    assert is_valid_email ("aaditya.shetty@alumni.ashoka.edu.in")
    assert not is_valid_email ("adhiraj1.singh123@alumni2.ashoka.edu.in")
if __name__ == "__main__":
    with open ("./config/config.json", "r") as f:
        data = f.read ()
        config = json.loads (data)
        verifier = Verifier(config)
        test_email_verification (verifier)
        