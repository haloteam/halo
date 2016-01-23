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
        print data
        resp = subprocess.call(['curl', '-X', 'POST', '-d', json.dumps(data), HALO_LAMBDA_URL])
        print resp
        q.task_done()


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
        LCD.write(1,0,"Gas detected!")
        print ''
        print '   ***************'
        print '   * Danger Gas! *'
        print '   ***************'
        print ''
    elif temp <= 45:
        status = 0
        LCD.clear()
        LCD.write(0,0,"ALERT!"
        LCD.write(1,0,"Low temperature!")
        print ''
        print '   ********************'
        print '   * Danger Low Temp! *'
        print '   ********************'
        print ''
    elif h2o <= 100:
        LCD.clear()
        LCD.write(0,0,"ALERT!"
        LCD.write(1,0,"Water detected!")
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
    LCD.write(0,0,'System status: OK')
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
