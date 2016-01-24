import wit
wit.init()
wit_access_token = '5HO7GQT6GHYYBC4G2M5SPTCWXSNSEL4S'
speech_response = wit.voice_query_auto(wit_access_token)
print speech_response
