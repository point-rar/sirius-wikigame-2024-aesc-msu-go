from gensim.models import Word2Vec, KeyedVectors
from gensim.test.utils import common_texts
from gensim.scripts.glove2word2vec import glove2word2vec
from gensim.test.utils import datapath, get_tmpfile
import gensim
from gensim import downloader
from flask import Flask, request
import json
import os
from navec import Navec
from slovnet.model.emb import NavecEmbedding


lang = "ru"

if lang == "en":
    model = gensim.downloader.load('fasttext-wiki-news-subwords-300')

    app = Flask(__name__)


    @app.post('/')
    def get_query():
        links = request.get_json()['links']
        who = [request.get_json()['word']]

        result = []

        for i in range(len(links)):
            try:
                result.append(str(model.similarity(links[i], who)))
            except Exception:
                result.append(str(-1))
        return json.dumps({"result": result}), 200


    port = int(os.environ.get("PORT", 5000))
    app.run(host='127.0.0.1', port=port)

elif lang == "ru":
    path = 'files/hudlit_12B_500K_300d_100q.tar'  # 51MB

    model = Navec.load(path)

    app = Flask(__name__)


    @app.post('/')
    def get_query():
        links = request.get_json()['links']
        who = request.get_json()['word'].lower()

        result = []

        for i in range(len(links)):
            links[i] = links[i].lower()
            try:
                result.append(str(model.sim(links[i], who)))
            except:
                result.append(str(-1))
        return json.dumps({"result": result}), 200


    app.run()

else:
    raise NotImplementedError
