from flask import Flask, request
import json
import os
from googletrans import Translator

translator = Translator()
app = Flask(__name__)
mp = {}


@app.post('/')
def get_query():
    words = request.get_json()['words']
    inds = []
    result = [''] * len(words)
    for i in range(len(words)):
        if words[i] in mp.keys():
            result[i] = mp[words[i]]
            continue
        inds.append(i)
    q_result = translator.translate('. '.join([words[i] for i in inds]), src='ru', dest='en').text.split('.')
    for i in range(len(inds)):
        mp[words[inds[i]]] = result[inds[i]] = q_result[i]
    return json.dumps({"result": result}), 200


port = int(os.environ.get("PORT", 7373))
app.run(host='127.0.0.1', port=port)
