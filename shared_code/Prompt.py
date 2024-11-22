import requests
import json
import uuid


class Prompt:
    def __init__(self, username, texts):

        self.id = str(uuid.uuid4()) 
        self.username = username
        self.texts = texts  
        

    def __str__(self):

        texts_str = ", ".join([f"({t['language']}: {t['text']})" for t in self.texts])
        return f"ID: {self.id}, Username: {self.username}, Texts: [{texts_str}]"

    def to_dict(self):

        return {
            "id": self.id,
            "username": self.username,
            "texts": [{"language": t["language"], "text": t["text"]} for t in self.texts]
        }

    def to_json(self):

        return json.dumps(self.to_dict())


    def from_dict(self, dict_prompt):

        required_keys = {'id', 'username', 'texts'}
        if not required_keys.issubset(dict_prompt.keys()):
            raise ValueError("Input dict is not from a Prompt")

        # Set instance attributes based on dict input
        self.id = dict_prompt['id']
        self.username = dict_prompt['username']
        self.texts = dict_prompt['texts']
        
