from __future__ import print_function
import base64
from email import errors
from email.mime import base
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os.path
import threading
from unittest import result
from xmlrpc.client import _iso8601_format
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import timedelta
from dateutil import parser
import time
import re
from marketgets import *
from constants import *
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://mail.google.com/']

# These are private constants in a seperate file
#SENDER = EMAIL 
#SENDERNAME = NAME OF PERSON

#from marketgets import getstockprice
lastprice = 0


# Creating gmail messages
def create_message(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEMultipart()
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  message.attach(MIMEText(message_text, 'plain'))
  return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
#sending message
def send_message(service, user_id, message):
    """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print ('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print ('An error occurred: %s' % error)

# reads mail that contains symbol and price
def readAlarm(decoded_data):
    alarm = re.search(r'(Crypto)? ?([\w]+) *(\d+.?\d+) (above|below)', str(decoded_data[0])) # regex parsing of content from email
    price = None
    symbol = None
    crypto = False
    above = None
    try:
        if (alarm.group(1)) == "Crypto":
            symbol = alarm.group(2)
            price = alarm.group(3)
            above = alarm.group(4)
            crypto = True
        else:
            symbol = alarm.group(1)
            price = alarm.group(2)
            above = alarm.group(3)
            crypto = False
        if above == "above":
            above = True
        else:
            above = False
    except AttributeError as error:
        print(f'An error occurred: {error}' + " AKA No Price or Symbol in Message")
    return symbol, price, above, crypto

def returnMsg(service, senderName, email, date = "0-0-0"):
    #the only site that explained this
    #https://www.geeksforgeeks.org/how-to-read-emails-from-gmail-using-gmail-api-in-python/
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages')
    latestmessage = []
    subject = ''
    sender = ''
    timesent = ''
    done = False
    for msg in messages: # Parses the latest messages from inbox
        txt = service.users().messages().get(userId='me', id =msg['id']).execute()
        headers = txt['payload']['headers']
        for d in headers: #searching for email from a certain address
            if(d['name'] == 'Date' and date != "0-0-0" and parser.parse(d['value']).date() > datetime.strptime(date, '%Y-%m-%d').date()):# if the date is specific discard earlier date
                #print(parser.parse(d['value']).date().isoformat())
                sender = ''
                break
            #if d['name'] == 'Subject': # if you want to check the subject
            #    subject = d['value']
            if d['name'] == 'From':
                sender = d['value']
            if d['name'] == 'Date' and sender != '':
                if sender == "{} <{}>".format(senderName, email): # if the message is from a particular email address
                    latestmessage = txt
                    done = True
                    break
        if done:
            payload = latestmessage['payload']
            parts = payload.get('parts')[0]
            data = parts['body']['data']
            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data)
            return decoded_data, #returns body text in lxml
    return "read failed" # returns failure if it couldn't find a message from the sender

#starts the Gmail API
def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        return service
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')
    
def checkAlarm(service, symbol, price, above, alert):
    currprice = getstockprice(symbol)#askprice
    emailaction = False
    if above and price < currprice:
        #to stuff
        print("price above target")
        emailaction = True
    elif not above and price > currprice:
        print("below")
        emailaction = True
    else:
        print("not reached alarm")
        emailaction = False
    if emailaction and alert:
        message = create_message('me', SENDER, 'marketalert', symbol + " has crossed: $" + str(price) + " at: $" + str(currprice))
        send_message(service, 'me', message)
    return emailaction

def organizedict(dict):
    m = ""
    for key in dict:
        s = (key, dict[key])
        m += str(s) + "\n"
    return m

def checkCryptoAlarm(service, symbol, price, above, alert):
    symbol = str(symbol)
    price = float(price)
    currprice = getcryptoprice(symbol)#askprice
    emailaction = False
    if above and price < currprice:
        #to stuff
        print("price above target")
        emailaction = True
    elif not above and price > currprice:
        print("below")
        emailaction = True
    else:
        print("not reached alarm")
        emailaction = False
    if emailaction and alert:
        message = create_message('me', SENDER, 'marketalert', symbol + " has crossed: $" + str(price) + " at: $" + str(currprice) + "\n" + organizedict(getcryptoinfo(symbol))) 
        send_message(service, 'me', message)
    return emailaction

def checkingThread(name, service, symbol, price, above):
    print("Alarm {} Thread Started".format(name))
    price = float(price)
    symbol = str(symbol)
    emailaction = False
    thread.is_alive = True # alive by default
    while(not emailaction and thread.is_alive): # constantly check if thread is still alive
        print("checking alarm {}".format(name))
        emailaction = checkAlarm(service, symbol, price, above, True)
        time.sleep(1)
    print("Alarm {} Thread Stopped".format(name))
    

def checkingcryptoThread(name, service, symbol, price, above):
    print("Alarm {} Crypto Thread Started".format(name))
    price = float(price)
    symbol = str(symbol)
    print(symbol)
    print(price)
    above = bool(above)
    emailaction = False
    thread.is_alive = True
    while(not emailaction and thread.is_alive):
        print("checking crypto alarm {}".format(name))
        emailaction = checkCryptoAlarm(service, symbol, price, above, True)
        time.sleep(1)
    print("Alarm {} Crypto Thread Stopped".format(name))
    

if __name__ == '__main__':
    service = main()
    emailaction = True
    alarm1 = False
    alarm2 = False
    todayDate = datetime.now().date().isoformat()
    previousMail = readAlarm(returnMsg(service, SENDERNAME, SENDER, todayDate))
    index = 0
    thread = threading.Thread(target=checkingThread, args=(index, service, previousMail[0], previousMail[1], previousMail[2]), daemon= True)
    
    try:
        while(True):#replace with a datetime script or something
            mail = readAlarm(returnMsg(service, SENDERNAME, SENDER))
            if mail != previousMail:
                if mail[3] == True:
                    thread = threading.Thread(target=checkingcryptoThread, args=(index, service, mail[0], mail[1], mail[2]), daemon= True)
                    thread.start()
                else:
                    thread = threading.Thread(target=checkingThread, args=(index, service, mail[0], mail[1], mail[2]), daemon= True)
                    thread.start()
                previousMail = mail
                index = index + 1
            time.sleep(10)
            print("RUNNING")
    except KeyboardInterrupt:
        thread.is_alive = False # making thread not alive
        print("trying to kill the thread")
        thread.join(timeout= 100)
    print("STOPPED")