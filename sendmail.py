#!/usr/bin/env python3

import datetime
import logging

import sendgrid
import os
from sendgrid.helpers.mail import *

import json

# Create Rotating Logger
logger = logging.getLogger().addHandler(logging.StreamHandler())
now = datetime.datetime.now()
secretsFileName = '/home/pi/secrets.json'
with open(secretsFileName) as file:
    data = json.load(file)
sg = sendgrid.SendGridAPIClient(api_key=data['secrets'][0]['SENDGRID_API_KEY'])
from_email = Email('amarppatel1@gmail.com')
to_email = To('amarppatel1@gmail.com')
subject = 'Pushpal Up and Running'
content = Content('text/plain', 'Pushpal started on ' + now.strftime('%Y-%m-%d %H:%M:%S') + '. You can now turn on the TV.')
mail = Mail(from_email, to_email, subject, content)
response = sg.client.mail.send.post(request_body=mail.get())
logger.info('System ready email sent.')
logger.debug('Email response status code: ' + str(response.status_code))