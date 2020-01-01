import requests
import json

def getStatusCode(url):
    response = requests.get(url)
    return(response.status_code)

def test_answer():
    assert (getStatusCode('https://stagingapi.pythonanywhere.com/status')==200)