import requests
import json


def test_staging_upload():
    deployment = requests.get('http://stagingapi.pythonanywhere.com/git')
    if deployment.status_code == 200:
        dep_result = deployment.text.split(",")
        branch = dep_result[0]
        dep_hash = str(dep_result[1])
    else:
        assert False

    if branch == "master" or branch == "branch":
        assert True
    else:
        git = requests.get(
            "https://api.github.com/repos/anant-j/API-Toolkit/git/refs/heads" +
            "/" + branch)
        if git.status_code == 200:
            res = json.loads(git.text)
            sha = str(res["object"]["sha"])
            assert dep_hash == sha, "test failed"
        else:
            assert False
