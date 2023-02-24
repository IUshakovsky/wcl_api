from flask import Flask, request, jsonify
from matplotlib.colors import is_color_like
from wordcloud import WordCloud
from PIL import Image
from io import BytesIO
from pprint import pprint
from numpy import array

MAX_WIDTH = 3600
MAX_HEIGHT = 2400

app = Flask(__name__)


@app.route('/', methods=['POST','GET'])
def home():
    return "\_O_/"

@app.route('/wcl', methods=['POST'] )
def generate_wcl():
    input_params = request.get_json()
    
    if not (check_status := check_input(input_params))[0]:
        return jsonify({'error': check_status[1]}), 400
    
    params = parse_data(input_params)
    text = input_params["text"]
    
    return generate_img(text, params)
                
def check_input(data: dict) -> tuple:
    if 'text' not in data:
        return (False,'Missing required parameter Text')
    
    if 'background_color' in data and \
        (bg_color := data['background_color']) != None: 
        if not is_color_like(bg_color):
            return (False, 'Incorrect value of background_color parameter')
    
    return (True,'')

def parse_data(data: dict) -> dict:
    default_params = {
        "width":            1200,
        "height":           800,
        "collocations":     True,
        "background_color": "white",
        "mask":             None    
    }
    
    params = { item[0]:item[1] 
                for item in {**default_params, **data}.items() 
                if item[0] in default_params 
    }
    
    if params['mask'] not in {'circle','cloud'}:
        params.pop('mask')
    else:
        params['mask'] = array(Image.open(f'masks/{params["mask"]}.png'))
    
    params['width'] = min(params['width'], MAX_WIDTH)    
    params['height'] = min(params['height'], MAX_HEIGHT)
    
    return params


def generate_img(text:str, params:dict) -> bytes:
    wc = WordCloud(**params)
    wc.generate(text)
    
    np_data = wc.to_array()
    img_data = Image.fromarray(np_data)
    
    return img_to_png_bytes(img_data)


def img_to_png_bytes(img: Image) -> bytes:
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.read()


if __name__ == "__main__":
    pass