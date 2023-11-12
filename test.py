import requests
import time

start = time.time()

url = 'https://onguard-394009.uc.r.appspot.com/?sms='

payload = 'Show me the list of all appointments today'

# Send a GET request
response = requests.get(url+payload)
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    # result = data['result']
    print(data)
else:
    print(f"Request failed with status code {response.status_code}")
    
end = time.time()
print("Time taken: {} seconds".format(end-start))
