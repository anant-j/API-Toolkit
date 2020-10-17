import requests
import json 

deployment = requests.get('http://anantj24.pythonanywhere.com/git')
if deployment.status_code==200:
    dep_result=deployment.text.split(",")
    branch=dep_result[0]
    dep_hash=str(dep_result[1])
else:
    dep_hash=2222

try:
    git=requests.get("https://api.github.com/repos/anant-j/API-Toolkit/git/refs/heads/"+branch)
except Exception:
    git=requests.get("https://api.github.com/repos/anant-j/API-Toolkit/git/refs/heads/master")
if git.status_code==200:
    res = json.loads(git.text)
    sha=str(res["object"]["sha"])
else:
    sha=1111
if(dep_hash!="0000000000000000000000000000000000000000"):
    assert(dep_hash==sha)
else:
    assert(True)