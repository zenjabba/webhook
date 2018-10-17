#!/usr/bin/env python3

from flask import Flask, request, abort
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import json
import requests
import urllib

def acknowledgeIPN(data):
	
   VERIFY_URL_PROD = 'https://ipnpb.paypal.com/cgi-bin/webscr'
   VERIFY_URL_TEST = 'https://ipnpb.sandbox.paypal.com/cgi-bin/webscr'

   # Switch as appropriate
   VERIFY_URL = VERIFY_URL_PROD
   payload = data.to_dict()
   payload['cmd'] = '_notify-validate'
   print(payload)
   r = requests.post(VERIFY_URL,headers={'content-type': 'application/x-www-form-urlencoded',
           'user-agent': 'Python-IPN-Verification-Script'},params=payload,verify=True)
   if(r.text == 'VERIFIED'):
        print("Acknowledged IPN Successfully!")
   elif r.text == 'INVALID':
        print("Did not acknowledge IPN Successfully!")
   else:
        print(r.text)

def authorize():
    # Authorize user using OAUTH2
    SCOPES = 'https://www.googleapis.com/auth/admin.directory.user'

    #Create local token.json for storing credentials after authorization
    store = file.Storage('token.json')
    creds = store.get()

    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)

    service = build('admin', 'directory_v1', http=creds.authorize(Http()))
    return service

def addUser(userData):
    # Create user GCE credentials given details

    # Normal arguments:
    # userData --- Multidict of user data needed for request


    body = {
            "name": {
            "familyName": userData['last_name'],
            "givenName": userData['first_name'],
            "fullName": userData['first_name'] + userData['last_name']
          },
          "password": "zendrive1!",
          "changePasswordAtNextLogin": True,
          "ipWhiteListed": False,
          "primaryEmail": "{}.{}@myonlinebackup.org".format(userData['first_name'],userData['last_name']),
          "emails": [
            {
              "address": userData['payer_email'],
              "type": "home",
              "customType": "",
              "primary": True
            }
          ],
          "orgUnitPath": "/zendrive"
  }

    authorizedUser = authorize()
    response = authorizedUser.users().insert(body=body).execute()
    print(response)


def getUserDetails(body):
    #Given the raw IPN, extract user details and return as a dictionary from paypal webhook

    # Normal arguments:
    # body --- Multidict of body from paypal
    # wantedFields --- List of desired fields for a valid user
    output = {}
    for field in wantedFields:
        if field in body:
            output[field] = body[field]

    print("Returning {}".format(output))
    return output


def validateAddUserFields(user, wantedFields):
    # Given a user dictionary, verify all required fields are present before attempting to add

    # Normal arguments:
    # user --- Dictionary containing user data
    # wantedFields --- List of desired fields for a valid user
    for field in wantedFields:
        if field not in user:
            return False
    return True


app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print("Received {}".format(request.form))
        acknowledgeIPN(request.form)
        wantedFields = ['first_name', 'last_name', 'payer_email', 'subscr_id']
        user = getUserDetails(request.form, wantedFields)

        # Check for presence of all the required fields for adding user
        if (validateAddUserFields(user, wantedFields)):
            addUser(user)
        return '', 200
    #else:
    #    abort(400)


if __name__ == '__main__':
    app.run()
