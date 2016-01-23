import requests

r = requests.post('https://a9a0t0l599.execute-api.us-east-1.amazonaws.com/prod/Halo', {"deviceId": 1})
r.status_code
