import json
import cv2
import pytesseract as pyt
import requests
from functools import reduce
from services import textDataFunctions as TDF

# Not sure (Measures the distance between two separate instances of recorded text)
def gaps_distance(data_instances):
    sum_total = 0
    prev_end = 0
    for i in [[i[6], i[8]] for i in data_instances]:
        if prev_end == 0:
            prev_end = i[0]+i[1]
        else:
            sum_total += i[0]-prev_end
    return sum_total

# Gets the image data and preprocesses it

def sendResponseToBackend(result):
    # send an http post requst to https://voon-demo.herokuapp.com/v1/graphql with headers and a body
    # json to string

    schema = '''
    mutation MyMutation($fps: Int!, $url: String!) {
        makeFileSnippet(fps: $fps, url: $url) {
            videoId
        }
    }
    ''' 

    query = {
        "query": schema,
        "variables": result
    }
    headers = {
        'Content-Type': 'application/json',
        'x-hasura-admin-secret': 'secret'
    }
    response = requests.post('https://voon-demo.herokuapp.com/v1/graphql', headers=headers, json=query)
    return response.json()
    
def gather_image_data(image):

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image_data = pyt.image_to_data(image)
    image_data = image_data.splitlines()

    processed_data = []
    for text_data_str in image_data[1:]:
        text_data = text_data_str.split()
        text_data[6], text_data[7], text_data[8], text_data[9] = int(text_data[6]), int(text_data[7]), int(text_data[8]), int(text_data[9])
        if len(text_data) == 12 and len(text_data[11]) > 3:
            processed_data.append(text_data)
            
    return processed_data

def amalgamated_data_ins(data_instances, file_name):
    result = {'file_name': file_name}
    min_x = reduce(lambda a, b: a if a < b else b, [i[6] for i in data_instances])
    min_y = reduce(lambda a, b: a if a < b else b, [i[7] for i in data_instances])
    w_each_sum = reduce(lambda a, b: a + b, [i[8] for i in data_instances])
    w_start_sum = gaps_distance(data_instances)
    w_sum = w_each_sum+w_start_sum
    # h difference should be considered to determine if its stacked
    h_max = reduce(lambda a, b: a if a > b else b, [i[9] for i in data_instances])
    result['x'] = min_x
    result['y'] = min_y
    result['width'] = w_sum
    result['height'] = h_max
    combined_text = reduce(lambda a, b: a + b, [i[11] for i in data_instances])
    result['unfinished'] = True if combined_text[-2:] == '..' else False
    result['text'] = TDF.space_clone_less(combined_text)
    result['indexes'] = (data_instances[0][-1], data_instances[-1][-1])
    return result

def index_in_use(data_ins, data_matches):
    for amalgamated_data in data_matches:
        if amalgamated_data['indexes'][0] <= data_ins[-1] <= amalgamated_data['indexes'][1]:
            return True
    return False