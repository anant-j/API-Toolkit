import requests
import json

deployment = requests.get('http://stagingapi.pythonanywhere.com/git')
if deployment.status_code == 200:
    dep_result = deployment.text.split(",")
    branch = dep_result[0]
    dep_hash = str(dep_result[1])
else:
    assert(False)

try:
    git = requests.get(
        "https://api.github.com/repos/anant-j/API-Toolkit/git/refs/heads/" +
        branch)
except Exception:
    git = requests.get(
        "https://api.github.com/repos/anant-j/API-Toolkit/git/refs/heads/master")

if git.status_code == 200:
    res = json.loads(git.text)
    sha = str(res["object"]["sha"])
else:
    assert(False)

assert(dep_hash == sha)
