# This example uses Python 2.7+ and the python-request library
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
parameters = {
    'start': '1',
    'limit': '5000',
    'convert': 'CNY',
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '830353c1-ff69-462e-8f2c-951b6fedda47',
}

session = Session()
session.headers.update(headers)

try:
    response = session.get(url, params=parameters)
    data = json.loads(response.text)
    print(data)
except (ConnectionError, Timeout, TooManyRedirects) as e:
    print(e)
    
    
    