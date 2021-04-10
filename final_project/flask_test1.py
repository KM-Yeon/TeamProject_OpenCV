
from flask import Flask, render_template


import transcribe_streaming_mic2 as mic


app = Flask(__name__)

# http://localhost:8800/

@app.route('/')
def index():
   return render_template('index.html')


@app.route('/search_to_voice')

def search_to_voice():
    list_dict = mic.call_runner(4)
    print("flask---",list_dict)
    return render_template('index.html', MY_LIST_DICT=list_dict)



@app.route('/search_to_text')
def search_to_text():
    pass


if __name__ == '__main__':
    app.debug = True
    app.run(port=8000, debug=True)    # 개발 후에는 False로 설정!! 개발자모드임
