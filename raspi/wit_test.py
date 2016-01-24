import wit
from multiprocessing import Process, Queue
import time

outputQueue = Queue()

def start_wit():
    wit.init()
    wit_access_token = '5HO7GQT6GHYYBC4G2M5SPTCWXSNSEL4S'
    while True:
        resp = wit.voice_query_auto(wit_access_token)
        outputQueue.put(resp)
