import azure.functions as func
import json
import logging
import os
import random
import requests

from pymongo import MongoClient

client = MongoClient(os.environ["CONNECTION_STRING"])
music_db = client[os.environ["DATABASE_NAME"]]


def __get_tracks_ids(tr_pids):
    tracks = list(music_db['tracks'].find(
        {'pid' : {"$in" : tr_pids}},
    ))
    return {tr['pid']: tr['_id'] for tr in tracks}

def __get_tracks_info(track_ids):
    return list(music_db['tracks'].aggregate(
        [
            { 
                "$match":
                {
                    "_id" : {"$in" : track_ids}
                }
            },
            {
                "$lookup":
                {
                    "from": 'artists',
                    "localField": 'artist',
                    "foreignField": '_id',
                    "as": 'artist'
                }
            },
            {
                "$lookup":
                {
                    "from": 'albums',
                    "localField": 'album',
                    "foreignField": '_id',
                    "as": 'album'
                }
            }
        ]
    ))

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    global pl_pid
    try:
        pl_pid = int(req.route_params.get('id'))
    except:
        return func.HttpResponse(status_code=400)

    pl = music_db['playlists'].find_one({'pid' : pl_pid})
    if  pl != None:
        name = pl['name']
        known_tracks_set = set(pl['tracks'])
        
        body = {
            "action" : "make_prediction_user",
            "data" : pl_pid
        }
        
        body = json.dumps(body)
        headers = {"Content-Type": "application/json"}
        resp = requests.post(os.environ['MODEL_ENDPOINT'], body, headers=headers)
        
        execution_time = json.loads(resp.text)['execution_time']        
        logging.info(f'model endpoint execution time: {execution_time} s.')

        recomm_tracks  = json.loads(resp.text)['result']
        track_id_dict = __get_tracks_ids([tr['item_id'] for tr in recomm_tracks])
        recomm_tracks = [{'_id' : track_id_dict[tr['item_id']], 
                          'score' : tr['score']} 
                         for tr in recomm_tracks if tr['item_id'] in track_id_dict.keys()]
        recomm_tracks = [tr for tr in recomm_tracks if tr['_id'] not in known_tracks_set]

        recomm_tracks = __get_tracks_info([tr['_id'] for tr in recomm_tracks])[:256]
        
        init_num = len(known_tracks_set)
        if init_num < 20:
            init_num = 20
        end_num = init_num + 20
        if end_num > 200:
            end_num = 200

        recommPls = []
        for _ in range(5):
            r = random.randint(init_num,end_num)
            tracks = random.sample(recomm_tracks, r)
            tracks = [
                {
                    'name' : tr['name'], 'id' : "spotify:track:"+tr['_id'],
                    'album' : {'name': tr['album'][0]['name'], 'id': "spotify:album:"+tr['album'][0]['_id'],
                               'release_date' : tr['album'][0]['release_date'].strftime("%Y-%m-%d")},
                    'artist' : {'name' : tr['artist'][0]['name'], 'id' : "spotify:artist:"+tr['artist'][0]['_id']}
                }
                for tr in tracks]
            pl = {'name' : name, 
                  'tracks' : tracks}
            recommPls.append(pl)
    
    return func.HttpResponse(status_code=200, body=json.dumps(recommPls, indent=4))