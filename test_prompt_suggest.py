import unittest
import requests
import json
import logging
import openai


class TestPromptSuggest(unittest.TestCase):
    LOCAL_TEST_SUGGEST="http://localhost:7071/api/prompt/suggest"
    PUBLIC_TEST_SUGGEST = "https://cw111.azurewebsites.net/api/prompt/suggest"

    TEST_URL = PUBLIC_TEST_SUGGEST
    
    # Load settings for Function App Key
    with open('local.settings.json') as settings_file:
        settings = json.load(settings_file)
    FunctionAppKey = settings['Values']['FunctionAppKey']
    
    def test_prompt_suggest_valid_keyword(self):
        """Test with a typical keyword to ensure the LLM response includes the keyword within 20-100 characters."""
        response = requests.post(
            self.TEST_URL,
            json={"keyword": "adventure"},
            params={"code": self.FunctionAppKey},
            headers={"Content-Type": "application/json"}
        )
        print("Response for valid keyword:", response.json())
        
        suggestion = response.json().get("suggestion", "")
        self.assertIn("adventure", suggestion.lower())
        self.assertTrue(20 <= len(suggestion) <= 100)

    def test_prompt_suggest_short_keyword(self):
        """Test with a very short keyword to confirm it handles minimum keyword length."""
        response = requests.post(
            self.TEST_URL,
            json={"keyword": "a"},
            params={"code": self.FunctionAppKey},
            headers={"Content-Type": "application/json"}
        )
        print("Response for short keyword:", response.json())
        
        suggestion = response.json().get("suggestion", "")
        self.assertIn("a", suggestion.lower())
        self.assertTrue(20 <= len(suggestion) <= 100)

   
    '''
 def test_prompt_suggest_missing_keyword(self):
        """Test for missing 'keyword' to check if it handles input validation properly."""
        response = requests.post(
            self.TEST_URL,
            json={},
            params={"code": self.FunctionAppKey},
            headers={"Content-Type": "application/json"}
        )
        print("Response for missing keyword:", response.json())
        
        self.assertEqual(response.json()["msg"], "Invalid or missing 'keyword' field")

'''

    def test_prompt_suggest_non_inclusive_keyword(self):
        """Test retry logic with a challenging keyword unlikely to appear in LLM responses."""
        response = requests.post(
            self.TEST_URL,
            json={"keyword": "challenging_keyword"},
            params={"code": self.FunctionAppKey},
            headers={"Content-Type": "application/json"}
        )
        print("Response for challenging keyword:", response.json())
        
        suggestion = response.json().get("suggestion", "")
        # Ensure fallback message is used or keyword is included
        self.assertTrue("Cannot generate suggestion" in suggestion or "challenging_keyword" in suggestion.lower())
'''
def test_prompt_suggest_number_content_type(self):
        """Test with incorrect content type header."""
        response = requests.post(
            self.TEST_URL,
            json={"keyword": 123},
            params={"code": self.FunctionAppKey},
            headers={"Content-Type": "application/json"}
        )
        print("Response for number content type:", response.json())
        
        self.assertEqual(response.json()["msg"], "Invalid or missing 'keyword' field")

'''
    
if __name__ == "__main__":
    unittest.main()
