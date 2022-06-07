import azure.functions as func
import json
import logging
import os

from pymongo import MongoClient

client = MongoClient(os.environ["CONNECTION_STRING"])
music_db = client[os.environ["DATABASE_NAME"]]

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    global pl_pid
    try:
        pl_pid = int(req.route_params.get('id'))
    except:
        return func.HttpResponse(status_code=400, body=json.dumps({}))

    result = list(music_db['playlists'].aggregate(
        [
            { "$match": {'pid' : pl_pid} },
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
    if len(result) == 0:
        return func.HttpResponse(status_code=404)
    else:        
        pl_info = {
            'pid' : result[0]['pid'],
            'name' : result[0]['name'],
            'tracks' : [
                {
                    'name' : tr['name'], 'id' : "spotify:track:"+tr['_id'],
                    'album' : {'name': tr['album'][0]['name'], 'id': "spotify:album:"+tr['album'][0]['_id'],
                               'release_date' : tr['album'][0]['release_date'].strftime("%Y-%m-%d")},
                    'artist' : {'name' : tr['artist'][0]['name'], 'id' : "spotify:artist:"+tr['artist'][0]['_id']}
                }
                for tr in result[0]['tracks']
            ]
        }
        return func.HttpResponse(status_code=200, body=json.dumps(pl_info,indent=4).encode('utf8'))