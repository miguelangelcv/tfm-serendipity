import joblib
import json
import lightfm
import numpy as np
import os
import time

from flask import Flask, request
from scipy import sparse as sp
from scipy.sparse.construct import identity


app = Flask(__name__)

def init():
    global model
    global model_data
    global num_users
    global num_items
    global num_threads
    
    # AZUREML_MODEL_DIR is an environment variable created during deployment.
    # It is the path to the model folder (./azureml-models/$MODEL_NAME/$VERSION)
    # For multiple models, it points to the folder containing all deployed models (./azureml-models)
    model_path = "../model/model.pkl"
    model_data_path = "../model/model_data.pkl"
    
    model = joblib.load(model_path)
    model_data = joblib.load(model_data_path)
    
    num_users = len([x for x in model_data['playlist_features_names'] if "name:" in x])
    num_items = len([x for x in model_data['track_features_names'] if "track:" in x])
    
    num_threads = 3
    

# Obtiene de un modelo los items similares al indicado
# mediante la similaridad coseno
def similar_items(item_id, model, num_items, N=1000):
    """
    :param item_id: Item del que obtener similares.
    :param model: Modelo a emplear.
    :param N: (Opcional) Número de items similares, por defecto se devuelven todos.
    :return: Lista de tuplas en formato (PID,SCORE).
    """
    
    if N > 1000:
        N = 1000
    N += 200
    (item_biased, item_representations) = model.get_item_representations()
    
    # Cosine Similarity
    scores = item_representations.dot(item_representations[item_id])
    item_norms = np.linalg.norm(item_representations, axis=1)
    item_norms[item_norms == 0] = 1e-10    
    scores /= item_norms
    best = np.argpartition(scores, -N)[-N:]    
    result = sorted(zip(best, scores[best] / item_norms[item_id]),
                  key=lambda x: -x[1])
    N -= 200
    
    return [{'item' : int(t), 'score' : float(s)} for (t,s) in result if t < num_items and t != item_id][:N]


# Obtiene de un modelo los usuarios similares al indicado
# mediante la similaridad coseno
def similar_users(user_id, model, num_users, N=1000):
    """
    :param item_id: Usuario del que obtener similares.
    :param model: Modelo a emplear.
    :param num_items: Número total de usuarios
    :param N: (Opcional) Número de usuarios similares, por defecto se devuelven todos.
    :return: Lista de tuplas en formato (PID,SCORE).
    """
    
    if N > 1000:
        N = 1000
    N += 200
    
    (user_biased, user_representations) = model.get_user_representations()
    
    # Cosine Similarity
    scores = user_representations.dot(user_representations[user_id])
    user_norms = np.linalg.norm(user_representations, axis=1)
    user_norms[user_norms == 0] = 1e-10    
    scores /= user_norms
    best = np.argpartition(scores, -N)[-N:] 
    
    result = sorted(zip(best, scores[best] / user_norms[user_id]),
                  key=lambda x: -x[1])
    N -= 200
    
    return [{'user' : int(u), 'score' : float(s)} for (u,s) in result if u < num_users and u != user_id][:N]


def get_similar_user_tags(tag_id, model, N=100):
    # Define similarity as the cosine of the angle
    # between the tag latent vectors

    # Normalize the vectors to unit length
    tag_embeddings = (model.user_embeddings.T
                      / np.linalg.norm(model.user_embeddings, axis=1)).T

    query_embedding = tag_embeddings[tag_id]
    similarity = np.dot(tag_embeddings, query_embedding)
    most_similar = np.argsort(-similarity)[1:N+1]
    
    result = []
    for user_id in most_similar:
        result.append({'user_tag_id' : int(user_id), 'score' : float(similarity[user_id])})

    return result


def get_similar_item_tags(tag_id, model, N=100):
    # Define similarity as the cosine of the angle
    # between the tag latent vectors

    # Normalize the vectors to unit length
    tag_embeddings = (model.item_embeddings.T
                      / np.linalg.norm(model.item_embeddings, axis=1)).T

    query_embedding = tag_embeddings[tag_id]
    similarity = np.dot(tag_embeddings, query_embedding)
    most_similar = np.argsort(-similarity)[1:N+1]
    
    result = []
    for item_id in most_similar:
        result.append({'item_tag_id' : int(item_id), 'score' : float(similarity[item_id])})

    return result


def format_userfeats(userfeat_ids, num_user_features):
    normalised_val = 1.0 
    new_user_features = np.zeros(num_user_features)
    
    for i in userfeat_ids:
        new_user_features[i] = normalised_val
    
    new_user_features = sp.csr_matrix(new_user_features)
      
    return new_user_features


def make_newuser_recomm(userfeat_ids, model, i_features, num_items, n_recs=1000, n_threads=1):
    if n_recs > 1000: n_recs = 1000
        
    total_userfeats = len(model.get_user_representations()[0])
    new_user_features = format_userfeats(userfeat_ids, total_userfeats)
    
    scores = model.predict(0, np.arange(num_items), user_features=new_user_features, 
                           item_features=model_data['track_features'], num_threads=n_threads)
    items = list(np.argsort(scores)[::-1])[:n_recs]
    
    result = []    
    for item_id in items:
        result.append({'item_id' : int(item_id), 'score' : float(scores[item_id])})
        
    return result


def make_user_recomm(user_id, model, u_features, i_features, num_items, n_recs=1500, n_threads=1):
    if n_recs > 1500: n_recs = 1500
        
    scores = model.predict(user_id, np.arange(num_items), user_features=u_features, 
                           item_features=i_features, num_threads=n_threads)
    items = list(np.argsort(scores)[::-1])[:n_recs]
    
    result = []    
    for item_id in items:
        result.append({'item_id' : int(item_id), 'score' : float(scores[item_id])})
        
    return result


def run(raw_data):
    input_json = json.loads(raw_data)
    
    if all(k in input_json.keys() for k in ("data","action")):    
        data = input_json["data"]
        action = input_json["action"]
        start_time = time.time()
        response = {}    
        
        try:
            if action == 'similar_items':
                data = json.loads(raw_data)["data"]
                result = similar_items(data,model,num_items)
                response['result'] = result 
            elif action == 'similar_users':
                data = json.loads(raw_data)["data"]
                result = similar_users(data,model,num_users)
                response['result'] = result
            elif action == 'similar_item_tags':
                data = json.loads(raw_data)["data"]
                result = get_similar_item_tags(data,model)
                response['result'] = result
            elif action == 'similar_user_tags':
                data = json.loads(raw_data)["data"]
                result = get_similar_user_tags(data,model)
                response['result'] = result
            elif action == 'make_prediction_newuser':
                data = json.loads(raw_data)["data"]
                result = make_newuser_recomm(data, model, model_data['track_features'], 
                                             num_items, n_threads=num_threads)
                response['result'] = result
            elif action == 'make_prediction_user':
                data = json.loads(raw_data)["data"]
                result = make_user_recomm(data, model, model_data['playlist_features'], 
                                          model_data['track_features'], num_items,
                                          n_threads=num_threads)
                response['result'] = result
            else:
                response['error'] = "Wrong invocation."
            
        except Exception as e:
            response['error'] = str(e)
            
        response['execution_time'] = time.time() - start_time

        return json.dumps(response)
    else:
        return json.dumps({'error' : 'Wrong invocation.'})

@app.route('/', methods=['POST', 'GET'])
def index():
    return run(request.data)

if __name__ == "__main__":
    init()
    app.run(debug=True)