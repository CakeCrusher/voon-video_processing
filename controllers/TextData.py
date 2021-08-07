from requests.models import Response
import youtube_dl
import cv2
import os
import pytesseract as pyt
from nltk import edit_distance
from datetime import datetime, date
import json
from services import apiRequests as APIR

from services import helperFunctions as HF
from services import textDataFunctions as TDF
def timeNow():
    # print the current time
    return str(date.today()) + ' ' + str(datetime.now().time())
def locateFiles(args):
    print(f'Started at {timeNow()}')
    videoVH = VideoHandler(args['url'])
    videoVH.getVideoData()
    videoVH.getFileData()
    print('FPS: ', videoVH.fps)
    print(args['per_frame'], type(args['per_frame']))
    saveFPS = int(videoVH.fps/int(args['per_frame']))
    print('save FPS: ', saveFPS)
    frameData = videoVH.run_every_x_frame(saveFPS, lambda a, b: videoVH.find_matches(a))
    os.remove(videoVH.video_path)
    print(f'Finished processing video "{videoVH.video_name}" at {timeNow()}!')
    if 'v=' in args['url'] :
        videoId = args['url'].split('v=')[1].split('&')[0]
    else:
        videoId = args['url'].split('/')[3]
    response = {
        'videoId': videoId,
        'githubURL': videoVH.githubURL,
        'fps': videoVH.fps,
        'dimensions': {
            'x': videoVH.dimensions[0],
            'y': videoVH.dimensions[1],
        },
        'payload': frameData
    }

    # HF.sendResponseToBackend(response)

    return response

class VideoHandler():
    def __init__(self, url):
        self.url = url
        self.githubURL = None
        if 'v=' in url:
            self.video_name = url.split('v=')[-1][:11]
        else:
            self.video_name = self.url.split('/')[-1][:11]
        
        self.media_path = os.getcwd().split('/controllers')[0]+'/media'
        self.video_path = None

        self.vid_cap = None
        self.n_frames = None
        self.fps = None

        self.dimensions = None
        self.description = None

        self.file_names = None

    def getVideoData(self):
        if self.video_name in [i.split('.')[0] for i in os.listdir(os.getcwd()+'/media/')]:
            toDownload = False
        else:
            toDownload = True
            print('Downloading...')
        
        def processingInfo(res):
            if res['status'] == 'finished':
                print(res)
        
        ydl_opts = {
            'format': 'bestvideo',
            'outtmpl': self.media_path+f'/{self.video_name}'+'.%(ext)s',
            'progress_hooks': [processingInfo]
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(
                self.url, download=toDownload
            )
        self.video_path = self.media_path+'/'+self.video_name+'.'+meta['ext']
        self.vid_cap = cv2.VideoCapture(self.video_path)
        self.n_frames = int(self.vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.vid_cap.get(cv2.CAP_PROP_FPS))
        self.vid_cap.release()

        self.dimensions = [meta['width'], meta['height']]
        self.description = meta['description']

    def getFileData(self, url = None):
        if url:
            parsedUrl = APIR.parseGithubURL(url)
            filePaths = APIR.fetchRepoFiles(parsedUrl['owner'], parsedUrl['repo'])
            # self.file_names = [path.split('/')[-1] for path in filePaths]
            self.file_names = filePaths
        else:
            words = self.description.split(' ')
            url = None
            for word in words:
                if 'https://' in word:
                    potentialURL = 'https://'+word.split('https://')[1]
                    if 'https://github.com/' in potentialURL:
                        url = potentialURL
                        break
            self.githubURL = url
            parsedUrl = APIR.parseGithubURL(url)
            filePaths = APIR.fetchRepoFiles(parsedUrl['owner'], parsedUrl['repo'])
            # self.file_names = [path.split('/')[-1] for path in filePaths]
            self.file_names = filePaths
        return url
            
            


    def gather_image_data(self, image, saveImageOnFile = None):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        processed_data = HF.gather_image_data(image)

        curr_data_index = 0
        for data_ins in processed_data:
            data_ins.append(curr_data_index)
            curr_data_index += 1

        if saveImageOnFile:
            proof_image = image.copy()
            for box in processed_data:
                x, y, w, h, text = int(box[6]), int(box[7]), int(box[8]), int(box[9]), box[11]
                cv2.rectangle(proof_image, (x,y), (w+x,h+y), (255,0,0), 1)
                cv2.putText(proof_image, text, (x,y),cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,0,0), 2)
            cv2.imwrite(self.media_path+'/ID'+saveImageOnFile+'.jpg', proof_image)

        return processed_data

    def find_matches(self, image, saveImageOnFile = None):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        data = self.gather_image_data(image, saveImageOnFile)

        # self.file_names = ['restock_checker', 'scrape_trigger.py']
        # data = [
        #     [0., 0., 0., 0., 0., 0., 1004, 10, 19, 10, 0., 'reztock', 12],
        #     [0., 0., 0., 0., 0., 0., 1010, 9, 22, 12, 0., 'check', 13],
        #     [0., 0., 0., 0., 0., 0., 1004, 9, 19, 10, 0., 'deCOYpy', 14],
        #     [0., 0., 0., 0., 0., 0., 1004, 9, 19, 10, 0., 'scrape_triggerpy', 15],
        #     [0., 0., 0., 0., 0., 0., 1004, 9, 19, 10, 0., 'deCOYpy', 16],
        #     [0., 0., 0., 0., 0., 0., 1004, 9, 19, 10, 0., 'RESTOCK', 17],
        #     [0., 0., 0., 0., 0., 0., 1004, 9, 19, 10, 0., 'che..', 18],
        # ]

        data_matches = [] # [{image_data: data_ins, file_name]]
        specific_files = [path.split('/')[-1] for path in self.file_names]
        for data_ins, file_name in [(data_ins, file_name) for data_ins in data for file_name in specific_files]:
            parsed_file_name = TDF.space_clone_less(file_name)
            if not HF.index_in_use(data_ins, data_matches):
                for i in range(TDF.space_twin_cou(file_name)+1):
                    def is_within_range(di):
                        if data_ins[-1] <= di[-1] <= data_ins[-1]+i:
                            return True
                        else:
                            return False
                    data_instances = list(filter(is_within_range, data))
                    amal_data_ins = HF.amalgamated_data_ins(data_instances, file_name)
                    if amal_data_ins['unfinished']:
                        if edit_distance(amal_data_ins['text'], parsed_file_name) < (len(parsed_file_name) * 0.5): # tolerance percentage
                            data_matches.append(amal_data_ins)
                            break
                    else:
                        if edit_distance(amal_data_ins['text'], parsed_file_name) < (len(parsed_file_name) * 0.25): # tolerance percentage
                            data_matches.append(amal_data_ins)
                            break
        data_matches_copy = []
        for dm in data_matches:
            def isRoot(fn):
                if fn.split('/')[-1] == dm['file_name']:
                    return True
                else:
                    return False
            dm['file_name'] = list(filter(isRoot, self.file_names))[0]
            data_matches_copy.append(dm)
        data_matches = data_matches_copy
        
        proof_image = image.copy()
        for box in data_matches:
            x, y, w, h, text = box['x'], box['y'], box['width'], box['height'], box['file_name']
            cv2.rectangle(proof_image, (x,y), (w+x,h+y), (255,0,0), 1)
            cv2.putText(proof_image, text, (x,y),cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,0,0), 2)
        if saveImageOnFile:
            cv2.imwrite(self.media_path+'/FM'+saveImageOnFile+'.jpg', proof_image)

        return {'data_matches': data_matches, 'image': proof_image}

    def save_image(self, image, _):
        cv2.imwrite(self.media_path+'/'+self.video_name+'.jpg', image)
        print('Image saved')

    def run_every_x_frame(self, x, callback, show=False):
        frameData = []
        frameCou = 0
        videoCap = cv2.VideoCapture(self.video_path)
        while videoCap.isOpened():
            success, image = videoCap.read()
            if not success:
                break
            if frameCou % x == 0:
                # cv2.imwrite(self.media_path+'/B'+str(frameCou)+'.jpg', image)
                callbackRes = callback(image, frameCou)
                cleanedDM = []
                for dataMatch in callbackRes['data_matches']:
                    newDataMatch = {
                        'file_name': dataMatch['file_name'],
                        'x': dataMatch['x'],
                        'y': dataMatch['y'],
                        'width': dataMatch['width'],
                        'height': dataMatch['height'],
                    }
                    cleanedDM.append(newDataMatch)
                frameData.append({'frame': frameCou, 'data': cleanedDM})
                if show:
                    cv2.imshow('output', callbackRes['image'])
                    cv2.waitKey(10)
                print(f'Finished frame: {frameCou} at {timeNow()}')
            frameCou += 1
        videoCap.release()
        if show:
            with open(os.getcwd()+'/results.json', 'w') as fp:
                json.dump(frameData, fp)
        return frameData