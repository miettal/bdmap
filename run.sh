#!/bin/bash

export FLASK_APP=bdmap
export FLASK_ENV=development
pip install -e .
flask run
