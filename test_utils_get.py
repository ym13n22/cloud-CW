import unittest
import requests
import json
from azure.cosmos import CosmosClient

class TestUtilsGet(unittest.TestCase):
    LOCAL_DEV_URL_GET = "http://localhost:7071/api/utils/get"
    PUBLIC_DEV_URL_GET = "https://cw111.azurewebsites.net/api/utils/get"
    TEST_URL_GET = PUBLIC_DEV_URL_GET

    # Load Cosmos setting
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    MyCosmos = CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
    PromptContainerProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName']).get_container_client(settings['Values']['PromptContainerName'])
    FunctionAppKey = settings['Values']['FunctionAppKey']

    def setUp(self):
        # Clear previous data and set up test data
        for item in self.PromptContainerProxy.read_all_items():
            self.PromptContainerProxy.delete_item(item=item['id'], partition_key=item['username'])

        # Insert test data
        test_data = [
            {"id": "auto-gen-1", "username": "py_luis", "texts": [
                {"text": "The most useless Python one-line program", "language": "en"},
                {"text": "El programa de una línea en Python más inútil", "language": "es"}
            ]},
            {"id": "auto-gen-2", "username": "py_luis", "texts": [
                {"text": "Why the millenial crossed the avenue?", "language": "en"},
                {"text": "¿Por qué el millenial cruzó la avenida?", "language": "es"}
            ]},
            {"id": "auto-gen-3", "username": "js_packer", "texts": [
                {"text": "Why the boomer crossed the road?", "language": "en"},
                {"text": "¿Por qué el boomer cruzó la calle?", "language": "es"}
            ]},
            {"id": "auto-gen-4", "username": "les_cobol", "texts": [
                {"text": "Why the boomer crossed the road?", "language": "en"},
                {"text": "¿Por qué el boomer cruzó la calle?", "language": "es"}
            ]},
            {"id": "auto-gen-5", "username": "les_cobol", "texts": [
                {"text": "Why the boomer entered the pub?", "language": "en"},
                {"text": "¿Por qué el boomer entró al bar?", "language": "es"}
            ]}
        ]
        for item in test_data:
            self.PromptContainerProxy.create_item(item)

    def test_utils_get_multiple_players(self):
        # Input for UtilsGet
        request_data = {
            "players": ["js_packer", "les_cobol"],
            "language": "en"
        }
        response = requests.get(self.TEST_URL_GET, json=request_data, params={"code": self.FunctionAppKey})
        print("UtilsGet test response:", response.json())

        # Expected output
        expected_output = [
            {"id": "auto-gen-3", "text": "Why the boomer crossed the road?", "username": "js_packer"},
            {"id": "auto-gen-4", "text": "Why the boomer crossed the road?", "username": "les_cobol"},
            {"id": "auto-gen-5", "text": "Why the boomer entered the pub?", "username": "les_cobol"}
        ]

        # Verify response matches expected output
        self.assertEqual(response.json(), expected_output)

    def tearDown(self):
        # Clean up database items after each test
        for item in self.PromptContainerProxy.read_all_items():
            self.PromptContainerProxy.delete_item(item=item['id'], partition_key=item['username'])

