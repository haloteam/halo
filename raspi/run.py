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

# wit init
wit_access_token = '5HO7GQT6GHYYBC4G2M5SPTCWXSNSEL4S'
wit.init()
IS_TALKING = False


THERMISTOR = 17
GAS_SENSOR = 18
BUZZ = 6
RAIN = 13

GPIO.setmode(GPIO.BCM)

HALO_LAMBDA_URL = "https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo"

# queue init
q = Queue(maxsize=0)

def queue_task(q):
    while True:
        updates = q.get()
        print updates
        data = {}
        data['deviceId'] = 1;
        data['updates'] = updates
        data['action'] = "save"
        print data
        resp = subprocess.call(['curl', '-X', 'POST', '-d', json.dumps(data), HALO_LAMBDA_URL])

        if resp.action == "talking":
            IS_TALKING = True
            worker = Thread(target=speech_to_text, args=())
            worker.setDaemon(True)
            worker.start()

        q.task_done()

def speech_to_text():

    # user is prompted to talk
    speech_response = wit.voice_query_auto(wit_access_token)

    # response
    question = urllib.quote_plus(speech_response['_text'])
    resp = subprocess.call(['curl', 'https://www.houndify.com/textSearch?query=' +  + '&clientId=e7SgQJ_wwXjv5cUx1nLqKQ%3D%3D&clientKey=Pi_smrHYQhCA_nLgukp4C4nnQE2WyQvk3l3Bhs8hcbchrLAmjl5LWS3ewq1U8LMser8j890OfhklwNm77baPTw%3D%3D', '-H', 'Accept-Encoding: gzip, deflate, sdch', '-H', 'Accept-Language: en-US,en;q=0.8', '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36', '-H', 'Accept: */*', '-H', 'Referer: https://www.houndify.com/try/986dcfd1-0b91-4346-a5a0-6d53f0d18da2', '-H',
    'Cookie: houndify-sess=s%3Ar-94jGq48cQMay2q1fgRwSolHIV4ZQpk.Y3Wns0NNtM5LCgWUcaAc8MUdH3Z0elclREmfzZ%2BJzLY; _gat=1; _ga=GA1.2.1948120585.1453572520', '-H', 'Connection: keep-alive', '-H', 'Hound-Request-Info: {"ClientID":"e7SgQJ_wwXjv5cUx1nLqKQ==","UserID":"houndify_try_api_user","PartialTranscriptsDesired":true,"SDK":"web","SDKVersion":"0.1.6"}', '--compressed'])


    answer = resp['answer']
    # do something with answer
    # speak the answer

    IS_TALKING = False


def setup():
    ADC.setup(0x48)
    LCD.init(0x27, 1)
    LCD.write(0,0,'System startup...')
    time.sleep(1)
    LCD.clear()
    GPIO.setup(THERMISTOR, GPIO.IN)
    GPIO.setup(GAS_SENSOR, GPIO.IN)
    GPIO.setup(BUZZ, GPIO.OUT)
    GPIO.setup(RAIN, GPIO.OUT)
    GPIO.output(BUZZ, 1)

def update_LCD(temp, gas, h2o):
    if gas >= 180:
        LCD.clear()
        LCD.write(0,0,"ALERT!")
        LCD.write(0,1,"Gas detected!")
        print ''
        print '   ***************'
        print '   * Danger Gas! *'
        print '   ***************'
        print ''

    elif temp <= 45:
        status = 0
        LCD.clear()
        LCD.write(0,0,"ALERT!")
        LCD.write(0,1,"Low temperature!")
        print ''
        print '   ********************'
        print '   * Danger Low Temp! *'
        print '   ********************'
        print ''
    elif h2o <= 100:
        LCD.clear()
        LCD.write(0,0,"ALERT!")
        LCD.write(0,1,"Water detected!")
        print ''
        print '   **************************'
        print '   * Danger Water Detected! *'
        print '   **************************'
        print ''
    else:
        LCD.clear()
        LCD.write(0,0, "System Normal")
        print ''
        print '   --------------------------'
        print '   *  System Status Normal  *'
        print '   --------------------------'
        print ''


def loop():
    worker = Thread(target=queue_task, args=(q,))
    worker.setDaemon(True)
    worker.start()
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
            updates.append({'type' : 'rain', 'value': str(rainVal), 'timestamp': str(datetime.now())})
            q.put(updates)
            q_count = 0
        q_count = q_count + 1
        time.sleep(2)

def destroy():
    GPIO.output(BUZZ, 1)
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        destroy()
