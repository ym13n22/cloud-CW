import unittest
import requests
import json
from azure.cosmos import CosmosClient
from shared_code.Prompt import Prompt
from shared_code.Player import Player
import logging

class TestPromptCreate(unittest.TestCase):
    LOCAL_DEV_URL_REGISTER = "http://localhost:7071/api/player/register"
    LOCAL_DEV_URL_PROMPT = "http://localhost:7071/api/prompt/create"
    PUBLIC_DEV_URL_REGISTER = "https://cw111.azurewebsites.net/api/player/register"
    PUBLIC_DEV_URL_PROMPT = "https://cw111.azurewebsites.net/api/prompt/create"
    TEST_URL_REGISTER = PUBLIC_DEV_URL_REGISTER
    TEST_URL_PROMPT = PUBLIC_DEV_URL_PROMPT

    # Load Cosmos settings
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    PlayerDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PlayerContainerProxy = PlayerDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
    PromptContainerProxy = PlayerDBProxy.get_container_client(settings['Values']['PromptContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    def setUp(self):
        # Ensure a valid player exists and clear previous data
        for item in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['id'])
        print("Registering valid player for testing...")
        response = requests.post(self.TEST_URL_REGISTER, json={
            "username": "validUser",
            "password": "password123"
        }, params={"code": self.FunctionAppKey})
        print("Player registration response:", response.json())

    
    def test_prompt_create_supported_languages(self):

        supported_prompts = [
            {"language": "en", "text": "This is an English prompt."},
            {"language": "ga", "text": "Seo é m'aistriúchán Gaeilge."},
            {"language": "es", "text": "Esta es una pregunta en español."},
            {"language": "hi", "text": "यह एक हिंदी प्रॉम्प्ट है।"},
            {"language": "zh-Hans", "text": "这是一个足够长的简体中文提示符用于通过验证。"},
            {"language": "pl", "text": "To jest polska wiadomość."}
          ]
    
        for prompt in supported_prompts:
            print(f"\nTesting prompt in {prompt['language']}...")
            # Adjusting payload structure to include username and text directly
            prompt_data = {
                "username": "validUser",  # User
                "text": prompt["text"]     # Text for prompt creation
            }
            
            response = requests.post(self.TEST_URL_PROMPT, json=prompt_data, params={"code": self.FunctionAppKey})

            try:
                dict_response = response.json()
            except json.JSONDecodeError:
                print("Prompt creation response is not JSON. Raw response:", response.text)

            print("Prompt creation response:", response.json())
            dict_response = response.json()
            
            
            self.assertTrue(dict_response['result'])
            self.assertEqual(dict_response['msg'], 'OK')

            # Verify prompt exists in CosmosDB
            query_result = self.PromptContainerProxy.query_items(
                query="SELECT * FROM c WHERE c.username = @username",
                parameters=[{"name": "@username", "value": "validUser"}],
                enable_cross_partition_query=True
            )
            query_result_list = list(query_result)
            print("Query result from CosmosDB:", query_result_list)
            self.assertGreaterEqual(len(query_result_list), 1)


    def test_prompt_create_unsupported_language(self):
        unsupported_prompt = {
            "username": "validUser",
            "text": "Ceci est un message en français."
        }
        response = requests.post(self.TEST_URL_PROMPT, json=unsupported_prompt, params={"code": self.FunctionAppKey})
        print("Unsupported language test response:", response.json())
        self.assertEqual(response.json(), {"result": False, "msg": "Unsupported language"})


    def test_prompt_create_numbers(self):
            # Unsupported language prompt due to numbers-only content
            number_prompt = {
                "username": "validUser",
                "text": "123456789123456789000000000"  # Adding `text` directly
            }
            
            logging.info("Sending numbers-only prompt for unsupported language test.")
            
            # Send request to the PromptCreate endpoint
            response = requests.post(self.TEST_URL_PROMPT, json=number_prompt, params={"code": self.FunctionAppKey})
            
            # Log the response received from the server
            logging.info("Received response for numbers-only prompt: %s", response.json())

            print("Number-based prompt test response:", response.json())
            

            # Log the expected vs actual response content
            logging.debug("Expected response: {'result': False, 'msg': 'Unsupported language'}, Actual response: %s", response.json())
            
            # Check if the response content matches expected JSON
            self.assertEqual(response.json(), {"result": False, "msg": "Unsupported language"})

    
    def test_prompt_create_garbled(self):
        garbled_prompt = {
            "username": "validUser",
            "text": "γ̴̟̚o̴̙͛ɿ̶͇͋ ̴͈̾ƨ̷̢͠ɒ̷͓̋b̵̀ͅ ̷̰́*̶̬̔*̶͖́ ̴̈͜ɔ̴̗̐ɒ̴̢͐i̴̹͊n̵̗̚ɘ̵̖̒"
        }
        response = requests.post(self.TEST_URL_PROMPT, json=garbled_prompt, params={"code": self.FunctionAppKey})
        print("Garbled prompt test response:", response.json())
        self.assertEqual(response.json(), {"result": False, "msg": "Unsupported language"})


    def test_prompt_create_short_text(self):
        # Text too short
        short_text_prompt = {
            "username": "validUser", 
            "text": "Hi"
            }
        response = requests.post(self.TEST_URL_PROMPT, json=short_text_prompt, params={"code": self.FunctionAppKey})
        print("Short text test response:", response.json())
        self.assertEqual(response.json(), {"result": False, "msg": "Prompt less than 20 characters or more than 100 characters"})


    def test_prompt_create_long_text(self):
        # Text over 100 characters
        long_text_prompt = {
            "username": "validUser", 
            "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi"
            }
        response = requests.post(self.TEST_URL_PROMPT, json=long_text_prompt, params={"code": self.FunctionAppKey})
        print("Long text test response:", response.json())
        self.assertEqual(response.json(), {"result": False, "msg": "Prompt less than 20 characters or more than 100 characters"})


    def test_prompt_create_nonexist_player(self):
        long_text_prompt = {
            "username": "invalidUser",
            "text": "Player does not exist, Player does not exist"
        }
        response = requests.post(self.TEST_URL_PROMPT, json=long_text_prompt, params={"code": self.FunctionAppKey})
        print("Player does not exist test response:", response.json())
        self.assertEqual(response.json(), {"result": False, "msg": "Player does not exist"})

    def tearDown(self):
        # Clean up database items after each test
        print("Cleaning up database items after test...")
        for item in self.PlayerContainerProxy.read_all_items():
            self.PlayerContainerProxy.delete_item(item=item['id'], partition_key=item['id'])
        for item in self.PromptContainerProxy.read_all_items():
            self.PromptContainerProxy.delete_item(item=item['id'], partition_key=item['username'])
