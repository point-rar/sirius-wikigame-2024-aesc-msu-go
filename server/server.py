# from gensim.models import Word2Vec, KeyedVectors
# from gensim.test.utils import common_texts
# from gensim.scripts.glove2word2vec import glove2word2vec
# from gensim.test.utils import datapath, get_tmpfile
# import gensim
# from gensim import downloader
#
# # glove_file = datapath('glove.6B.300d.txt')
#
# model = gensim.downloader.load('fasttext-wiki-news-subwords-300')
#
# from flask import Flask, request
#
# app = Flask(__name__)
#
# import json
#
#
# @app.post('/')
# def get_query():
#     links = request.get_json()['links']
#     who = request.get_json()['word']
#
#     result = []
#
#     for i in range(len(links)):
#         try:
#             result.append(str(model.similarity(links[i], who)))
#         except:
#             result.append(str(-1))
#     return json.dumps({"result": result}), 200
#
#
# app.run()