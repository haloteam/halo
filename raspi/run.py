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


#------------ INITIALIZATIONS -----------_#
# wit
wit_access_token = '5HO7GQT6GHYYBC4G2M5SPTCWXSNSEL4S'

# GLOBALS
IS_TALKING = False
ALARM_ON = False
HALO_LAMBDA_URL = "https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo"

THERMISTOR_PIN = 17
GAS_SENSOR_PIN = 18
BUZZ_PIN = 6
H2O_PIN = 13


GPIO.setmode(GPIO.BCM)

# queue init
q = Queue(maxsize=0)

def setup():
    ADC.setup(0x48)
    LCD.init(0x27, 1)
    LCD.write(0,0,'System startup...')
    time.sleep(1)
    LCD.clear()
    GPIO.setup(THERMISTOR_PIN, GPIO.IN)
    GPIO.setup(GAS_SENSOR_PIN, GPIO.IN)
    GPIO.setup(BUZZ_PIN, GPIO.OUT)
    GPIO.setup(H2O_PIN, GPIO.OUT)
    GPIO.output(BUZZ_PIN, GPIO.HIGH)
    wit.init()

def queue_task(q):
    while True:
        updates = q.get()
        data = {}
        data['deviceId'] = 1;
        data['updates'] = updates
        data['action'] = "save"
        raw_resp = subprocess.call(['curl', '-X', 'POST', '-d', json.dumps(data), HALO_LAMBDA_URL])
        resp = json.loads(raw_resp)
        if resp.action == "talking":
	    print resp
            IS_TALKING = True
            worker = Thread(target=speech_to_text, args=())
            worker.setDaemon(True)
            worker.start()

        q.task_done()

def alarm_task():
	while True:
		if ALARM_ON:
			GPIO.output(BUZZ_PIN, GPIO.LOW)
			time.sleep(.5)
			GPIO.output(BUZZ_PIN, GPIO.HIGH)
		else:
			pass

def speech_to_text():
    # user is prompted to talk
    speech_response = wit.voice_query_auto(wit_access_token)
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

def mouth_open():
    LCD.clear()
    LCD.write(0,0,"")

def setup():
    ADC.setup(0x48)
    LCD.init(0x27, 1)
    LCD.write(0,0,'System startup...')
    time.sleep(1)
    ALARM = False
    LCD.clear()
    GPIO.setup(THERMISTOR_PIN, GPIO.IN)
    GPIO.setup(GAS_SENSOR_PIN, GPIO.IN)
    GPIO.setup(BUZZ_PIN, GPIO.OUT)
    GPIO.setup(H2O_PIN, GPIO.OUT)
    GPIO.output(BUZZ_PIN, GPIO.HIGH)

def update_LCD(temp, gas, h2o):
    global ALARM_ON
    if not IS_TALKING:
        if gas >= 150:
            if not ALARM_ON == True:
                ALARM_ON = True
            LCD.clear()
            LCD.write(0,0,"ALERT!")
            LCD.write(0,1,"Gas detected!")
            print ''
            print '   ***************'
            print '   * Danger Gas! *'
            print '   ***************'
            print ''

        elif temp <= 45:
            if not ALARM_ON == True:
                ALARM_ON = True
            status = 0
            LCD.clear()
            LCD.write(0,0,"ALERT!")
            LCD.write(0,1,"Low temperature!")
            print ''
            print '   ********************'
            print '   * Danger Low Temp! *'
            print '   ********************'
            print ''

        elif h2o <= 200:
            if not ALARM_ON == True:
                ALARM_ON = True
            LCD.clear()
            LCD.write(0,0,"ALERT!")
            LCD.write(0,1,"Water detected!")
            print ''
            print '   **************************'
            print '   * Danger Water Detected! *'
            print '   **************************'
            print ''

        else:
	    if ALARM_ON:
                ALARM_ON = False
            LCD.clear()
            LCD.write(0,0, "System Normal")
            print ''
            print '   --------------------------'
            print '   *  System Status Normal  *'
            print '   --------------------------'
            print ''
    else:
        pass

def loop():
    worker = Thread(target=queue_task, args=(q,))
    worker.setDaemon(True)
    worker.start()
    alarm_thread = Thread(target=alarm_task)
    alarm_thread.setDaemon(True)
    alarm_thread.start()
    status = 1
    count = 0
    q_count = 0
    now = datetime.now()
    LCD.write(0,0,'System Normal')
    while True:
        # get and convert temperature
        analogTemp = ADC.read(0)
        Vr = 5 * float(analogTemp) / 255
        Rt = 10000 * Vr / (5 - Vr)
        temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15 + 25)))
        temp = (temp - 273.15) * 9/5 + 32
        print 'temperature = ', temp, 'F'
        # get and convert gas sensor data
        gas = ADC.read(1)
        print 'gas sensor = ', gas

        # tmp = GPIO.input(GAS_SENSOR)
        # if tmp != status:
        #     check_gas(tmp)
        #     status = tmp
        # if status == 0:
        #     count += 1
        #     if count % 2 == 0:
        #         GPIO.output(BUZZ, 1)
        #     else:
        #         GPIO.output(BUZZ, 0)
        # else:
        #     GPIO.output(BUZZ, 1)
        #     count = 0

        # get water data
        h2o = ADC.read(2)
        print "h2o sensor = " + str(h2o)
        update_LCD(temp, gas, h2o)

        if q_count > 3.5:
            updates = []
            updates.append({'type' : 'temperature', 'value': str(temp), 'timestamp': str(datetime.now())})
            updates.append({'type' : 'gas', 'value': str(ADC.read(1)), 'timestamp': str(datetime.now())})
            updates.append({'type' : 'h2o', 'value': str(h2o), 'timestamp': str(datetime.now())})
            q.put(updates)
            q_count = 0
        q_count = q_count + 1
        time.sleep(2)

def destroy():
	LCD.clear()
	GPIO.output(BUZZ_PIN, GPIO.HIGH)
	GPIO.output(H2O_PIN, GPIO.HIGH)
	GPIO.cleanup()

if __name__ == '__main__':
    try:
        setup()
        loop()
    except KeyboardInterrupt:
	print "Exiting Halo..."
    finally:
        destroy()
