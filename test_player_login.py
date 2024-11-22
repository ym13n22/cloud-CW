import unittest
import requests
import json
from azure.cosmos import CosmosClient
from shared_code.Player import Player

class TestPlayerLogin(unittest.TestCase):
    LOCAL_DEV_URL_LOGIN = "http://localhost:7071/api/player/login"
    LOCAL_DEV_URL_REGISTER = "http://localhost:7071/api/player/register"
    PUBLIC_URL_LOGIN = "https://cw111.azurewebsites.net/api/player/login"
    PUBLIC_URL_REGISTER = "https://cw111.azurewebsites.net/api/player/register"
    
    TEST_URL_LOGIN = PUBLIC_URL_LOGIN
    TEST_URL_REGISTER = PUBLIC_URL_REGISTER

    # Load Cosmos settings
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    PlayerDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PlayerContainerProxy = PlayerDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    # Define a valid player
    valid_player = Player(username="validUser", password="password123", games_played=0, total_score=0)
    json_valid_player = valid_player.to_dict()

    def setUp(self):
        # Ensure the test database is clear and add a valid player for login tests
        for item in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['id'])
        
        # Register a valid player in the database
        requests.post(
            self.TEST_URL_REGISTER,
            json=self.json_valid_player,
            params={"code": self.FunctionAppKey}
        )

    def test_player_login_valid(self):
        print("Testing valid player...")
        # Test login with correct credentials
        valid_login = {"username": "validUser", "password": "password123"}
        response = requests.get(
            self.TEST_URL_LOGIN,
            json=valid_login,
            params={"code": self.FunctionAppKey}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}") 
        dict_response = response.json()
        
        self.assertTrue(dict_response['result'])
        self.assertEqual(dict_response['msg'], "OK")

    def test_player_login_invalid_username(self):
        print("Testing invalid player username...")
        # Test login with incorrect username
        invalid_username = {"username": "invalidUser", "password": "password123"}
        response = requests.get(
            self.TEST_URL_LOGIN,
            json=invalid_username,
            params={"code": self.FunctionAppKey}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}") 
        dict_response = response.json()

        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], "Username or password incorrect")

    def test_player_login_invalid_password(self):
        print("Testing invalid player password...")
        # Test login with incorrect password
        invalid_password = {"username": "validUser", "password": "wrongPassword"}
        response = requests.get(
            self.TEST_URL_LOGIN,
            json=invalid_password,
            params={"code": self.FunctionAppKey}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}") 
        dict_response = response.json()
        
        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], "Username or password incorrect")

    def tearDown(self):
        # Clean up database items after each test
        for doc in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=doc['id'], partition_key=doc['id'])
