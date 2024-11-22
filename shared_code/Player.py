import requests
import json
import uuid


class Player:
    def __init__(self, username, password, games_played=0, total_score=0):
        self.id = str(uuid.uuid4())  
        self.username = username
        self.password = password
        self.games_played = games_played
        self.total_score = total_score

    def __str__(self):
        return f"""
        id = {self.id}
        username = {self.username}
        password = {self.password}
        games_played = {self.games_played}
        total_score = {self.total_score}
        """

    def from_dict(self, dict_player):
        required_keys = {'username', 'password', 'games_played', 'total_score'}
        if not required_keys.issubset(dict_player.keys()):
            raise ValueError("Input dict is not from a Player")
        
        self.id = dict_player.get('id', str(uuid.uuid4()))
        self.username = dict_player['username']
        self.password = dict_player['password']
        self.games_played = dict_player['games_played']
        self.total_score = dict_player['total_score']

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "games_played": self.games_played,
            "total_score": self.total_score
        }

    def to_json(self):
        return json.dumps(self.to_dict())

