from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api, reqparse
from matplotlib.colors import is_color_like
from wordcloud import WordCloud
from PIL import Image
from io import BytesIO
from numpy import array
from string import punctuation

MAX_WIDTH = 3600
MAX_HEIGHT = 2400

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()

class WclGenerator(Resource):
    def post(self):
        input_params = request.get_json() 
        
        if not (check_status := self._check_input(input_params))[0]:
            return jsonify({'error': check_status[1]}), 400
        
        params = self._parse_data(input_params)
        text = self._preprocess_text(input_params["text"])
        
        response = make_response(self._generate_img(text, params))
        response.headers.set('Content-Type', 'image/png')
        
        return response  

    def _check_input(self, data: dict) -> tuple:
        if 'text' not in data:
            return (False,'Missing required parameter Text')
        
        if 'background_color' in data and \
            (bg_color := data['background_color']) != None: 
            if not is_color_like(bg_color):
                return (False, 'Incorrect value of background_color parameter')
        
        return (True,'')
    
    def _parse_data(self, data: dict) -> dict:
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
            
        params['width'] = min(int(params['width']), MAX_WIDTH)    
        params['height'] = min(int(params['height']), MAX_HEIGHT)

        if params['mask'] not in {'circle','cloud'}:
            params.pop('mask')
        else:
            maskImg = Image.open(f'masks/{params["mask"]}.png')
            if params['mask'] == 'circle':
                size = (params['width'],params['width'])
            else:
                size = (params['width'],params['height']) 
            
            params['mask'] = array(maskImg.resize(size))
        
        return params

    def _preprocess_text(self, text: str) -> str:
        '''
        replace {} () [] with spaces,
        remove words of less then 2 letters
        '''
        trans_dict = dict.fromkeys(punctuation, '')
        trans_dict.update(dict.fromkeys('[]{}()',' '))
        
        clean_str = text.translate(str.maketrans(trans_dict))
        words_list = [word for word in clean_str.split() if len(word) > 2 ]
        return ' '.join(words_list)
        
    def _generate_img(self, text:str, params:dict) -> bytes:
        wc = WordCloud(**params)
        wc.generate(text)
        
        
        np_data = wc.to_array()
        img_data = Image.fromarray(np_data)
        
        return self._img_to_png_bytes(img_data)


    def _img_to_png_bytes(self, img: Image) -> bytes:
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.read()

api.add_resource(WclGenerator, '/wcl') 

if __name__ == "__main__":
    app.run()