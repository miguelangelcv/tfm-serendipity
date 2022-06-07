import azure.functions as func
import json
import logging
import os

from pymongo import MongoClient

client = MongoClient(os.environ["CONNECTION_STRING"])
music_db = client[os.environ["DATABASE_NAME"]]

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    global pl_pid_list
    try:
        pl_pid_list = json.loads(req.get_body())['pids']
    except:
        return func.HttpResponse(status_code=400, body=json.dumps({}))

    result = list(music_db['playlists'].aggregate(
        [
            { "$match": {'pid' : {"$in" : pl_pid_list}} },
            { "$lookup": 
                {
                    "from": 'tracks',
                    "localField": 'tracks',
                    "foreignField": '_id',
                    "as": 'tracks'
                }
            },
            { "$unwind": "$tracks" },
            { "$lookup": 
                {
                    "from": 'artists',
                    "localField": 'tracks.artist',
                    "foreignField": '_id',
                    "as": 'tracks.artist'
                }
            },
            { "$lookup": 
                {
                    "from": 'albums',
                    "localField": 'tracks.album',
                    "foreignField": '_id',
                    "as": 'tracks.album'
                }
            },
            {
                "$group": 
                {
                    "_id" : "$_id",
                    "pid": { "$first": "$pid" },
                    "name" : {"$first" : "$name"},
                    "tracks" : { "$push": "$tracks" }
                }
            }
        ]
    ))

    pls_info_list = []

    for pl in result :
        pl_info = {
            'pid' : pl['pid'],
            'name' : pl['name'],
            'tracks' : [
                {
                    'name' : tr['name'], 'id' : tr['_id'],
                    'album' : {'name': tr['album'][0]['name'], 'id': "spotify:album:"+tr['album'][0]['_id'],
                               'release_date' : tr['album'][0]['release_date'].strftime("%Y-%m-%d")},
                    'artist' : {'name' : tr['artist'][0]['name'], 'id' : tr['artist'][0]['_id']}
                }
                for tr in pl['tracks']
            ]
        }
        pls_info_list.append(pl_info)

    return func.HttpResponse(status_code=200, body=json.dumps({'playlists' : pls_info_list},indent=4).encode('utf8'))