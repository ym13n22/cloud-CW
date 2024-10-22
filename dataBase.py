from azure.cosmos import CosmosClient, exceptions
import json
import openai
import logging
import os

# Cosmos DB 配置
endpoint = "<your-cosmos-db-uri>"  # 替换为您的 Cosmos DB URI
key = "<your-cosmos-db-key>"        # 替换为您的 Cosmos DB 密钥

openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")  # 设置API的base URL
openai.api_type = 'azure'
openai.api_version = '2023-05-15'  # 使用最新版本的 API

player_container=None
prompt_container=None


# 创建 CosmosClient 实例
cosmos_client = CosmosClient(endpoint, key)

def create_dataSet():
    try:
        # 创建数据库
        database_name = 'quiplash'
        database = cosmos_client.create_database_if_not_exists(id=database_name)
        logging.info(f'Database "{database_name}" created or already exists.')
        print(f'Database "{database_name}" created or already exists.')

        # 创建 player 容器
        player_container_name = 'player'
        player_container = database.create_container_if_not_exists(
            id=player_container_name,
            partition_key='/id',
            offer_throughput=400
        )
        print(f'Container "{player_container_name}" created or already exists.')

        # 创建 prompt 容器
        prompt_container_name = 'prompt'
        prompt_container = database.create_container_if_not_exists(
            id=prompt_container_name,
            partition_key='/username',
            offer_throughput=400
        )
        print(f'Container "{prompt_container_name}" created or already exists.')

    except exceptions.CosmosHttpResponseError as e:
        print(f'An error occurred: {e.message}')
    finally:
        # 释放资源
        cosmos_client = None  # 这里将无法释放已创建的客户端，通常建议在主程序结束时释放资源

def register_player(input_json):
    # 解析输入 JSON
    input_data = json.loads(input_json)
    username = input_data.get("username")
    password = input_data.get("password")

    # 验证用户名和密码
    if not (5 <= len(username) <= 15):
        return json.dumps({"result": False, "msg": "Username less than 5 characters or more than 15 characters"})
    
    if not (8 <= len(password) <= 15):
        return json.dumps({"result": False, "msg": "Password less than 8 characters or more than 15 characters"})

    # 检查用户名是否已存在
    try:
        existing_player = player_container.read_item(item=username, partition_key=username)
        return json.dumps({"result": False, "msg": "Username already exists"})
    except exceptions.CosmosResourceNotFoundError:
        # 用户名不存在，可以注册新用户
        new_player = {
            "id": username,
            "username": username,
            "password": password,
            "games_played": 0,
            "total_score": 0
        }
        player_container.create_item(body=new_player)
        return json.dumps({"result": True, "msg": "OK"})

def log_in(input_json):
    input_data = json.loads(input_json)
    username = input_data.get("username")
    password = input_data.get("password")

    try:
        exiting_player=player_container.read_item(item=username, partition_key=username)
        stored_password = exiting_player.get("password")
        if password == stored_password:
            return json.dumps({"result": True,"msg": "OK"})
        else:
            return json.dumps({"result": False,"msg": "Username or password incorrect"})
    except exceptions.CosmosResourceNotFoundError:
        return json.dumps({"result": False,"msg": "Username or password incorrect"})
    
def update(input_json):
    input_data = json.loads(input_json)
    username= input_data.get("username")
    add_to_games_played=input_data.get("add_to_games_played")
    add_to_score=input_data.get("add_to_score")
    if not isinstance(add_to_games_played, int) or not isinstance(add_to_score, int):
        return json.dumps({"result": False, "msg": "Invalid input data. 'add_to_games_played' and 'add_to_score' should be integers."})
    try:
        exiting_player=player_container.read_item(item=username,partition_key=username)
        games_played=exiting_player.get("games_played",0)
        total_score=exiting_player.get("total_score",0)

        exiting_player["games_played"]=games_played+add_to_games_played
        exiting_player["total_score"]=total_score+add_to_score

        if exiting_player["games_played"] < 0 or exiting_player["total_score"] < 0:
            return json.dumps({"result": False, "msg": "Invalid update. Values cannot be negative."})
        
        player_container.replace_item(item=exiting_player,body=exiting_player)
        
        return json.dumps({"result":True,"msg":"OK"})
    except exceptions.CososResourcsNotFoundError:
        return json.dumps({"result": False,"msg":"Player does not exit"})
    
def suggest(input_json):
    input_data=json.loads(input_json)
    keyword=input_data.get("keyword")
    
    if not keyword or not isinstance(keyword,str):
        return json.dumps({"result": False,"msg":"Invalid input. 'keyword' must be a string"})
    
    try:
        response=openai.ChatCompletion.create(
            engine="gpt-35-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that suggests prompts."},
                {"role": "user", "content": f"Generate a useful prompt suggestion that includes the keyword '{keyword}'."}
            ],
            max_tokens=100,
            temperature=0.7
        )
        suggestion = response['choices'][0]['message']['content'].strip()

        # 确保关键字至少出现一次
        if keyword not in suggestion:
            return json.dumps({"result": False, "msg": "The suggestion does not include the keyword."})

        # 返回包含关键词的建议提示
        return json.dumps({"suggestion": suggestion})
            
        
    except openai.error.OpenAIError as e:
        return json.dumps({"result":False,"msg":f"Fail to generate prompt.Error:{str(e)}"})
    
def delete(input_json):
    input_data=json.loads(input_json)
    username=input_data.get("username")
    try:
        exiting_promp=prompt_container.read_item(item=username,pertition_key=username)
        query=f"SELECT * FROM c WHERE c.username='{username}'"
        items=list(prompt_container.query_items(query=query,enable_cross_partition_query=True))
        #if not items:
            #return json.dumps({"result": True,"msg":"0 prompts deleted"})
        
        deleted_count=0
        for item in items:
            prompt_container.delete_item(item=item['id'],partition_key=item['username'])
            deleted_count +=1

        return json.dumps({"result":True,"msg":f"{deleted_count} prompts deleted"})
        
    except exceptions.CCosmosResourceNotFoundError:
        return json.dumps({"result": True,"msg":"0 prompts deleted"})
    
def get_prompts(input_json):
    input_data=json.loads(input_json)
    players=input_data.get("players")
    language=input_data.get("language")

    prompts = []
    for player in players:
        query = f"SELECT * FROM c WHERE c.username = '{player}'"
        items = list(prompt_container.query_items(query=query, enable_cross_partition_query=True))
    
        for item in items:
                for text in item.get("texts", []):
                    # 只返回匹配指定语言的文本
                    if text["language"] == language:
                        prompts.append({
                            "id": item["id"],
                            "text": text["text"],
                            "username": item["username"]
                        })

        
    return json.dumps(prompts)

def get_podium():
    try:
        
        query = "SELECT c.username, c.games_played, c.total_score FROM c"
        players = list(prompt_container.query_items(query=query, enable_cross_partition_query=True))
        
        
        valid_players = [
            {"username": p["username"], "games_played": p["games_played"], "total_score": p["total_score"], 
             "ppgr": p["total_score"] / p["games_played"]} 
            for p in players if p["games_played"] > 0
        ]

        
        valid_players.sort(key=lambda x: (-x["ppgr"], x["games_played"], x["username"]))

        
        podium = {"gold": [], "silver": [], "bronze": []}
        if not valid_players:
            return json.dumps(podium)

        
        podium_ranks = []
        for player in valid_players:
            if len(podium_ranks) < 3:
                if not podium_ranks or player["ppgr"] != podium_ranks[-1]:
                    podium_ranks.append(player["ppgr"])

        
        for player in valid_players:
            if player["ppgr"] == podium_ranks[0]:
                podium["gold"].append({"username": player["username"], "games_played": player["games_played"], "total_score": player["total_score"]})
            elif len(podium_ranks) > 1 and player["ppgr"] == podium_ranks[1]:
                podium["silver"].append({"username": player["username"], "games_played": player["games_played"], "total_score": player["total_score"]})
            elif len(podium_ranks) > 2 and player["ppgr"] == podium_ranks[2]:
                podium["bronze"].append({"username": player["username"], "games_played": player["games_played"], "total_score": player["total_score"]})

        return json.dumps(podium)
    
    except exceptions.CosmosHttpResponseError as e:
        return json.dumps({"result": False, "msg": f"An error occurred: {str(e)}"})