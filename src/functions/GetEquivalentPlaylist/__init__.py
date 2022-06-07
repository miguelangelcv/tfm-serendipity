import azure.functions as func
import json
import logging
import os

from . import textprocessing, emojis
from pymongo import MongoClient

client = MongoClient(os.environ["CONNECTION_STRING"])
music_db = client[os.environ["DATABASE_NAME"]]

def __validate_json(val_json):
    is_valid = False
    if all(k in val_json.keys() for k in ("name","tracks")):
        if (type(val_json['name']) == str) and (type(val_json['tracks']) == list):
            is_valid = True
    return is_valid

def __find_equivalent_playlist(tags,tracks):
    result = music_db['playlists'].find_one(
        {
            "$or" : [
                {"$and" : [{"tags" : {"$eq": tags}}, {"tracks": {"$eq": tracks}}]},
                {"$and" : [{"tags" : {"$all": tags}}, {"tracks": {"$eq": tracks}}]},
                {"$and" : [{"tags" : {"$all": tags}}, {"tracks": {"$all": tracks}}]},
                {"$and" : [{"tags" : {"$in": tags}}, {"tracks": {"$eq": tracks}}]},
                {"$and" : [{"tags" : {"$in": tags}}, {"tracks": {"$all": tracks}}]},
                {"tracks": {"$eq": tracks}},
                {"tracks": {"$all": tracks}}
            ]
        },
        {
            'name':1, 'tracks': 1, 'pid' : 1
        }
    )
    return result

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        req_body = json.loads(req.get_body())
    except:
        return func.HttpResponse(status_code=400, body=json.dumps({}))

    if __validate_json(req_body):
        # Obtenemos los emojis del nombre de la lista y sus significados de la BD
        emojis_pl = emojis.get_emojis_list(req_body['name'])
        emoji_results = music_db['emojiTranslations'].find({"emoji": { "$in": emojis_pl }})
        emoji_dict = { e['emoji'] : e['tags'] for e in emoji_results}

        tag_list = textprocessing.name_tokenizer(req_body['name'], emoji_dict)

        track_list = req_body['tracks']

        result = __find_equivalent_playlist(tag_list,track_list)

        if result != None:
            result['_id'] = str(result['_id'])
            result['track_ids'] = result['tracks']
            del result['tracks']
            response = func.HttpResponse(status_code=200, body=json.dumps(result,indent=4)
            )
        else:
            response = func.HttpResponse(status_code=404)
    else:
        response = func.HttpResponse(status_code=400)

    return response