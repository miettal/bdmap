# coding=utf-8
import datetime
import json
import os
import logging

from flask import Flask
from flask import render_template

# flask
app = Flask(__name__)
#  logger
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.addHandler(gunicorn_logger)
app.logger.setLevel(logging.DEBUG)


filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/center_list.json')
center_list = json.loads(open(filepath).read())

@app.route('/', methods=['GET'])
def index():
    today = datetime.date.today().isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    return render_template('index.html', center_list=center_list, today=today, tomorrow=tomorrow)


@app.route('/<center_name>/<room_name>', methods=['GET'])
def image(qrcode_filename):
    return 'Hello, World!'

if __name__ == '__main__':
    app.run()
