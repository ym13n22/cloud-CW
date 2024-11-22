import unittest
import requests
import json
from azure.cosmos import CosmosClient
from shared_code.Player import Player

class TestPlayerUpdate(unittest.TestCase):
    LOCAL_DEV_URL_REGISTER = "http://localhost:7071/api/player/register"
    LOCAL_DEV_URL_UPDATE = "http://localhost:7071/api/player/update"
    PUBLIC_URL_UPDATE = "https://cw111.azurewebsites.net/api/player/update"
    PUBLIC_URL_REGISTER = "https://cw111.azurewebsites.net/api/player/register"
    

    # Load Cosmos settings
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    PlayerDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PlayerContainerProxy = PlayerDBProxy.get_container_client(settings['Values']['PlayerContainerName'])

    # Define a valid player for testing
    valid_player = Player(
        username="player",
        password="password1234",
        games_played=0,
        total_score=0
    )
    json_valid_player = valid_player.to_dict()

    @classmethod
    def setUpClass(cls):
        cls.FunctionAppKey = cls.settings['Values']['FunctionAppKey']
        cls.TEST_URL_REGISTER = f"{cls.PUBLIC_URL_REGISTER}?code={cls.FunctionAppKey}"
        cls.TEST_URL_UPDATE = f"{cls.PUBLIC_URL_UPDATE}?code={cls.FunctionAppKey}"

    def setUp(self):
        # Clear database items before each test
        for item in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['id'])
        
        # Register a valid player for testing update functionality
        requests.post(self.TEST_URL_REGISTER, json=self.json_valid_player)

    def test_player_update_valid(self):
        print("Testing valid player...")
        # Update player data
        valid_update1 = {
            "username": "player",
            "add_to_games_played": 1,
            "add_to_score": 10
        }
        valid_update2 = {
            "username": "player",
            "add_to_games_played": 1,
            "add_to_score": 20
        }
        
        # Send update requests
        response1 = requests.put(self.TEST_URL_UPDATE, json=valid_update1)
        print(f"Status Code: {response1.status_code}")
        print(f"Response Text: {response1.text}") 
        response2 = requests.put(self.TEST_URL_UPDATE, json=valid_update2)
        print(f"Status Code: {response2.status_code}")
        print(f"Response Text: {response2.text}") 

        # Check responses
        self.assertEqual(response1.json(), {"result": True, "msg": "OK"})
        self.assertEqual(response2.json(), {"result": True, "msg": "OK"})

        # Verify the player data was updated in CosmosDB
        query_result = self.PlayerContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.username = @username",
            parameters=[{"name": "@username", "value": "player"}],
            enable_cross_partition_query=True
        )
        query_result_list = list(query_result)
        self.assertEqual(len(query_result_list), 1)

        # Check updated fields in the result
        query_result_data = query_result_list[0]
        self.assertEqual(query_result_data['username'], "player")
        self.assertEqual(query_result_data['games_played'], 2)
        self.assertEqual(query_result_data['total_score'], 30)

    def test_player_update_invalid(self):
        print("Testing invalid player...")
        # Attempt to update a non-existent player
        non_existent_player_update = {
            "username": "nonExistentUser",
            "add_to_games_played": 1,
            "add_to_score": 100
        }
        response = requests.put(self.TEST_URL_UPDATE, json=non_existent_player_update)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}") 

        # Verify that response indicates failure
        self.assertEqual(response.json(), {"result": False, "msg": "Player does not exist"})

    def test_update_games_played_boundary_min(self):
        print("Testing games_played at minimum boundary...")
        update_data = {"username": "player", "add_to_games_played": 1, "add_to_score": 0}
        response = requests.put(self.TEST_URL_UPDATE, json=update_data)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})

    def test_update_games_played_below_min(self):
        print("Testing games_played below minimum boundary...")
        update_data = {"username": "player", "add_to_games_played": -1, "add_to_score": 0}
        response = requests.put(self.TEST_URL_UPDATE, json=update_data)
        self.assertEqual(response.json(), {"result": False, "msg": "Input less than 0"})

    def test_update_total_score_boundary_min(self):
        print("Testing total_score at minimum boundary...")
        update_data = {"username": "player", "add_to_games_played": 0, "add_to_score": 1}
        response = requests.put(self.TEST_URL_UPDATE, json=update_data)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})


    def test_update_total_score_below_min(self):
        print("Testing total_score below minimum boundary...")
        update_data = {"username": "player", "add_to_games_played": 0, "add_to_score": -1}
        response = requests.put(self.TEST_URL_UPDATE, json=update_data)
        self.assertEqual(response.json(), {"result": False, "msg": "Input less than 0"})



    def tearDown(self):
        # Clean up database items after each test
        for item in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['id'])
