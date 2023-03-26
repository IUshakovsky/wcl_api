from flask import Flask, jsonify, make_response
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

class WclGenerator(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('text', required = 'True', trim='True')
        parser.add_argument('background_color', default='white', store_missing=True)
        parser.add_argument('width', type=int, default='1200')
        parser.add_argument('height', type=int, default='800')
        parser.add_argument('mask', choices=('circle','cloud', None), default = 'white')
        
        args = parser.parse_args(strict=True)
        
        if not (check_status := self._check_input(args))[0]:
            return {'message': check_status[1]}, 400
        
        text = self._preprocess_text(args["text"])
        params_for_wcl = self._get_params_for_wcl(args)

        response = make_response(self._generate_img(text, params_for_wcl))
        response.headers.set('Content-Type', 'image/png')
        
        return response  

    def _check_input(self, data: dict) -> tuple:        
        if 'background_color' in data and \
            (bg_color := data['background_color']) != None: 
            if not is_color_like(bg_color):
                return (False, {'background_color': 'Not color like value'})
        
        return (True,'')
    
    def _get_params_for_wcl(self, params: dict) -> dict:
        params.pop('text')
        params['collocations'] = True
            
        params['width'] = min(int(params['width']), MAX_WIDTH)    
        params['height'] = min(int(params['height']), MAX_HEIGHT)

        if params['mask']:
            maskImg = Image.open(f'masks/{params["mask"]}.png')
            if params['mask'] == 'circle':
                size = (params['width'],params['width'])
            else:
                size = (params['width'],params['height']) 
            
            params['mask'] = array(maskImg.resize(size))
        
        if not params['background_color']:
            params['background_color'] = 'white'
        
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