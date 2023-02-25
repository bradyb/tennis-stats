import certifi
import json
import urllib3

http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)
# TODO: Check that response is legit (i.e. http request doesn't need to be retried).
resp = http.request("GET", "https://www.rolandgarros.com/en-us/matches/2022/SM001")
print(resp.data)
# jsonResp = json.loads(resp.data.decode('utf-8'))

# print(resp)
