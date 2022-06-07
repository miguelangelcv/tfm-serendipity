import re
import os

from . import emojis
from nltk.tokenize import word_tokenize
from nltk.downloader import download as nltk_download

nltk_download("punkt")

def replace_apostrophe(text):
    # Como caso excepcional, vamos a hacer que el género R'n'B  se conserve como
    # una única palabra, rnb.
    if text.lower() == "r'n'b":
        return "rnb"
    
    # Adaptamos décadas como 1990's ó 90's para que aparezcan como
    # 1990s ó 90s.
    text = re.sub(r"([0-9]+)'s", r'\1s', text)
    text = text.replace("'s ", " ")
    
    text = re.sub(r"([0-9]+)´s", r'\1s', text)
    text = text.replace("´s ", " ")
    
    return text


def dot_remover(text):
    # Si el texto contiene un punto, realiza la comprobación.
    if "." in text:
        d = dict()
        
        for token in word_tokenize(text):
            cond_1 = "." in token
            cond_2 = len(token) > 2
            cond_3 = token.count('.') >= int(len(token)/2)
            cond_4 = not(token.count('.') == 1 and token.replace(".","").isnumeric())
            # Comprobamos si la palabra es separada por puntos.
            if all([cond_1, cond_2, cond_3, cond_4]):
                d[token] = token.replace('.','')
            else:
                # Comprobamos si la palabra del texto es un número.
                result = re.match(r"^[0-9]+([,.][0-9]+)?$", token)
                if result != None:
                    d[result.string] = result.string.replace(",","{dot}").replace(".","{dot}")

        for k,v in d.items():
            text = text.replace(k,v)
        
        text = text.replace("."," ")
        text = text.replace("{dot}",".")
        
    return text


def name_tokenizer(name, emoji_dict):

    emoji_list = emojis.get_emojis_list(name)
    
    name = str(name).lower()
    name = replace_apostrophe(name)
    name = dot_remover(name)
    name = re.sub(r"[~_]", ' ', name)
    name = re.sub(r"[^\w\s\.]", ' ', name)
    
    tokens = list()
    for token in word_tokenize(name):
        token = emojis.remove_emojis(token)
        token = re.sub(r'\s+', ' ', token).strip()
        tokens.append(token)
    
    emojis_translations = set()
    for e in emoji_list:
        if e in emoji_dict:
            emojis_translations.update(emoji_dict[e][:2])
        else:
            emojis_translations.add(e)
            
    for t in emojis_translations:
        if t not in tokens:
            tokens.append(t)
    
    return tokens
