from flask import Flask
from flask_restful import Resource, Api, reqparse

from controllers import Test as TC
from controllers import TextData as TDC


app = Flask(__name__)
api = Api(app)

class TextData(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True)
        parser.add_argument('per_frame', required=False)
        args = parser.parse_args()
        print('args', args)

        textData = TDC.locateFiles(args)

        return textData, 200

        

# Test that tesseract is running correctly
class Test(Resource):
    def get(self):
        return TC.sendTest()
        
api.add_resource(TextData, '/text-data')
api.add_resource(Test, '/test')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)