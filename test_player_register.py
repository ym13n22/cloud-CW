import unittest
import requests
import json
from azure.cosmos import CosmosClient
from shared_code.Player import Player

class TestPlayerRegister(unittest.TestCase):
    LOCAL_DEV_URL = "http://localhost:7071/api/player/register"
    PUBLIC_DEV_URL = "https://cw111.azurewebsites.net/api/player/register"
    TEST_URL = PUBLIC_DEV_URL 

    # Load Cosmos settings
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    PlayerDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PlayerContainerProxy = PlayerDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    headers = {"x-functions-key": FunctionAppKey}

    valid_player = Player(
        username="validUser",
        password="password123"
    )

    def setUp(self):
        for item in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['id'])


    def test_player_register_valid(self):
        print("Testing valid player when DB is empty...")
        response = requests.post(self.TEST_URL, json=self.valid_player.to_dict(), headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")  

        dict_response = response.json()
        
        self.assertTrue(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'OK')
        
        query_result = self.PlayerContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.username = @username",
            parameters=[{"name": "@username", "value": "validUser"}],
            enable_cross_partition_query=True
        )
        query_result_list = list(query_result)
        self.assertEqual(len(query_result_list), 1)


    def test_player_register_duplicate(self):
        print("Testing duplicate player...")
        duplicate_player1 = Player(username="duplicateUser", password="password123")
        duplicate_player2 = Player(username="duplicateUser", password="anotherPass123")

        # Send requests to register the duplicate players
        response1 = requests.post(self.TEST_URL, json=duplicate_player1.to_dict(), headers=self.headers)
        print(f"Status Code: {response1.status_code}")
        print(f"Response Text: {response1.text}")

        response2 = requests.post(self.TEST_URL, json=duplicate_player2.to_dict(), headers=self.headers)
        print(f"Status Code: {response2.status_code}")
        print(f"Response Text: {response2.text}")

        # Parse JSON responses
        dict_response1 = response1.json()
        dict_response2 = response2.json()

        # Assert the first response was successful
        self.assertTrue(dict_response1['result'])
        self.assertEqual(dict_response1['msg'], 'OK')

        # Assert the second response failed due to duplicate username
        self.assertFalse(dict_response2['result'])
        self.assertEqual(dict_response2['msg'], 'Username already exists')

        

    def test_player_register_nonempty(self):
        print("Testing valid player when DB is not empty...")
        duplicate_player1 = Player(username="User1", password="password123")
        duplicate_player2 = Player(username="User2", password="anotherPass123")

        # Register the first player
        response1 = requests.post(self.TEST_URL, json=duplicate_player1.to_dict(), headers=self.headers)
        print(f"Response Text: {response1.text}")

        # Register the second player
        response2 = requests.post(self.TEST_URL, json=duplicate_player2.to_dict(), headers=self.headers)
        print(f"Response Text: {response2.text}")

        # Validate responses for each registration
        dict_response1 = response1.json()
        dict_response2 = response2.json()

        self.assertTrue(dict_response1['result'])
        self.assertEqual(dict_response1['msg'], 'OK')

        self.assertTrue(dict_response2['result'])
        self.assertEqual(dict_response2['msg'], 'OK')

        # Query the database for each user to verify they were added correctly
        query_result1 = self.PlayerContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.username = @username",
            parameters=[{"name": "@username", "value": "User1"}],
            enable_cross_partition_query=True
        )
        query_result2 = self.PlayerContainerProxy.query_items(
            query="SELECT * FROM c WHERE c.username = @username",
            parameters=[{"name": "@username", "value": "User2"}],
            enable_cross_partition_query=True
        )

        # Convert results to lists and check that each player was added once
        query_result_list1 = list(query_result1)
        query_result_list2 = list(query_result2)
        self.assertEqual(len(query_result_list1), 1)
        self.assertEqual(len(query_result_list2), 1)

 
        

    def test_player_register_short_username(self):
        print("Testing player with short username...")
        invalid_username_short = Player(username= "usr", password= "password123")

        response = requests.post(self.TEST_URL, json=invalid_username_short.to_dict(), headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}") 

        dict_response = response.json()

        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'Username less than 5 characters or more than 15 characters')


    def test_player_register_long_username(self):
        print("Testing player with long username...")
        invalid_username_long = Player(username= "thisusernameistoolong", password= "password123")

        response = requests.post(self.TEST_URL, json=invalid_username_long.to_dict(), headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}") 


        dict_response = response.json()

        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'Username less than 5 characters or more than 15 characters')


    def test_player_register_short_password(self):
        print("Testing player with short password...")
        invalid_password_short = Player(username= "validUser", password= "pass123")

        response = requests.post(self.TEST_URL, json=invalid_password_short.to_dict(), headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}") 


        dict_response = response.json()


        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'Password less than 8 characters or more than 15 characters')


    def test_player_register_long_password(self):
        print("Testing player with long password...")
        invalid_password_long = Player(username= "validUser", password= "12345678901234567890")

        response = requests.post(self.TEST_URL, json=invalid_password_long.to_dict(), headers=self.headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}") 


        dict_response = response.json()

   
        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'Password less than 8 characters or more than 15 characters')

    
    def test_username_min_boundary(self):
        print("Testing username at minimum boundary...")
        valid_username_min = Player(username="user5", password="password123")
        response = requests.post(self.TEST_URL, json=valid_username_min.to_dict(), headers=self.headers)
        dict_response = response.json()

        self.assertTrue(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'OK')


    def test_username_max_boundary(self):
        print("Testing username at maximum boundary...")
        valid_username_max = Player(username="user12345678901", password="password123")
        response = requests.post(self.TEST_URL, json=valid_username_max.to_dict(), headers=self.headers)
        dict_response = response.json()

        self.assertTrue(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'OK')

    def test_username_below_min_boundary(self):
        print("Testing username below minimum boundary...")
        invalid_username_below_min = Player(username="usr", password="password123")
        response = requests.post(self.TEST_URL, json=invalid_username_below_min.to_dict(), headers=self.headers)
        dict_response = response.json()

        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'Username less than 5 characters or more than 15 characters')

    def test_username_above_max_boundary(self):
        print("Testing username above maximum boundary...")
        invalid_username_above_max = Player(username="thisusernameistoolong", password="password123")
        response = requests.post(self.TEST_URL, json=invalid_username_above_max.to_dict(), headers=self.headers)
        dict_response = response.json()

        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'Username less than 5 characters or more than 15 characters')

    def test_password_min_boundary(self):
        print("Testing password at minimum boundary...")
        valid_password_min = Player(username="user12345", password="pass1234")
        response = requests.post(self.TEST_URL, json=valid_password_min.to_dict(), headers=self.headers)
        dict_response = response.json()

        self.assertTrue(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'OK')

    def test_password_max_boundary(self):
        print("Testing password at maximum boundary...")
        valid_password_max = Player(username="user12345", password="123456789012345")
        response = requests.post(self.TEST_URL, json=valid_password_max.to_dict(), headers=self.headers)
        dict_response = response.json()

        self.assertTrue(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'OK')

    def test_password_below_min_boundary(self):
        print("Testing password below minimum boundary...")
        invalid_password_below_min = Player(username="user12345", password="short1")
        response = requests.post(self.TEST_URL, json=invalid_password_below_min.to_dict(), headers=self.headers)
        dict_response = response.json()

        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'Password less than 8 characters or more than 15 characters')

    def test_password_above_max_boundary(self):
        print("Testing password above maximum boundary...")
        invalid_password_above_max = Player(username="user12345", password="12345678901234567890")
        response = requests.post(self.TEST_URL, json=invalid_password_above_max.to_dict(), headers=self.headers)
        dict_response = response.json()

        self.assertFalse(dict_response['result'])
        self.assertEqual(dict_response['msg'], 'Password less than 8 characters or more than 15 characters')



    def tearDown(self):
        print("Clearing up after test...")
        for doc in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=doc['id'], partition_key=doc['id'])
