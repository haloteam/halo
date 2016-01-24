#!/usr/bin/env python
import httplib, urllib
import PCF8591 as ADC
import LCD1602 as LCD
import RPi.GPIO as GPIO
import time
import math
from Queue import Queue
from threading import Thread
import subprocess
import json
from datetime import datetime
import wit
from espeak import espeak
import random
from wit_test import start_wit, outputQueue
from multiprocessing import Process, Queue

class Halo:
    def __init__(self):
        self.THERMISTOR_PIN = 17
        self.GAS_SENSOR_PIN = 18
        self.BUZZ_PIN = 6
        self.H2O_PIN = 13
        self.wit_access_token = '5HO7GQT6GHYYBC4G2M5SPTCWXSNSEL4S'
        self.halo_lambda_save_url = 'https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo'
        self.save_data_queue = Queue(maxsize=0)

        self.wit_process = Process(target=start_wit, args=())
        self.wit_process.daemon = True
        self.wit_process.start()        # Launch reader() as a separate python process

        self.temperature = None
        self.gas = None
        self.h2o = None

        self.inConversation = False

        self.setup()
        self.start_conversation()

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        ADC.setup(0x48)
        LCD.init(0x27, 1)
        self.alert("System startup")
        GPIO.setup(self.THERMISTOR_PIN, GPIO.IN)
        GPIO.setup(self.GAS_SENSOR_PIN, GPIO.IN)
        GPIO.setup(self.BUZZ_PIN, GPIO.OUT)
        GPIO.setup(self.H2O_PIN, GPIO.IN)
        #wit.init()

    def begin_threads(self):
        save_data_worker = Thread(target=self.save_data_thread, args=())
        save_data_worker.setDaemon(True)
        save_data_worker.start()

    # be careful, may cause conflicts in runtime
    # params is tuple of parameters
    def run_func_in_background(self, func, params):
        if params is None:
            params = ()
        worker = Thread(target=func, args=params)
        worker.setDaemon(True)
        worker.start()


    def start(self):
        self.begin_threads()
        while True:
            self.get_temperature_sensor_data()
            self.get_gas_sensor_data()
            self.get_h2o_sensor_data()
            self.check_data()

    def check_data(self):
        if self.inConversation == False:
            if self.gas > 90:
                self.alert("GAS OVERLOAD")

    def alert(self, text):
        self.displayText(text)

    def speak(self, text):
        espeak.synth(text)

    def displayText(self, text):
	if len(text) < 16:
	    LCD.write(0,0,text)
	else:
	    while True:
		space = '      '
		tmp = space + text
		for i in range(0, len(text)):
		    LCD.write(0,0,tmp)
		    tmp = tmp[1:]
		    time.sleep(0.3)
		    LCD.clear()

    def get_temperature_sensor_data(self):
        analogTemp = ADC.read(0)
        Vr = 5 * float(analogTemp) / 255
        Rt = 10000 * Vr / (5 - Vr)
        temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15 + 25)))
        self.temp = (temp - 273.15) * 9/5 + 32
        return self.temp

    def get_gas_sensor_data(self):
        self.gas = ADC.read(1)
        return self.gas

    def get_h2o_sensor_data(self):
        self.h2o = ADC.read(2)
        return self.h2o

    def save_data_thread(self):
        while True:
            time.sleep(4)
            self.save_data_task()

    def save_data_task(self):
        updates = []
        updates.append({'type' : 'temperature', 'value': str(temp), 'timestamp': str(datetime.now())})
        updates.append({'type' : 'gas', 'value': str(ADC.read(1)), 'timestamp': str(datetime.now())})
        updates.append({'type' : 'rain', 'value': str(h2o), 'timestamp': str(datetime.now())})
        data = {}
        data['deviceId'] = 1;
        data['updates'] = updates
        data['action'] = "save"
        subprocess.call(['curl', '-X', 'POST', '-d', json.dumps(data), self.halo_lambda_save_url])


    def start_conversation(self):

        #conversation_starters = ["Hello", "How are you?", "Hi There", "I don't know you, but I like you.", "You are dashing in that Suit."]
        #espeak.synth(random.choice(conversation_starters))
        # user is prompted to talk
        print outputQueue.get()
        #speech_response = wit.voice_query_auto(self.wit_access_token)

        # response
        question = urllib.quote_plus(speech_response['_text'])
        resp = subprocess.call(['curl', 'https://www.houndify.com/textSearch?query=' + question + '&clientId=e7SgQJ_wwXjv5cUx1nLqKQ%3D%3D&clientKey=Pi_smrHYQhCA_nLgukp4C4nnQE2WyQvk3l3Bhs8hcbchrLAmjl5LWS3ewq1U8LMser8j890OfhklwNm77baPTw%3D%3D', '-H', 'Accept-Encoding: gzip, deflate, sdch', '-H', 'Accept-Language: en-US,en;q=0.8', '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36', '-H', 'Accept: */*', '-H', 'Referer: https://www.houndify.com/try/986dcfd1-0b91-4346-a5a0-6d53f0d18da2', '-H',
        'Cookie: houndify-sess=s%3Ar-94jGq48cQMay2q1fgRwSolHIV4ZQpk.Y3Wns0NNtM5LCgWUcaAc8MUdH3Z0elclREmfzZ%2BJzLY; _gat=1; _ga=GA1.2.1948120585.1453572520', '-H', 'Connection: keep-alive', '-H', 'Hound-Request-Info: {"ClientID":"e7SgQJ_wwXjv5cUx1nLqKQ==","UserID":"houndify_try_api_user","PartialTranscriptsDesired":true,"SDK":"web","SDKVersion":"0.1.6"}', '--compressed'])
        answer = json.parse(resp)
        talk_answer = answer["AllResults"][0]['SpokenResponseLong'];
        # do something with answer
        # speak the answer
        espeak.synth(talk_answer)
        IS_TALKING = False

    def destroy(self):
    	LCD.clear()
    	GPIO.output(self.BUZZ_PIN, GPIO.HIGH)
    	GPIO.cleanup()

halo = Halo()
halo.start_conversation()
#
# if __name__ == "__main__":
# 	try:
# 		halo = Halo()
#         #halo.start_conversation()
# #		halo.start()
# 		#LCD.init(0x27, 1)
# 		#print "LCD initialized... starting sequence"
# 		#halo.displayText("Hello my name is slim shady")
# 	except KeyboardInterrupt:
# 		print "Exiting Halo..."
# 		halo.destroy()
# #	finally:
# #		halo.destroy()
