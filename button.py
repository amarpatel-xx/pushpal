#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

LedPin = 24
BtnPin = 23

LedStatus = 1

def setup():
	# Numbers GPIOs by BCM
	GPIO.setmode(GPIO.BCM)
	# Set BtnPin's mode as input, and pull up to high level(3.3V)
	# Button to GPIO BtnPin
	GPIO.setup(BtnPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	# Set LedPin high(+3.3V) to off led
	# LED to GPIO LedPin
	GPIO.setup(LedPin, GPIO.OUT)

def loop():
	flag = 0

	while True:
		button_state = GPIO.input(BtnPin)
		#print(button_state)
		if button_state == False:
			time.sleep(0.5)
			if flag == 0:
				flag = 1
			else:
				flag = 0

			if flag == 1:
				GPIO.output(LedPin, GPIO.HIGH)
			else:
				GPIO.output(LedPin, GPIO.LOW)
#		if button_state == False:
#			GPIO.output(LedPin, True)
#			print("Button Pressed...")
#			print("...LED on")
#			time.sleep(0.2)
#		else:
#			GPIO.output(LedPin, False)
#			print("Button Pressed...")
#			print("...LED off")

def destroy():
	# LED off
	GPIO.output(LedPin, GPIO.HIGH)
	# Release resource
	GPIO.cleanup()

if __name__ == '__main__':	# Program start from here
	setup()
	try:
		loop()
	# When 'Ctrl+C' is pressed, the child program destroy() will be 
	# executed
	except KeyboardInterrupt: 
		destroy()
