import azure.functions as func
from azure.cosmos import CosmosClient, exceptions
from azure.functions import HttpRequest, HttpResponse
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
import openai
import requests, uuid, json
import logging
import os
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
import openai
import uuid

# CosmosDB setup
cosmos_connection_string = os.getenv("AzureCosmosDBConnectionString")
database_name = os.getenv("DatabaseName")
player_container_name = os.getenv("PlayerContainerName")
prompt_container_name = os.getenv("PromptContainerName")

# Translation service setup
translation_endpoint = os.getenv("TranslationEndpoint")
logging.info(f"translation_endpoint_initial: {translation_endpoint}")
translation_key = os.getenv("TranslationKey")
translation_region = os.getenv("TranslationRegion")

#prompt translate
#deployment_url="https://api.cognitive.microsofttranslator.com/"
#deployment_url = os.getenv("TranslationEndpoint")
prompt_translate_endpoint=os.getenv("Prompt_translate_endpoint")
prompt_translate_key=os.getenv("Prompt_tranalate_key")


# Azure OpenAI setup
oai_endpoint = os.getenv("OAIEndpoint")
oai_key = os.getenv("OAIKey")
oai_vision=os.getenv("OAIVision")

# Deployment settings

function_app_key = os.getenv("FunctionAppKey")


MyCosmos=CosmosClient.from_connection_string(cosmos_connection_string)
QuiplashDBProxy = MyCosmos.get_database_client(database_name)
PlayerContainerProxy = QuiplashDBProxy.get_container_client(player_container_name)
promptContainerProxy = QuiplashDBProxy.get_container_client(prompt_container_name)


client_AI = AzureOpenAI(
    api_key=oai_key,  
    api_version=oai_vision,
    azure_endpoint=oai_endpoint
)

params = {
    'api-version': '3.0'
}


headers = {
    'Ocp-Apim-Subscription-Key': prompt_translate_key,
    # location required if you're using a multi-service or regional (not global) resource.
    'Ocp-Apim-Subscription-Region': translation_region,
    'Content-type': 'application/json',
    'X-ClientTraceId': str(uuid.uuid4())
}


SUPPORTED_LANGUAGES = ["en", "ga", "es", "hi", "zh-Hans", "pl"]  # English, Irish, Spanish, Hindi, Simplified Chinese, Polish


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger", auth_level=func.AuthLevel.FUNCTION)
def http_trigger(req: HttpRequest) -> HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )


@app.route(route="player/register",methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def register(req: HttpRequest) -> HttpResponse:
    try:
        data=req.get_json()
        username = data.get("username")
        password = data.get("password")
        
        if len(username) < 5 or len(username) > 15:
            return HttpResponse(
                body='{"result": false, "msg": "Username less than 5 characters or more than 15 characters"}',
                status_code=400,
                mimetype="application/json"
            )
        if len(password) < 8 or len(password) > 15:
            return HttpResponse(
                body='{"result": false, "msg": "Password less than 8 characters or more than 15 characters"}',
                status_code=400,
                mimetype="application/json"
            )
            
        query = "SELECT * FROM player p WHERE p.username = @username"
        items = list(PlayerContainerProxy.query_items(
            query=query,
            parameters=[{"name": "@username", "value": username}],
            enable_cross_partition_query=True
        ))

        if items:    
            return HttpResponse(
                body='{"result": false, "msg": "Username already exists"}',
                status_code=409,
                mimetype="application/json"
            )
            
        new_player = {
            "id": username,  
            "username": username,
            "password": password,  
            "games_played": 0,
            "total_score": 0
        }
        PlayerContainerProxy.create_item(body=new_player)
        
        return HttpResponse(
            body='{"result": true, "msg": "OK"}',
            status_code=201,
            mimetype="application/json"
        )
        
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Cosmos DB Error: {str(e)}")
        return HttpResponse(
            body='{"result": false, "msg": "Database error"}',
            status_code=500,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"General Error: {str(e)}")
        return HttpResponse(
            body='{"result": false, "msg": "Internal server error"}',
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="player/login", methods=["GET"],auth_level=func.AuthLevel.FUNCTION)
def login(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data=req.get_json()
        username = data.get("username")
        password = data.get("password")
        
        query = "SELECT * FROM player p WHERE p.username = @username"
        items = list(PlayerContainerProxy.query_items(
            query=query,
            parameters=[{"name": "@username", "value": username}],
            enable_cross_partition_query=True
        ))
        
        if not items:
            return HttpResponse(
                body='{"result": false,"msg": "Username or password incorrect"}',
                status_code=200,
                mimetype="application/json"
            )
        
        player=items[0]
        if player.get("password") == password:
            return HttpResponse(
                body='{"result": true,"msg": "OK"}',
                status_code=200,
                mimetype="application/json"
            )
        else:
            return HttpResponse(
                body='{"result": false,"msg": "Username or password incorrect"}',
                status_code=200,
                mimetype ="application/json"                
            )
        
    except Exception as e:
        return HttpResponse(
            body='{"result": false,"msg": "Invalid JSON input"}',
            status_code=400,
            mimetype="application/json"
        )

@app.route(route="player/update",methods=["PUT"], auth_level=func.AuthLevel.FUNCTION)
def update(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data=req.get_json()
        username=data.get("username")
        #这里有说如果没有得到值就是0吗？
        add_to_games_played=data.get("add_to_games_played",0)
        add_to_score=data.get("add_to_score",0)
        
        #Interval and boundary tests？？？？只能有整值？！！！！
        query="SELECT * FROM player p WHERE p.username=@username"
        items=list(PlayerContainerProxy.query_items(
            query=query,
            parameters=[{"name": "@username", "value":username}],
            enable_cross_partition_query=True
        ))
        
        if not items:
            return HttpResponse(
                body='{"result": false,"msg": "Player does not exist"}',
                status_code=200,
                mimetype="application/json"
            )
        
        player=items[0]
        player_id=player["id"]
        player_pwd=player.get("password")
        
        new_games_played=player.get("games_played",0)+add_to_games_played
        new_total_score=player.get("total_score",0)+add_to_score
        updated_player_data={
            "id":player_id,
            "username": username,
            "games_played": new_games_played,
            "total_score": new_total_score,
            "password":player_pwd
        }
        
        try:
            PlayerContainerProxy.replace_item(item=player_id,body=updated_player_data)
            return HttpResponse(
                body='{"result": true, "msg": "OK"}',
                status_code=200,
                mimetype="application/json"
            )
        except exceptions.CosmosHttpResponseError as e:
            return HttpResponse(
                body='"result": false, "msg": "Error updating player"',
                status_code=500,
                mimetype="application/json"
            )
        
    except Exception as e:
        return HttpResponse(
            body='{"result": false,"msg": "Invalid JSON input"}',
            status_code=400,
            mimetype="application/json"
        )

@app.route(route="prompt/create",methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def create_prompt(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data=req.get_json()
        logging.info("test1")
        text=data.get("text")
        username=data.get("username")
        
        translation_endpoint = os.getenv("TranslationEndpoint")
        logging.info(f"translation_endpoint_initial: {translation_endpoint}")
        translation_key = os.getenv("TranslationKey")
        translation_region = os.getenv("TranslationRegion")
        
        if len(text)<20 or len(text)>100:
            return HttpResponse(
                body='{"result": false, "msg": "Prompt less than 20 characters or more than 100 characters"}',
                status_code=400,
                mimetype="application/json"
            )
        
        query="SELECT * FROM player p WHERE p.username=@username"
        items=list(PlayerContainerProxy.query_items(
            query=query,
            parameters=[{"name": "@username", "value":username}],
            enable_cross_partition_query=True
        ))
        
        if not items:
            return HttpResponse(
                body='{"result":false, "msg":"Player does not exist"}',
                status_code=404,
                mimetype="application/json"
            )
            
        logging.info("test2")
        construct_path = '/detect'
        logging.info(f"translation_endpoint: {translation_endpoint}")
        constructed_url = translation_endpoint + construct_path
        logging.info(f"constructed_url: {constructed_url}")
        
        detect_body = [{"text": text}]
        detect_response = requests.post(constructed_url, params=params, headers=headers, json=detect_body)
        detect_result = detect_response.json()

        logging.info(json.dumps(detect_result, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))
        language_code = detect_result[0].get("language")
        confidence_score = detect_result[0].get("score")
        
        logging.info(f"language_code: {language_code}")
        logging.info(f"confidence_code: {confidence_score}")
    
    
        
        if language_code not in SUPPORTED_LANGUAGES or confidence_score<0.2:
            return HttpResponse(
                body='{"result": false, "msg": "Unsupported language"}',
                status_code=400,
                mimetype="application/json"
            )
            
        translate_path = '/translate'
        translate_url = translation_endpoint + translate_path

       
                 
        params_translate = {
                 'api-version': '3.0',
                 'from': language_code,
                 'to': SUPPORTED_LANGUAGES
                }    
        
        request_translate = requests.post(translate_url, params=params_translate, headers=headers, json=detect_body)
        response_translate = request_translate.json()    
        
        translations=[]
        logging.info("next translate")
        logging.info(json.dumps(response_translate, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))
        
        for translation in response_translate[0].get('translations', []):
            translated_text = translation['text']
            target_language = translation['to']
            translations.append({
                "language": target_language,
                "text": translated_text
            })
        
        
        
        #used for debug        
        logging.info(f"texts:{translations}")
           
        new_prompt={
            "id":str(uuid.uuid4()),
            "username":username,
            "texts":translations
        }
        promptContainerProxy.create_item(body=new_prompt)
        return HttpResponse(
            body='{"result": true, "msg": "OK"}',
            status_code=201,
            mimetype="application/json"
        )
    
    except Exception as e:
        return HttpResponse(
            body=f'{{"result": false, "msg": "Invalid JSON input: {str(e)}"}}',
            status_code=400,
            mimetype="application/json"
        )

@app.route(route="prompt/suggest",methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def suggest(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data=req.get_json()
        keyword=data.get("keyword")
        
        if not keyword:
            return HttpResponse(
                body='{"suggestion": "Cannot generate suggestion"}',
                status_code=400,
                mimetype="application/json"
            )
            
        logging.info("test1")
        response = client_AI.chat.completions.create(
            model="gpt-35-turbo", 
            messages=[
                {"role": "user", "content": f"Generate a creative prompt that includes the keyword '{keyword}' and is around 50 characters long."}
            ],
            
            max_tokens=25,
            temperature=0.7
        )
        logging.info("test2")
        suggestion = response.choices[0].message.content.strip()
        output_json=json.dumps(suggestion,ensure_ascii=False)
        if keyword.lower() in suggestion.lower():
            response_data = {
            "suggestion": suggestion
            }
            return HttpResponse(
                body=json.dumps(response_data, ensure_ascii=False),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return HttpResponse(
                body='{"suggestion": "Cannot generate suggestion"}',
                status_code=400,
                mimetype="application/json"
            )
    except Exception as e:
        return HttpResponse(
            body=f'{{"result": false, "msg": "Invalid JSON input: {str(e)}"}}',
            status_code=400,
            mimetype="application/json"
        )
        
@app.route(route="prompt/delete",methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def delete_prompt(req:HttpRequest)->HttpResponse:
    try:
        data=req.get_json()
        player=data.get("player")
        
        prompt_num=0
        
        query="SELECT * FROM prompt p WHERE p.username = @username"
        items=list(promptContainerProxy.query_items(
            query=query,
            parameters=[{"name": "@username", "value": player}],
            enable_cross_partition_query=True
        ))
        
        for item in items:
            promptContainerProxy.delete_item(item=item['id'], partition_key=item['username'])
            prompt_num += 1
            
        return HttpResponse(
            body=f'{{"result": true, "msg": "{prompt_num} prompts deleted"}}',
            status_code=200,
            mimetype="application/json"
        )
        

    except Exception as e:
        return HttpResponse(
            body=f'{{"result": false, "msg": "Invalid JSON input: {str(e)}"}}',
            status_code=400,
            mimetype="application/json"
        )
        
        
@app.route(route="utils/get",methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_prompts(req:HttpRequest)->HttpResponse:
    try:
        data=req.get_json()
        players=data.get("players",[])
        language=data.get("language")
        
        logging.info(f"players:{players}")
        logging.info(f"language:{language}")
        
        if not players or not language:
            return HttpResponse(
                body='{"result": false, "msg": "Invalid input players list or language is missing"}',
                status_code=400,
                mimetype="application/json"
            )
            
        prompts=[]
        
        for player in players:
            query="SELECT * FROM prompt p WHERE p.username = @username"
            items=list(promptContainerProxy.query_items(
            query=query,
            parameters=[{"name": "@username", "value": player}],
            enable_cross_partition_query=True
            ))
            if not items==[]:
             prompts.append(items)  
            
          
        logging.info(f"prompts{str(prompts)}")
        
        output=[]   
        for prompt_group in prompts:
            for single_prompt in prompt_group:
                logging.info(f"prompt: {str(single_prompt)}")
                id = single_prompt["id"]
                username = single_prompt["username"]
                texts = single_prompt["texts"]

                for text in texts:
                    if text["language"] == language:
                        output.append({
                        "id": id,
                        "text": text["text"],
                        "username": username
                    })
                        
        output_json = json.dumps(output, ensure_ascii=False)
                    
        return HttpResponse(
            body=output_json,
            status_code=200,
            mimetype="application/json"
        )
            
            
        
    except Exception as e:
        return HttpResponse(
            body=f'{{"result": false, "msg": "Invalid JSON input: {str(e)}"}}',
            status_code=400,
            mimetype="application/json"
        )  
        

@app.route(route="utils/podium", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_podium(req: HttpRequest) -> HttpResponse:
    try:
        # Query to get all players
        query = "SELECT * FROM player"
        items = list(PlayerContainerProxy.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        players_with_ppgr = []
        logging.info("Processing players for ppgr calculation")

        for item in items:
            # Retrieve player data with defaults to handle missing fields
            username = item.get("username", "Unknown")
            games_played = item.get("games_played", 0)
            total_score = item.get("total_score", 0)

            # Calculate ppgr safely with a fallback for zero games
            ppgr = total_score / games_played if games_played > 0 else 0
            logging.info(f"Player: {username}, Games: {games_played}, Score: {total_score}, PPGR: {ppgr}")

            # Append player info with ppgr to list
            players_with_ppgr.append({
                "username": username,
                "games_played": games_played,
                "total_score": total_score,
                "ppgr": ppgr
            })

        # Sort players by ppgr descending, games_played ascending, and username alphabetically
        players_with_ppgr.sort(key=lambda x: (-x["ppgr"], x["games_played"], x["username"]))

        # Initialize the podium dictionary for the top 3 ranks
        podium = {"gold": [], "silver": [], "bronze": []}
        rank_categories = ["gold", "silver", "bronze"]
        current_rank = 0

        # Fill the podium by iterating through sorted players
        for player in players_with_ppgr:
            if current_rank >= 3:
                break

            # Log current player and rank details
            logging.info(f"Evaluating player for podium: {player['username']} with PPGR: {player['ppgr']} at rank {rank_categories[current_rank]}")

            # Place player into the current rank if rank is empty or ppgr matches
            if len(podium[rank_categories[current_rank]]) == 0 or player["ppgr"] == (podium[rank_categories[current_rank]][0]["total_score"]/podium[rank_categories[current_rank]][0]["games_played"] if podium[rank_categories[current_rank]][0]["games_played"] > 0 else 0):
                podium[rank_categories[current_rank]].append({
                    "username": player["username"],
                    "games_played": player["games_played"],
                    "total_score": player["total_score"]
                })
            else:
                # Move to the next rank if ppgr does not match
                current_rank += 1
                if current_rank < 3:
                    podium[rank_categories[current_rank]].append({
                        "username": player["username"],
                        "games_played": player["games_played"],
                        "total_score": player["total_score"]
                    })

        logging.info(f"Final podium results: {podium}")

        return HttpResponse(
            body=json.dumps(podium),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Exception in get_podium: {str(e)}")
        return HttpResponse(
            body=json.dumps({"result": False, "msg": f"Invalid input: {str(e)}"}),
            status_code=400,
            mimetype="application/json"
        )
        