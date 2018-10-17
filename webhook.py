#!/usr/bin/env python3

from werkzeug.datastructures import ImmutableMultiDict
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
   VERIFY_URL = VERIFY_URL_TEST
   print(data.to_dict())   
   r = requests.post(VERIFY_URL,headers={'content-type': 'application/x-www-form-urlencoded',
           'user-agent': 'Python-IPN-Verification-Script'},data=data.to_dict(),verify=True)
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
          "password": "",
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
          "externalIds": [
            {
              "value": userData['subscriber_id'],
              "type": "organization"
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
    #     body --- Multidict of body from paypal

    output = {}
        # print("First Name: {}".format(body['first_name']))
    # print("Last Name: {}".format(body['last_name']))
    # print("Email: {}".format(body['payer_email']))
    # print("Subscriber ID: {}".format(body['subscr_id']))
    output['first_name'] = body['first_name']
    output['last_name'] = body['last_name']
    output['payer_email'] = body['payer_email']
    output['subscriber_id'] = body['subscr_id']
    print("Returning {}".format(output))
    return output



app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        # print("Received {}".format(request.form))
	acknowledgeIPN(request.form)
	user = getUserDetails(request.form)
        addUser(user)
        return '', 200
    else:
        abort(400)


if __name__ == '__main__':
    app.run()
