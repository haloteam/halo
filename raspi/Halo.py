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


class Halo:
	def __init__(self):
        self.THERMISTOR_PIN = 17
        self.GAS_SENSOR_PIN = 18
        self.BUZZ_PIN = 6
        self.RAIN_PIN = 13
        self.wit_access_token = '5HO7GQT6GHYYBC4G2M5SPTCWXSNSEL4S'
        self.halo_lambda_save_url = 'https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo'
        self.save_data_queue = Queue(maxsize=0)

        self.temperature = None
        self.gas = None
        self.h20 = None


        self.setup()

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        ADC.setup(0x48)
        LCD.init(0x27, 1)
        #LCD.write(0,0,'System startup...')
        GPIO.setup(self.THERMISTOR_PIN, GPIO.IN)
        GPIO.setup(self.GAS_SENSOR_PIN, GPIO.IN)
        GPIO.setup(self.BUZZ_PIN, GPIO.OUT)
        GPIO.setup(self.RAIN_PIN, GPIO.OUT)
        wit.init()

    def begin_threads(self):
        save_data_worker = Thread(target=save_data_thread, args=())
        save_data_worker.setDaemon(True)
        save_data_worker.start()


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
        pass
    def displayText(self, text):
        pass

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
        return self.h20

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
