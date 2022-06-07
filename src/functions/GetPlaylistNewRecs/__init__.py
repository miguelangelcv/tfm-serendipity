import azure.functions as func
import json
import logging
import os
import requests

from pymongo import MongoClient
from . import textprocessing, emojis

client = MongoClient(os.environ["CONNECTION_STRING"])
music_db = client[os.environ["DATABASE_NAME"]]


def __get_tracks_ids(tr_pids):
    tracks = list(music_db['tracks'].find(
        {'pid' : {"$in" : tr_pids}},
    ))
    return {tr['pid']: tr['_id'] for tr in tracks}

def __get_tracks_info(track_ids):
    agg_result = list(music_db['tracks'].aggregate(
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
    agg_result = {tr['_id'] : tr for tr in agg_result}

    return [agg_result[x] for x in track_ids if x in agg_result]

def __validate_json(val_json):
    is_valid = False
    if "name" in val_json.keys():
        if (type(val_json['name']) == str):
            is_valid = True
    return is_valid

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        req_body = json.loads(req.get_body())
    except:
        return func.HttpResponse(status_code=400)

    if __validate_json(req_body):
        # Obtenemos los emojis del nombre de la lista y sus significados de la BD
        emojis_pl = emojis.get_emojis_list(req_body['name'])
        emoji_results = music_db['emojiTranslations'].find({"emoji": { "$in": emojis_pl }})
        emoji_dict = { e['emoji'] : e['tags'] for e in emoji_results}

        tag_list = textprocessing.name_tokenizer(req_body['name'], emoji_dict)


        feats = list(music_db['playlistFeatures'].find(
            {'name' : {"$in" : tag_list}},
            {'pid' : 1, 'name': 1, '_id' : 0})
        )

        if len(feats) > 0:
            body = {
                'action': 'make_prediction_newuser',
                'data' : [x['pid'] for x in feats]
            }
        else:
            body = {}
        
        body = json.dumps(body)
        headers = {"Content-Type": "application/json"}
        
        try:
            resp = requests.post(os.environ['MODEL_ENDPOINT'], body, headers=headers)

            execution_time = json.loads(resp.text)['execution_time']
            logging.info(f'model endpoint execution time: {execution_time} s.')
        except:
            resp = None
        
        if resp != None:
            recomm_tracks  = json.loads(resp.text)['result']
            track_id_dict = __get_tracks_ids([tr['item_id'] for tr in recomm_tracks])
            recomm_tracks = [{'_id' : track_id_dict[tr['item_id']], 
                            'score' : tr['score']} 
                            for tr in recomm_tracks if tr['item_id'] in track_id_dict.keys()]

            recomm_tracks = __get_tracks_info([tr['_id'] for tr in recomm_tracks])

            result = {
                'feats' : [x['name'] for x in feats],
                'tracks' : [
                    {
                        'name' : tr['name'], 'id' : "spotify:track:"+tr['_id'],
                        'album' : {'name': tr['album'][0]['name'], 'id': "spotify:album:"+tr['album'][0]['_id'],
                                'release_date' : tr['album'][0]['release_date'].strftime("%Y-%m-%d")},
                        'artist' : {'name' : tr['artist'][0]['name'], 'id' : "spotify:artist:"+tr['artist'][0]['_id']}
                    }
                    for tr in recomm_tracks[:100]
                ]

            }
            
            return func.HttpResponse(status_code=200, body=json.dumps(result, indent=4))
        else:
            return func.HttpResponse(status_code=503)