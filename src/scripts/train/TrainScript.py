
import joblib
import numpy as np
import os
import pickle
import sys
import time

from azureml.core import Workspace
from azureml.core.authentication import AzureCliAuthentication
from azureml.core.model import Model
from lightfm import LightFM
from modules.TelegramBot import telegram_bot_sendtext


PROCESS_NANE = "TrainVM"
SEED = 1


def train_model(model_file, model_data_file, model_storage_path, num_epochs, num_threads):
    if not os.path.isdir(model_storage_path):
        os.mkdir(model_storage_path)
    model_file_path = os.path.join(model_storage_path,f"{model_file}")

    with open(model_data_file, "rb") as read_file:
        mpd_lfm_dict = pickle.load(read_file)

    interactions_weights = None
    if "playlist_interactions_weights" in mpd_lfm_dict.keys():
        interactions_weights = mpd_lfm_dict['playlist_interactions_weights']

        
    model = LightFM(loss='warp', no_components=200, max_sampled=30, random_state=SEED)

    ## Entrenamiento del modelo ##
    message = f"Comienza el entrenamiento."
    print(message)
    telegram_bot_sendtext(message, PROCESS_NANE) 

    start_time = time.time()
    train_error = False
    try:
        model.fit(interactions=mpd_lfm_dict['playlist_interactions'],
                sample_weight=interactions_weights, 
                item_features=mpd_lfm_dict['track_features'], 
                user_features=mpd_lfm_dict['playlist_features'],
                epochs=num_epochs, num_threads=num_threads, 
                verbose=True)
        
        duration = (time.time() - start_time)
        duration = np.round(duration/60,2)

        message = f"Entrenamiento completado. Tiempo empleado: {duration} min."
        print(message)
        telegram_bot_sendtext(message, PROCESS_NANE) 
    except Exception as e:
        message = f"ERROR: Se ha producido un error durante el proceso de entrenamiento ({str(e)})"
        telegram_bot_sendtext(message, PROCESS_NANE)   
        print(message)
        return        
    
    ## Almacenamiento del modelo ##
    try:
        print("Almacenando modelo...")
        telegram_bot_sendtext("Almacenando modelo...", PROCESS_NANE)
        joblib.dump(model, open(model_file_path, 'wb'))
    except Exception as e:
        message = f"ERROR: El modelo no ha podido ser almacenado ({str(e)})"
        telegram_bot_sendtext(message, PROCESS_NANE)
        print(message)
        return

    ## Comprobación del modelo almacenado ##
    try:
        joblib.load(open(model_file_path, 'rb'))
        print('Modelo almacendo correctamente')
        telegram_bot_sendtext('Modelo almacenado correctamente', PROCESS_NANE)
    except Exception as e:
        message = f"ERROR: El modelo no se ha almacenado correctamente ({str(e)})"
        telegram_bot_sendtext(message, PROCESS_NANE)
        print(message)


def register_model(model_name, model_path):
    cli_auth = AzureCliAuthentication()
    
    subscription_id = os.environ['AZ_SUBSCRIPTION_ID'] # Identificador de nuestra suscripción
    resource_group = os.environ['AZ_RESOURCE_GROUP'] # Nombre del grupo de recursos donde esta el área de trabajo
    workspace_name = os.environ['AZ_WORKSPACE_NAME'] # Nombre del área de trabajo

    ws = Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)
    ws.write_config()

    print("Registrando modelo...")
    telegram_bot_sendtext("Registrando modelo...", PROCESS_NANE)
    try:
        model = Model.register(
            workspace = ws,
            model_path = model_path,
            model_name = model_name,
            model_framework="LightFM",
            model_framework_version="1.16.0",
            description = "Serenditipy LightFM model for playlists recommendation (tracks)"
        )

        print("Modelo registrado.")
        telegram_bot_sendtext("Modelo registrado.", PROCESS_NANE)
    except Exception as e:
        message = f"ERROR: El modelo no ha podido ser registrado: ({str(e)})"
        telegram_bot_sendtext(message, PROCESS_NANE)
        print(message)



if __name__ == "__main__":
    if len(sys.argv) > 5:
        try:
            model_name = sys.argv[1]
            model_file = sys.argv[2]
            model_data_file = sys.argv[3]
            model_storage_folder = sys.argv[4]
            num_epochs = int(sys.argv[5])

            if len(sys.argv) > 6:
                num_threads = int(sys.argv[6])
            else:
                num_threads = 1

            train_model(model_file, model_data_file, model_storage_folder, num_epochs, num_threads)
            register_model(model_name,model_storage_folder)


        except Exception as e:
            print(f"ERROR: {str(e)}")
    
    else:
        print("ERROR: Invalid number of arguments.\nRequired -> model_name, model_file, model_data_file, model_storage_folder, num_epochs")
```
