import azure.functions as func
import logging
import json
import spotipy

DESCRIPTION = "Esta playlist ha sido recomendada por 'Serendipity'"

def __is_valid_json(val_json):
    is_valid = False
    if all(k in val_json.keys() for k in ("user_id","token","pl_name", "pl_tracks")):
        cond1 = type(val_json['user_id']) == str
        cond2 = type(val_json['user_id']) == str
        cond3 = type(val_json['pl_name']) == str
        cond4 = type(val_json['pl_tracks']) == list
        if all([cond1,cond2,cond3,cond4]):
            is_valid = True
    return is_valid

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    global token
    global id
    req_json = json.loads(req.get_body())
    if __is_valid_json(req_json):
        try:
            sp = spotipy.Spotify(auth=req_json['token'])
            new_playlist = sp.user_playlist_create(req_json['user_id'], req_json['pl_name'], 
                                                description=DESCRIPTION)
            result = sp.user_playlist_add_tracks(req_json['user_id'], new_playlist['id'], req_json['pl_tracks'])
        except Exception as e:
            logging.info(f"Error at 'PostNewPlaylist' {e}")
            return func.HttpResponse(status_code=401)
        
        return func.HttpResponse(status_code=200,
                                 body=json.dumps({'pl_id' : new_playlist['id'],
                                                  'pl_name' : req_json['pl_name'],
                                                  'pl_uri': new_playlist['uri'],
                                                  'pl_url' : new_playlist['external_urls']['spotify']}
                                                )
                                )
    else:
        return func.HttpResponse(status_code=400)