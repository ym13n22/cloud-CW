import unittest
import requests
import json
from azure.cosmos import CosmosClient
from shared_code.Prompt import Prompt

class TestPromptDelete(unittest.TestCase):
    LOCAL_DEV_URL_PROMPT_DELETE = "http://localhost:7071/api/prompt/delete"
    PUBLIC_DEV_URL_PROMPT_DELETE = "https://cw111.azurewebsites.net/api/prompt/delete"
    TEST_URL_PROMPT_DELETE = PUBLIC_DEV_URL_PROMPT_DELETE

    # Load Cosmos settings
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
    PromptContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PromptContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    def setUp(self):
        # Clear existing data and add example prompts for testing
        for item in self.PromptContainerProxy.read_all_items():
            self.PromptContainerProxy.delete_item(item=item['id'], partition_key=item['username'])

        # Add sample prompts
        sample_prompts = [
            {"id": "auto-gen-1", "username": "py_luis", "texts": [
                {"text": "The most useless Python one-line program", "language": "en"},
                {"text": "El programa de una línea en Python más inútil", "language": "es"}
            ]},
            {"id": "auto-gen-2", "username": "py_luis", "texts": [
                {"text": "Why the millenial crossed the avenue?", "language": "en"},
                {"text": "¿Por qué el millenial cruzó la avenida?", "language": "es"}
            ]},
            {"id": "auto-gen-3", "username": "js_packer", "texts": [
                {"text": "Why the ka-boomer crossed the road?", "language": "en"},
                {"text": "¿Por qué el ka-boomer cruzó la calle?", "language": "es"}
            ]},
            {"id": "auto-gen-4", "username": "les_cobol", "texts": [
                {"text": "Why the boomer crossed the road?", "language": "en"},
                {"text": "¿Por qué el boomer cruzó la calle?", "language": "es"}
            ]}
        ]
        
        # Insert sample prompts into the PromptContainerProxy
        for prompt in sample_prompts:
            self.PromptContainerProxy.create_item(prompt)

    def test_prompt_delete(self):
        # Test deletion of prompts by player "py_luis"
        delete_request_data = {"player": "py_luis"}
        response = requests.post(self.TEST_URL_PROMPT_DELETE, json=delete_request_data, params={"code": self.FunctionAppKey})
        response_data = response.json()
        
        print("Prompt delete response:", response_data)

        # Check response status and message
        self.assertTrue(response_data['result'])
        self.assertEqual(response_data['msg'], "2 prompts deleted")  # Expecting 2 prompts deleted for "py_luis"
        
        # Verify remaining prompts in the database
        remaining_prompts = list(self.PromptContainerProxy.read_all_items())
        remaining_usernames = [prompt["username"] for prompt in remaining_prompts]
        
        # Ensure only prompts from "js_packer" and "les_cobol" remain
        self.assertNotIn("py_luis", remaining_usernames)
        self.assertIn("js_packer", remaining_usernames)
        self.assertIn("les_cobol", remaining_usernames)

    def tearDown(self):
        # Clean up database items after each test
        for item in self.PromptContainerProxy.read_all_items():
            self.PromptContainerProxy.delete_item(item=item['id'], partition_key=item['username'])
