from flask import Flask, request
from scrape_captions import scrape_captions
import os
import traceback

app = Flask(__name__)

@app.route('/',  methods=['GET'])
def hello_world():
    return 'Caption scraper is live :)'

@app.route('/', methods=['POST'])
def kickoff_poem_stitcher():
    data = request.get_json()
    try:
        return str(scrape_captions(**data))
    except Exception as e:
        tb = traceback.format_exc()
        raise e

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
