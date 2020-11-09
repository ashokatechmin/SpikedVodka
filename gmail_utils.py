"""
App specific wrapper around the GMail API
@author: Adhiraj Singh

"""
import pickle
import os
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def get_gmail_service (client_secret_file: str, access_token_file: str):
    """ Authenticate with GMail. Most of the code from https://developers.google.com/gmail/api/quickstart/python """

    SCOPES = ['https://mail.google.com/']
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(access_token_file):
        with open(access_token_file, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=8000)
        # Save the credentials for the next run
        with open(access_token_file, 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)
def read_email (service, mID: str):
    """ Mark an email read """
    service.users().messages().modify(userId='me', id=mID, body={"removeLabelIds": ['UNREAD']}).execute()
def gmail_fetch (service, q: str):
    """ Fetch all emails fitting the query """
    results = service.users().messages().list(userId='me', q=q, includeSpamTrash=True).execute()
    messageIDs = results.get('messages', [])

    messages = []
    for mID in messageIDs:
        msg = service.users().messages().get(userId='me', id=mID['id']).execute()
        messages.append (extract_relevant(msg)) # extract the relevant part & add to the list
    return messages
def extract_name_email (txt):
    """ 
        Extracts the name and email from RFC-2822 encoded email address.
        For eg. "Jeff Jeff <jeff.jeff@gmail.com>" returns ("Jeff Jeff", "jeff.jeff@gmail.com")
    """
    if "<" in txt and ">" in txt:
        name, email = txt.split("<")
        return name[:-1], email[:-1]
    elif "<" not in txt and ">" not in txt:
        return "", txt
    else:
        return None
def send_reply (service, text: str, meta: dict):
    """  Replies to an email with the given text """
    message = MIMEText (text)
    message['to'] = meta ['from']
    message['from'] = 'me'

    # see https://developers.google.com/gmail/api/v1/reference/users/messages/send for header specifications
    message['subject'] = meta['subject'] if 'Re:' in meta['subject'] else ('Re: ' + meta['subject']) # required headers (RFC-2822)
    message['in-reply-to'] = meta ['message-id'] # required headers
    message['references'] = meta ['message-id'] # required headers
    # encode as url safe base64
    raw_message = base64.urlsafe_b64encode(message.as_string().encode("utf-8")).decode('utf-8')
    # mention thread Id to save as reply
    service.users().messages().send(userId='me', body={'raw': raw_message, 'thread_id': meta["thread_id"]}).execute()

def extract_relevant (msg):
    """ Extracts relevant (to the app) headers & info from a GMail message """
    headers_to_extract = set (["subject", "from", "message-id"])
    headers = msg["payload"]["headers"]
    
    data = dict ()
    data ["id"] = msg ["id"]
    data ["thread_id"] = msg ["threadId"]
    for header in headers:
        name = header["name"].lower()
        if name in headers_to_extract:
            data [name] = header ["value"]
    return data