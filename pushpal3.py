#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import socket
import sys
import datetime

# https://github.com/jcarbaugh/python-roku
from roku import Roku

import logging
from logging.handlers import RotatingFileHandler

import sendgrid
import os
from sendgrid.helpers.mail import *

import json

secretsFileName = '/home/pi/secrets.json'
with open(secretsFileName) as file:
    data = json.load(file)
sg = sendgrid.SendGridAPIClient(api_key=data['secrets'][0]['SENDGRID_API_KEY'])

TvServerConnectionAttempts = 4;

LogFilename='/home/pi/Desktop/pushpal.log'
# Create Rotating Logger
logger = logging.getLogger("Rotating Log")

BtnPin = 18
LedPin = 17

Led_status = 1
Led_status_changed = 0

##########################################
# Chose one of these Messages to set
##########################################
# Samsung TVs in my office - turn on/off:
# Message = 'sendir,1:2,1,37878,1,1,171,171,21,64,21,64,21,64,21,22,21,22,21,22,21,22,21,22,21,64,21,64,21,64,21,22,21,22,21,22,21,22,21,22,21,22,21,64,21,22,21,22,21,22,21,22,21,22,21,22,21,64,21,22,21,64,21,64,21,64,21,64,21,64,21,64,21,1779\r\n'

# LG TV in Baa's room - turn on/off:
Message = 'sendir,1:2,1,37878,1,1,342,170,21,22,21,21,21,64,21,22,21,22,21,22,21,21,21,22,21,64,21,64,21,22,21,64,21,64,21,64,21,64,21,64,21,22,21,22,21,22,21,64,21,22,21,22,21,22,21,22,21,64,21,64,21,64,21,22,21,64,21,64,21,64,21,64,21,3700\r\n'
#
##########################################

# The Global Cache iTach server's hostname or IP address
GCHOST = '192.168.157.2'
# The Global Cache iTach port used by the server
GCPORT = 4998
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Set socket timeout to 1 second
sock.settimeout(5)
server_address = (GCHOST, GCPORT)

# Initialize Roku
ROKUHOST = '192.168.157.3' # Joy Network
#ROKUHOST = '192.168.2.51'  # Radhasoami Network
roku = Roku(ROKUHOST)
youtube = roku['YouTube']

def setup():
    global logger
    global LogFilename
    global BtnPin
    global LedPin
    global sg

    create_rotating_log(LogFilename)

    # Initialize the Raspberry Pi GPIO
    GPIO.setmode(GPIO.BCM)       # Numbers GPIOs by BCM
    GPIO.setup(LedPin, GPIO.OUT)   # Set LedPin's mode is output
    GPIO.setup(BtnPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)    # Set BtnPin's mode is input, and pull up to high level(3.3V)
    GPIO.output(LedPin, GPIO.HIGH) # Set LedPin high(+3.3V) to off led

    logger.info ('Starting up Pushpal.')
    now = datetime.datetime.now()
    logger.info ('Start date and time: %s' % now.strftime('%Y-%m-%d %H:%M:%S'))
    sendEmail()

def connectToTv():
    global logger
    global TvServerConnectionAttempts
    global sock
    global server_address

    # Initialize Global Cache iTach
    # Bind the socket to the port
    try:
        sock.connect(server_address)
        # Connected successfully to Global Cache iTach server
        # logger.info ("Connected to TV server successfully!")
        TvServerConnectionAttempts = 4
    except:
        # Could not connect to Global Cache iTach server
        if TvServerConnectionAttempts > 0:
            logger.debug ('Failed to connect to TV server.')

        TvServerConnectionAttempts-=1

def sendEmail():
    global logger
    global sg
    try:
        now = datetime.datetime.now()
        from_email = Email('amarppatel1@gmail.com')
        to_email = To('amarppatel1@gmail.com')
        subject = 'Pushpal Up and Running'
        content = Content('text/plain', 'Pushpal started on ' + now.strftime('%Y-%m-%d %H:%M:%S') + '. You can now turn on the TV.')
        mail = Mail(from_email, to_email, subject, content)
        response = sg.client.mail.send.post(request_body=mail.get())
        logger.info('System ready email sent.')
        logger.debug('Email response status code: ' + str(response.status_code))
    except Exception as inst:
        logger.error('Problem occurred while trying to send email: ' + type(inst) + ' | ' + inst)

def swLed(ev=None):
    global logger
    global Led_status
    global Led_status_changed
    global LedPin

    Led_status = not Led_status
    Led_status_changed = 1
    GPIO.output(LedPin, Led_status)  # switch led status(on-->off; off-->on)

    if Led_status == 1:
        logger.debug ('led off...')
    else:
        logger.info ('++++++++++++++++++++++++++++++++++++++++++++++')
        now = datetime.datetime.now()
        logger.info ('LED is on at date and time: %s' % now.strftime('%Y-%m-%d %H:%M:%S'))
        logger.debug ('...led on')

def loop():
    global logger
    global Led_status
    global Led_status_changed
    global BtnPin
    global sock
    global roku
    global youtube
    global Message

    # Wait for falling and set bouncetime to prevent the callback
    # function from being called multiple times when the button is
    #pressed
    GPIO.add_event_detect(BtnPin, GPIO.FALLING, callback=swLed, bouncetime=40000)

    while True:
        connectToTv()

        if Led_status_changed == 1:
            if Led_status == 1:
                # LED is off
                logger.info ('LED is off!')
                logger.info ('Switch Roku back to Home screen...')
                roku.back()
                time.sleep(5)
                roku.back()
                time.sleep(2)
                roku.back()
                time.sleep(2)
                roku.down()
                time.sleep(2)
                roku.select()
                time.sleep(5)
                #roku.home()
                logger.info ('Sleeping for 5 seconds')
                time.sleep(5)
                # Send data
                try:
                    logger.info ('Sending turn off TV command...')
                    sock.sendall(Message.encode('utf-8'))
                    logger.debug ('Message sent: %s' % Message)
                except:
                    logger.debug ('Could not turn TV off!')
                logger.info ('++++++++++++++++++++++++++++++++++++++++++++++\n')
            else:
                # LED is on
                logger.info ('LED is on!')
                logger.info ('Sending turn on TV command...')
                try:
                    sock.sendall(Message.encode('utf-8'))
                except:
                    logger.debug ('Could not turn on TV!')
                logger.debug ('Message sent: %s' % Message)
                logger.info ('Sleeping for 10 seconds...')
                time.sleep(10)
                logger.info ('Launching YouTube application...')
                youtube.launch()
                logger.info ('Another nap, this time for 20 seconds...')
                time.sleep(20)
                logger.info ('Select the default video to play or select the default user')
                roku.select()
                # Double-selecting if video is already playing
                # Single-selecting if user selection prompt appears
                logger.info ('Sleep for 5 more seconds while video plays')
                time.sleep(5)
                logger.info ('Select whatever is in focus')
                roku.select()
            # Reset the Led_status_changed flag
            Led_status_changed = 0
        time.sleep(1)   # Don't do anything

def destroy():
    global sock
    global LedPin

    GPIO.output(LedPin, GPIO.HIGH)     # led off
    GPIO.cleanup()                     # Release resource
    sock.close()

def create_rotating_log(path):
    global logger

    # Set log level
    logger.setLevel(logging.DEBUG)

    # Add a rotating handler
    handler = RotatingFileHandler(path, maxBytes=5000, backupCount=3)

    logger.addHandler(handler)

if __name__ == '__main__':     # Program start from here

    setup()
    try:
        loop()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        logger.info ('Ended Pushpal process')
        destroy()