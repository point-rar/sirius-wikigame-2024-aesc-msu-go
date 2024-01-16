import json

import requests

host = "http://127.0.0.1:5000"


def get_score(links, last_word):
    data = json.dumps({
        "links": links,
        "word": last_word
    })

    session = requests.Session()

    result = session.post(url=host, data=data, headers={'Content-Type': 'application/json'})

    answer = [float(i) for i in json.loads(result.text)['result']]

    return answer
