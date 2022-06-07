import emoji

# Comprueba si un carácter es un emoticono
def is_emoji(char):
    return char in emoji.UNICODE_EMOJI['en']

# Obtiene la lista de emoticonos que aparecen en un texto dado
def get_emojis_list(text):
    text_chars = list(text)
    emojis_set = set()    
    for char in text_chars:
        if is_emoji(char):
            emojis_set.add(char)            
    return list(emojis_set)

# Devuelve un string con los emoticonos que aparecen en un texto dado
def get_emojis_string(text):
    emojis_list = get_emojis_list(text)
    return "".join(emojis_list)

# Comprueba si un texto tiene emoticonos
def has_emojis(text):
    return len(get_emojis_list(text)) > 0

# Elimina los emoticonos de un texto
def remove_emojis(text):
    return emoji.get_emoji_regexp().sub(u'', text)

# De una lista de cadenas, devuelve aquellas que contienen
# el emoticono indicado
def get_names_with_emoji(emj, names):
    names_list = []
    
    if is_emoji(emj):
        for name in names:
            if emj in name:
                names_list.append(name)
    else:
        raise Exception("'{}' no es un emoji.".format(emj))
        
    return names_list