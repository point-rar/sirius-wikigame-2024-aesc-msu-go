from flask import Flask, request
import json
import os
from googletrans import Translator

translator = Translator()
app = Flask(__name__)


@app.post('/')
def get_query():
    words = request.get_json()['words']
    result = translator.translate('. '.join(words), src='ru', dest='en').text.split('.')
    return json.dumps({"result": result}), 200


port = int(os.environ.get("PORT", 7373))
app.run(host='127.0.0.1', port=port)
