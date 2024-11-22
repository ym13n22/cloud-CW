import unittest
import json
import requests
from azure.cosmos import CosmosClient
from shared_code.Player import Player

class TestUtilsPodium(unittest.TestCase):
    LOCAL_DEV_URL_PODIUM = "http://localhost:7071/api/utils/podium"
    PUBLIC_DEV_URL_PODIUM = "https://cw111.azurewebsites.net/api/utils/podium"
    TEST_URL_PODIUM = PUBLIC_DEV_URL_PODIUM

    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    PlayerDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PlayerContainerProxy = PlayerDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
    PromptContainerProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName']).get_container_client(settings['Values']['PromptContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    headers = {"x-functions-key": FunctionAppKey}


    def setUp_no_tiebreaks(self) -> None:
      # Clear previous data
      for item in self.PlayerContainerProxy.read_all_items():
          self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['username'])

      # Define and insert test players
      test_players = [
          {"id": "player-8", "username": "High-ppgr", "games_played": 5, "total_score": 50},  # ppgr = 10
          {"id": "player-9", "username": "Medium-ppgr", "games_played": 10, "total_score": 60}, # ppgr = 6
          {"id": "player-10", "username": "Low-ppgr", "games_played": 20, "total_score": 80},   # ppgr = 4
      ]

      # Insert each test player into the collection
      for player in test_players:
          self.PlayerContainerProxy.create_item(player)
      print("No tiebreaks test data setup completed.")


    def setUp_tiebreak_games_played_only(self) -> None:
      # Clear previous data
      for item in self.PlayerContainerProxy.read_all_items():
          self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['username'])

      # Define and insert test players
      test_players = [
          {"id": "player-11", "username": "Player-A", "games_played": 5, "total_score": 20},    # ppgr = 4
          {"id": "player-12", "username": "Player-B", "games_played": 10, "total_score": 40},   # ppgr = 4
          {"id": "player-13", "username": "Player-C", "games_played": 15, "total_score": 60}    # ppgr = 4
      ]

      # Insert each test player into the collection
      for player in test_players:
          self.PlayerContainerProxy.create_item(player)
      print(" tiebreaks test data setup completed.")

    def setUp_both_tiebreaks(self) -> None:
      # Clear previous data
      for item in self.PlayerContainerProxy.read_all_items():
          self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['username'])

      # Define and insert test players
      test_players = [
          {"id": "player-1", "username": "A-player", "games_played": 10, "total_score": 40},
          {"id": "player-2", "username": "B-player", "games_played": 20, "total_score": 80},
          {"id": "player-3", "username": "C-player", "games_played": 10, "total_score": 40},
          {"id": "player-4", "username": "D-player", "games_played": 10, "total_score": 80},
          {"id": "player-5", "username": "X-player", "games_played": 50, "total_score": 100},
          {"id": "player-6", "username": "Y-player", "games_played": 10, "total_score": 10},
          {"id": "player-7", "username": "Z-player", "games_played": 10, "total_score": 10},
      ]

      # Insert each test player into the collection
      for player in test_players:
          self.PlayerContainerProxy.create_item(player)
      print("Both tiebreaks test data setup completed.")



    def test_podium_no_tiebreaks(self):
        self.setUp_no_tiebreaks()
        headers = {"x-functions-key": self.FunctionAppKey}
        response = requests.get(self.TEST_URL_PODIUM, headers=headers)

        expected_output = {
            "gold": [
                {"username": "High-ppgr", "games_played": 5, "total_score": 50}
            ],
            "silver": [
                {"username": "Medium-ppgr", "games_played": 10, "total_score": 60}
            ],
            "bronze": [
                {"username": "Low-ppgr", "games_played": 20, "total_score": 80}
            ]
        }

        self.assertDictEqual(response.json(), expected_output)


    def test_podium_tiebreak_games_played_only(self):
        self.setUp_tiebreak_games_played_only()
        headers = {"x-functions-key": self.FunctionAppKey}
        response = requests.get(self.TEST_URL_PODIUM, headers=headers)

        expected_output = {
            "gold": [
                {"username": "Player-A", "games_played": 5, "total_score": 20},
                {"username": "Player-B", "games_played": 10, "total_score": 40},
                {"username": "Player-C", "games_played": 15, "total_score": 60}
            ],
            "silver": [],
            "bronze": []
        }

        self.assertDictEqual(response.json(), expected_output)


    def test_podium_both_tiebreaks(self):
        self.setUp_both_tiebreaks()
        headers = {"x-functions-key": self.FunctionAppKey}  # Add function key header if needed
        response = requests.get(self.TEST_URL_PODIUM, headers=headers)

        expected_output = {
            "gold": [
                {"username": "D-player", "games_played": 10, "total_score": 80}  # ppgr = 8
            ],
            "silver": [
                {"username": "A-player", "games_played": 10, "total_score": 40},  # ppgr = 4
                {"username": "C-player", "games_played": 10, "total_score": 40},
                {"username": "B-player", "games_played": 20, "total_score": 80}
            ],
            "bronze": [
                {"username": "X-player", "games_played": 50, "total_score": 100}  # ppgr = 2
            ]
        }

        self.assertDictEqual(response.json(), expected_output)


    
    def setUp_no_tiebreaks_with_outside_player(self) -> None:
        # Clear previous data
        for item in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['username'])

        # Define and insert test players
        test_players = [
            {"id": "player-8", "username": "High-ppgr", "games_played": 5, "total_score": 50},  # ppgr = 10
            {"id": "player-9", "username": "Medium-ppgr", "games_played": 10, "total_score": 60}, # ppgr = 6
            {"id": "player-10", "username": "Low-ppgr", "games_played": 20, "total_score": 80},   # ppgr = 4
            {"id": "player-outside", "username": "Outside-player", "games_played": 30, "total_score": 50}  # ppgr = 1.67
        ]

        # Insert each test player into the collection
        for player in test_players:
            self.PlayerContainerProxy.create_item(player)
        print("No tiebreaks test data with outside player setup completed.")

    # Case 2: Games played tiebreak only
    def setUp_tiebreak_games_played_only_with_outside_player(self) -> None:
        # Clear previous data
        for item in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['username'])

        # Define and insert test players
        test_players = [
            {"id": "player-12", "username": "Player-B", "games_played": 10, "total_score": 40},   # ppgr = 4
            {"id": "player-13", "username": "Player-C", "games_played": 15, "total_score": 60},   # ppgr = 4
            {"id": "player-11", "username": "Player-A", "games_played": 5, "total_score": 20},    # ppgr = 4
            
            {"id": "player-14", "username": "Player-D", "games_played": 7, "total_score": 21},    # ppgr = 3
            {"id": "player-15", "username": "Player-E", "games_played": 10, "total_score": 30},   # ppgr = 3

            {"id": "player-16", "username": "Player-F", "games_played": 10, "total_score": 20},   # ppgr = 2
            {"id": "player-17", "username": "Player-G", "games_played": 5, "total_score": 10},    # ppgr = 2
            
            {"id": "player-outside", "username": "Outside-player", "games_played": 10, "total_score": 10}  # ppgr = 1
        ]

        # Insert each test player into the collection
        for player in test_players:
            self.PlayerContainerProxy.create_item(player)
        print("Games played tiebreak test data with outside player setup completed.")

    # Case 3: Both tiebreaks
    def setUp_both_tiebreaks_with_outside_player(self) -> None:
        # Clear previous data
        for item in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['username'])

        # Define and insert test players
        test_players = [
            {"id": "player-1", "username": "A-player", "games_played": 10, "total_score": 40},
            {"id": "player-2", "username": "B-player", "games_played": 20, "total_score": 80},
            {"id": "player-3", "username": "C-player", "games_played": 10, "total_score": 40},
            {"id": "player-4", "username": "D-player", "games_played": 10, "total_score": 80},
            {"id": "player-5", "username": "X-player", "games_played": 50, "total_score": 100},
            {"id": "player-6", "username": "Outside-player", "games_played": 10, "total_score": 10},  # Outside player
            {"id": "player-7", "username": "Z-player", "games_played": 10, "total_score": 10},
        ]

        # Insert each test player into the collection
        for player in test_players:
            self.PlayerContainerProxy.create_item(player)
        print("Both tiebreaks test data with outside player setup completed.")

    # Tests
    def test_podium_no_tiebreaks_with_outside_player(self):
        self.setUp_no_tiebreaks_with_outside_player()
        response = requests.get(self.TEST_URL_PODIUM, headers=self.headers)

        expected_output = {
            "gold": [{"username": "High-ppgr", "games_played": 5, "total_score": 50}],
            "silver": [{"username": "Medium-ppgr", "games_played": 10, "total_score": 60}],
            "bronze": [{"username": "Low-ppgr", "games_played": 20, "total_score": 80}]
        }

        self.assertDictEqual(response.json(), expected_output)

    def test_podium_tiebreak_games_played_only_with_outside_player(self):
        self.setUp_tiebreak_games_played_only_with_outside_player()
        response = requests.get(self.TEST_URL_PODIUM, headers=self.headers)

        expected_output = {
            "gold": [
                {"username": "Player-A", "games_played": 5, "total_score": 20},
                {"username": "Player-B", "games_played": 10, "total_score": 40},
                {"username": "Player-C", "games_played": 15, "total_score": 60}
            ],
            "silver": [
                {"username": "Player-D", "games_played": 7, "total_score": 21},
                {"username": "Player-E", "games_played": 10, "total_score": 30}
            ],
            "bronze": [
                {"username": "Player-G", "games_played": 5, "total_score": 10},
                {"username": "Player-F", "games_played": 10, "total_score": 20}
            ]
        }


        self.assertDictEqual(response.json(), expected_output)

    def test_podium_both_tiebreaks_with_outside_player(self):
        self.setUp_both_tiebreaks_with_outside_player()
        response = requests.get(self.TEST_URL_PODIUM, headers=self.headers)

        expected_output = {
            "gold": [{"username": "D-player", "games_played": 10, "total_score": 80}],
            "silver": [
                {"username": "A-player", "games_played": 10, "total_score": 40},
                {"username": "C-player", "games_played": 10, "total_score": 40},
                {"username": "B-player", "games_played": 20, "total_score": 80}
            ],
            "bronze": [{"username": "X-player", "games_played": 50, "total_score": 100}]
        }

        self.assertDictEqual(response.json(), expected_output)



    def tearDown(self):
        print("Clearing up after test...")
        for doc in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=doc['id'], partition_key=doc['id'])

