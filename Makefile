test-trigger:
	@echo Testing HTTP Trigger...
	curl -X GET "https://cw111.azurewebsites.net/api/http_trigger?name=myj"

# 目标：注册玩家
register-player:
	@echo Registering Player...
	curl -X POST "https://cw111.azurewebsites.net/api/player/register" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"username\": \"username\", \"password\": \"123456789\"}"

register-player1:
	curl -X POST "https://cw111.azurewebsites.net/api/player/register" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"username\": \"username1\", \"password\": \"123456789\"}"

register-player2:
	curl -X POST "https://cw111.azurewebsites.net/api/player/register" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"username\": \"A-player\", \"password\": \"123456789\"}"
####### login test
login-seccess:
	@echo login seccess...
	curl -X GET "https://cw111.azurewebsites.net/api/player/login"  -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"username\": \"username\", \"password\": \"123456789\"}"
# 预期输出: {"result": true, "msg": "OK"}
#这个wrong pwd得改
login-fail:
	curl -X GET "https://cw111.azurewebsites.net/api/player/login" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"username\": \"username\", \"password\": \"12345678\"}"
# 预期输出: {"result": false, "msg": "Username or password incorrect"}

#用户不存在
login-fail1:
	curl -X GET "https://cw111.azurewebsites.net/api/player/login" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ=="  -d "{\"username\": \"nonexistent_user\", \"password\": \"any_password\"}"
# 预期输出: {"result": false, "msg": "Username or password incorrect"}

####### update test
#这里后面加一个测试打出更新后的分数
update-seccess:
	curl -X PUT "https://cw111.azurewebsites.net/api/player/update"   -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ=="  -d "{\"username\": \"username\", \"add_to_games_played\": 2, \"add_to_score\": 50}"
# 预期输出: {"result": true, "msg": "OK"}

update-fail:
	curl -X PUT "https://cw111.azurewebsites.net/api/player/update"     -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ=="    -d "{\"username\": \"nonexistent_user\", \"add_to_games_played\": 1, \"add_to_score\": 10}"

### Interval and boundary tests得改
update-boundary:
	curl -X PUT "https://cw111.azurewebsites.net/api/player/update" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"username\": \"username\", \"add_to_games_played\": 0, \"add_to_score\": 0}"
# 预期输出: {"result": true, "msg": "OK"}

update-boundary1:
	curl -X PUT "https://cw111.azurewebsites.net/api/player/update" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"username\": \"username\", \"add_to_games_played\": -1, \"add_to_score\": -10}"
# 预期输出: {"result": true, "msg": "OK"}

update-boundary2:
	curl -X PUT "https://cw111.azurewebsites.net/api/player/update" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ=="  -d "{\"username\": \"username\", \"add_to_games_played\": 2147483647, \"add_to_score\": 2147483647}"
# 预期输出: {"result": true, "msg": "OK"}



###### test prompt create
prompt-seccess:
	curl -X POST "https://cw111.azurewebsites.net/api/prompt/create" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"text\": \"This is a test prompt to check translation functionality.\",\"username\": \"username\"}"

prompt-seccess2:
	curl -X POST "https://cw111.azurewebsites.net/api/prompt/create" -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"text\": \"translate prompt is here.\",\"username\": \"username1\"}"


###### test prompt suggest
suggest:
	curl -X POST  https://cw111.azurewebsites.net/api/prompt/suggest -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"keyword\": \"adventure\"}"

###### test prompt delete
prompt-delete:
	curl -X POST  https://cw111.azurewebsites.net/api/prompt/delete -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"player\": \"username\"}"

###### test prompt get
prompt-get:
	curl -X GET  https://cw111.azurewebsites.net/api/utils/get -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"players\": [\"username\", \"les_cobol\"], \"language\": \"en\"}"

prompt-getB:
	curl -X GET  https://cw111.azurewebsites.net/api/utils/get -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ==" -d "{\"players\": [\"username\", \"username1\"], \"language\": \"en\"}"

###### test podium
podium:
	curl -X GET  https://cw111.azurewebsites.net/api/utils/podium -H "Content-Type: application/json" -H "x-functions-key: jLncRoiYHvcqdgXVSKmMGKSpSpPSDRxgLS-WI5jJASR4AzFujfBAdQ=="





