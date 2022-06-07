
import sys

from pymongo import MongoClient
from pymongo import errors as mongoerrors


MUSIC_DB_NAME = "music"
MUSIC_DB_COLLECTIONS = ["artists", "albums", "tracks", "genres", 
                        "knownPlaylists", "newPlaylists", "mlPlaylists",
                        "playlistFeatures", "trackFeatures"]


def create_db(connection_string):
    client = MongoClient(connection_string)
    
    try:
        client.server_info()
    except mongoerrors.ServerSelectionTimeoutError as err:
        print("ERROR: Connection string is not valid or db is not available.")
        return

    music_db = client['music']

    for collection in MUSIC_DB_COLLECTIONS:
        if collection not in music_db.list_collection_names():
            music_db.create_collection(collection)

def main(argv):
    if len(argv) > 0:
        connection_string = argv[0]
        create_db(connection_string)
    else:
        print("ERROR: Connection string is required.")
    

if __name__ == "__main__":
   main(sys.argv[1:])
