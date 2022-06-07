import azure.functions as func
import json
import logging
import os
import requests

from pymongo import MongoClient

client = MongoClient(os.environ["CONNECTION_STRING"])
music_db = client[os.environ["DATABASE_NAME"]]

def __get_tracks_ids(tr_pids):
    tracks = list(music_db['tracks'].find(
        {'pid' : {"$in" : tr_pids}},
        {'_id' : 1, 'pid' : 1}
    ))
    return {tr['pid']: tr['_id'] for tr in tracks}

def __get_tracks_info(track_ids):
    agg_result = list(music_db['tracks'].aggregate(
        [
            { 
                "$match":
                {
                    "_idº" : {"$in" : track_ids}
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
    agg_result = {tr['_id'] : tr for tr in agg_result}

    return [agg_result[x] for x in track_ids if x in agg_result]


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    global pl_pid
    try:
        tr_id = req.route_params.get('id')
    except:
        return func.HttpResponse(status_code=400)

    db_result = music_db['tracks'].find_one({'_id' : tr_id})
    if  db_result != None:
        body = {
            "action" : "similar_items",
            "data" : db_result['pid']
        }
        
        body = json.dumps(body)
        headers = {"Content-Type": "application/json"}
        resp = requests.post(os.environ['MODEL_ENDPOINT'], body, headers=headers)

        execution_time = json.loads(resp.text)['execution_time']
        
        logging.info(f'model endpoint execution time: {execution_time} s.')
        recomm_tracks  = json.loads(resp.text)['result']
        track_id_dict = __get_tracks_ids([tr['item'] for tr in recomm_tracks])
        recomm_tracks = [{'_id' : track_id_dict[tr['item']], 
                          'score' : tr['score']} 
                         for tr in recomm_tracks if tr['item'] in track_id_dict.keys()]
        """
        recomm_tracks = __get_tracks_info([tr['_id'] for tr in recomm_tracks[:1]])

        pl_info = {
            'tracks' : [
                {
                    'name' : tr['name'], 'id' : "spotify:track:"+tr['_id'],
                    'album' : {'name': tr['album'][0]['name'], 'id': "spotify:album:"+tr['album'][0]['_id'],
                               'release_date' : tr['album'][0]['release_date'].strftime("%Y-%m-%d")},
                    'artist' : {'name' : tr['artist'][0]['name'], 'id' : "spotify:artist:"+tr['artist'][0]['_id']}
                }
                for tr in recomm_tracks
            ]
        }
        """
    else:
        recomm_tracks = []
        pl_info = {}

    return func.HttpResponse(status_code=200, body=json.dumps({'results': recomm_tracks}, indent=4))