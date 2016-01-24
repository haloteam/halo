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
import random
from espeak import espeak

class Halo:
    def __init__(self):
        # pins for sensors
        self.THERMISTOR_PIN = 17
        self.GAS_SENSOR_PIN = 18
        self.BUZZ_PIN = 6
        self.H2O_PIN = 13

        # pins for eyes
        self.SDI_0 = 20
        self.RCLK_0 = 16
        self.SRCLK_0 = 21
        self.SDI_1 = 5
        self.RCLK_1 = 19
        self.SRCLK_1 = 26

        self.wit_access_token = '5HO7GQT6GHYYBC4G2M5SPTCWXSNSEL4S'
        self.halo_lambda_save_url = 'https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo'
        self.save_data_queue = Queue(maxsize=0)
        self.temperature = None
        self.gas = None
        self.h2o = None

        self.inConversation = False
        self.alarmOn = False
        self.setup()

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        ADC.setup(0x48)
        LCD.init(0x27, 1)
        self.alert("System startup")

        # setup pins for sensors
        GPIO.setup(self.THERMISTOR_PIN, GPIO.IN)
        GPIO.setup(self.GAS_SENSOR_PIN, GPIO.IN)
        GPIO.setup(self.BUZZ_PIN, GPIO.OUT)
        GPIO.setup(self.H2O_PIN, GPIO.IN)

        # setup pins for "eyes"
        # first eye
        GPIO.setup(self.SDI_0, GPIO.OUT)
        GPIO.setup(self.RCLK_0, GPIO.OUT)
        GPIO.setup(self.SRCLK_0, GPIO.OUT)
        GPIO.output(self.SDI_0, GPIO.LOW)
        GPIO.output(self.RCLK_0, GPIO.LOW)
        GPIO.output(self.SRCLK_0, GPIO.LOW)
        # second eye
        GPIO.setup(self.SDI_1, GPIO.OUT)
        GPIO.setup(self.RCLK_1, GPIO.OUT)
        GPIO.setup(self.SRCLK_1, GPIO.OUT)
        GPIO.output(self.SDI_1, GPIO.LOW)
        GPIO.output(self.RCLK_1, GPIO.LOW)
        GPIO.output(self.SRCLK_1, GPIO.LOW)

        #wit.init()


    def begin_threads(self):
        save_data_worker = Thread(target=self.save_data_thread, args=())
        save_data_worker.setDaemon(True)
        save_data_worker.start()
        blink_worker = Thread(target = self.blink)
        blink_worker.setDaemon(True)
        blink_worker.start()
        alarm_worker = Thread(target = self.alarm)
        alarm_worker.setDaemon(True)
        alarm_worker.start()

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
            time.sleep(0.25)
            self.get_gas_sensor_data()
            time.sleep(0.25)
            self.get_h2o_sensor_data()
            time.sleep(0.25)
            self.check_data()

    def check_data(self):
        if self.inConversation == False:
            if self.gas > 90:
                self.alert("GAS DETECTED!")
                self.alarmOn = True
            elif self.temp < 45:
                self.alert("LOW TEMPERATURE!")
                self.alarmOn = True
            elif self.h2o < 215:
                self.alert("WATER DETECTED!")
                self.alarmOn = True
            else:
                self.display_text("SYSTEM NORMAL")
                self.alarmOn = False
            
    def alarm(self):
        while True:
            if self.alarmOn:
                GPIO.output(self.BUZZ_PIN, GPIO.LOW)
                time.sleep(.5)
                GPIO.output(self.BUZZ_PIN, GPIO.HIGH)
                time.sleep(.5)
            else:
                GPIO.output(self.BUZZ_PIN, GPIO.HIGH)

    def alert(self, text):
        LCD.clear()
        LCD.write(0,0,"ALERT!")
        LCD.write(0,1,text)

    def display_text(self, text):
        LCD.clear()
        if len(text) <= 16:
            LCD.write(0,0,text)
        else:
            top = text[0:15]
            bot = text[16:]
            LCD.write(0,0,top)
            LCD.write(0,1,bot)

    def speak(self, text):
        subprocess.call(["espeak", text])

    def mouth_open(self):
        LCD.clear()
        LCD.write(0,0,'|--------------|')
        LCD.write(0,1,'|______________|')

    def mouth_close(self):
        LCD.clear()
        LCD.write(0,0,'________________')
        LCD.write(0,1,'----------------')

    def talk(self):
        while True:
            self.mouth_open()
            time.sleep(.25)
            self.mouth_close()
            time.sleep(.25)

    def get_temperature_sensor_data(self):
        try:
            analogTemp = ADC.read(0)
            Vr = 5 * float(analogTemp) / 255
            Rt = 10000 * Vr / (5 - Vr)
            temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15 + 25)))
            self.temp = (temp - 273.15) * 9/5 + 32
            return self.temp
        except:
            print "Temp sensor read failed... analog temp = ", analogTemp

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
        self.get_temperature_sensor_data()
        self.get_gas_sensor_data()
        self.get_h2o_sensor_data()
        
        if self.temp is not None:
            updates.append({'type' : 'temperature', 'value': str(self.temp), 'timestamp': str(datetime.now())})

        if self.gas is not None:
            updates.append({'type' : 'gas', 'value': str(self.gas), 'timestamp': str(datetime.now())})

        if self.h2o is not None:
            updates.append({'type' : 'rain', 'value': str(self.h20), 'timestamp': str(datetime.now())})
        data = {}
        data['deviceId'] = 1;
        data['updates'] = updates
        data['action'] = "save"
        subprocess.call(['curl', '-X', 'POST', '-d', json.dumps(data), self.halo_lambda_save_url])

    def start_conversation(self):
        #speech_response = wit.voice_query_auto(self.wit_access_token)
        try:
            conversation_starters = ["Hello", "How are you?", "Hi There", "I don't know you, but I like you.", "You are dashing in that Suit."]
            espeak.synth(random.choice(conversation_starters))
        except Exception as err:
            print err
        # user is prompted to talk

        # # response
        # question = urllib.quote_plus(speech_response['_text'])
        # resp = subprocess.call(['curl', 'https://www.houndify.com/textSearch?query=' + question + '&clientId=e7SgQJ_wwXjv5cUx1nLqKQ%3D%3D&clientKey=Pi_smrHYQhCA_nLgukp4C4nnQE2WyQvk3l3Bhs8hcbchrLAmjl5LWS3ewq1U8LMser8j890OfhklwNm77baPTw%3D%3D', '-H', 'Accept-Encoding: gzip, deflate, sdch', '-H', 'Accept-Language: en-US,en;q=0.8', '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36', '-H', 'Accept: */*', '-H', 'Referer: https://www.houndify.com/try/986dcfd1-0b91-4346-a5a0-6d53f0d18da2', '-H',
        # 'Cookie: houndify-sess=s%3Ar-94jGq48cQMay2q1fgRwSolHIV4ZQpk.Y3Wns0NNtM5LCgWUcaAc8MUdH3Z0elclREmfzZ%2BJzLY; _gat=1; _ga=GA1.2.1948120585.1453572520', '-H', 'Connection: keep-alive', '-H', 'Hound-Request-Info: {"ClientID":"e7SgQJ_wwXjv5cUx1nLqKQ==","UserID":"houndify_try_api_user","PartialTranscriptsDesired":true,"SDK":"web","SDKVersion":"0.1.6"}', '--compressed'])
        # answer = json.parse(resp)
        # talk_answer = answer["AllResults"][0]['SpokenResponseLong'];
        # # do something with answer
        # # speak the answer
        # #espeak.synth(talk_answer)
        # IS_TALKING = False

    def set_eyes(self, dat):
        for bit in range(0,8):
            GPIO.output(self.SDI_0, 0x80 & (dat << bit))
            GPIO.output(self.SDI_1, 0x80 & (dat << bit))
            GPIO.output(self.SRCLK_0, GPIO.HIGH)
            GPIO.output(self.SRCLK_1, GPIO.HIGH)
            time.sleep(0.001)
            GPIO.output(self.SRCLK_0, GPIO.LOW)
            GPIO.output(self.SRCLK_1, GPIO.LOW)
        GPIO.output(self.RCLK_0, GPIO.HIGH)
        GPIO.output(self.RCLK_1, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(self.RCLK_0, GPIO.LOW)
        GPIO.output(self.RCLK_1, GPIO.LOW)

    def blink(self):
        while True:
            if self.alarmOn:
                ray = [0x20, 0x10, 0x08, 0x04, 0x02, 0x01]
                for x in ray:
                    self.set_eyes(x)
                    time.sleep(0.4)
            else:
                rand1 = random.randint(3,8)
                self.set_eyes(0x3f)
                time.sleep(rand1)
                self.set_eyes(0x40)
                time.sleep(0.4)

    def destroy(self):
    	LCD.clear()
        LCD.write(0,0,'')
        LCD.write(0,1,'')
        self.set_eyes(0x00)
    	GPIO.output(self.BUZZ_PIN, GPIO.HIGH)
    	GPIO.cleanup()

if __name__ == "__main__":
    try:
        halo = Halo()
        halo.start()
    except KeyboardInterrupt:
        print "Exiting Halo..."
    finally:
        halo.destroy()
    #halo.start_conversation()
	# try:
    #     halo = Halo()
    #     halo.start_conversation()
	# 	#LCD.init(0x27, 1)
	# 	#print "LCD initialized... starting sequence"
	# 	#halo.displayText("Hello my name is slim shady")
	# except KeyboardInterrupt:
	# 	print "Exiting Halo..."
	# finally:
    #     print 'about to destroy'
	# 	halo.destroy()
