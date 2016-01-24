import wit
from multiprocessing import Process, Queue
import time

#halo = Halo()

wit.init()
wit_access_token = '5HO7GQT6GHYYBC4G2M5SPTCWXSNSEL4S'
resp = wit.voice_query_auto(wit_access_token)
print resp
