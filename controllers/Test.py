import pytesseract as pyt
import os
import cv2

from services import helperFunctions as HF

def sendTest():
    image = cv2.imread(os.getcwd().split('/controllers')[0] + '/media/test.JPG')
    processed_data = [i[11] for i in HF.gather_image_data(image)]
    
    # If Tesseract-ocr reads the data as accuratly as Tesseract v.5 would this will return 200 success
    if processed_data == ["YouTube","STACEY","ABRAMS","your","name","STAND","WITH","Sitcoms","Conan","Helps","Assistant","ANew","CONAN","Coco","Conan","Hangs","With","Interns","CONAN","Conan","Andy","Help","Freshmen","Move","Into","College","\"Late","Nig.","Conan","Says","Farewell","Late","Night","CONAN","Sona","Finishes","\"Friends\"","Marathon","CONAN","1.9M","viey","Team","Coco","#CONAN:","Joel","McHale","Full","subs","Interview","CONAN"]:
        return{
            'status': 'success',
            'message': '🚀 All systems go!'
        }, 200
    else:
        try:
            tesseract_version = pyt.get_tesseract_version()
        except:
            tesseract_version = 'Tesseract not found'
        return{
            'status': 'failure',
            'message': f'🔥Test failed.   Tesseract version: {tesseract_version}'
        }, 404