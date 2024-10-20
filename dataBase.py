from azure.cosmos import CosmosClient, exceptions
import json
import logging

# Cosmos DB 配置
endpoint = "<your-cosmos-db-uri>"  # 替换为您的 Cosmos DB URI
key = "<your-cosmos-db-key>"        # 替换为您的 Cosmos DB 密钥

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
        return json.dumps({"result": True,"msg": "OK"})
    except exceptions.CosmosResourceNotFoundError:
        return json.dumps({"result": False,"msg": "Username or password incorrect"})