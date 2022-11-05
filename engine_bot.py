# This file contains almost everything of Engine-bot except the web server and QQ-specific content
import base64
from binascii import Error as BinAsciiError

from qq_adapter import *
import aiohttp
import subprocess

styles = ['超马1', '超马3', '超马世界', '新超马U']


async def command_help(data):
    retval = '📑 可用的命令 (输入命令以查看用法):\n' \
             'e!help : 查看此帮助。\n' \
             'e!register : 注册帐号或修改密码。\n' \
             'e!query : 查询关卡信息。\n' \
             'e!report : 举报关卡。\n' \
             'e!stats : 查看上传记录。\n' \
             'e!random : 来个随机关卡。\n' \
             'e!server : 查看服务器状态。'
    if data['sender']['user_id'] in BOT_ADMIN:
        retval += '📑 可用的管理命令:\n' \
                  'e!permission : 更新用户权限。\n' \
                  'e!execute : 运行命令。\n' \
                  'e!sql : 执行 SQL 语句。'
    if data['sender']['user_id'] in GAME_ADMIN:
        retval += '📑 可用的游戏管理命令:\n' \
                  'e!ban : 封禁用户。\n' \
                  'e!unban : 解封用户。'
    await send_group_msg(group_id=data['group_id'], message=retval)
    return


async def command_register(data):
    if not data['parameters']:
        await send_group_msg(data['group_id'], '🔗 打开 https://web.enginetribe.gq/register.html 以注册。\n'
                                               '打开 https://web.enginetribe.gq/change_password.html 以修改密码。')
        return
    else:
        try:
            raw_register_code = data['parameters'].split(' ')[0]
            try:  # auto add equal sign
                register_code = base64.b64decode(raw_register_code.encode()).decode().split("\n")
            except BinAsciiError:
                try:
                    register_code = base64.b64decode((raw_register_code + '=').encode()).decode().split("\n")
                except BinAsciiError:
                    register_code = base64.b64decode((raw_register_code + '==').encode()).decode().split("\n")
            operation = register_code[0]
            username = register_code[1]
            password_hash = register_code[2]
            if operation == 'r':  # register
                async with aiohttp.request(method='POST',
                                           url=ENGINE_TRIBE_HOST + '/user/register',
                                           json={'username': username, 'password_hash': password_hash,
                                                 'user_id': str(data['sender']['user_id']),
                                                 'api_key': ENGINE_TRIBE_API_KEY}) as response:
                    response_json = await response.json()
                if 'success' in response_json:
                    await send_group_msg(data['group_id'],
                                         f'🎉 注册成功，现在可以使用 {response_json["username"]} 在游戏中登录了。')
                    await delete_msg(data['message_id'])
                else:
                    if response_json['error_type'] == '035':
                        await send_group_msg(data['group_id'], f'❌ 注册失败。\n一个 QQ 号只能注册一个帐号，\n'
                                                               f'{response_json["username"]} 不能再注册账号了。')
                    elif response_json['error_type'] == '036':
                        await send_group_msg(data['group_id'], f'❌ 注册失败。\n'
                                                               f'{response_json["username"]}'
                                                               f' 用户名已经存在，请回到注册网页换一个用户名。')
                    else:
                        await send_group_msg(data['group_id'], f'❌ 注册失败，发生未处理的错误。\n'
                                                               f'{response_json["error_type"]}\n'
                                                               f'{response_json["message"]}')
            elif operation == 'c':  # change password
                async with aiohttp.request(method='POST',
                                           url=ENGINE_TRIBE_HOST + '/user/update_password',
                                           json={'username': username, 'password_hash': password_hash,
                                                 'user_id': str(data['sender']['user_id']),
                                                 'api_key': ENGINE_TRIBE_API_KEY}) as response:
                    response_json = await response.json()
                if 'success' in response_json:
                    await send_group_msg(data['group_id'], f'🎉 {response_json["username"]} 的密码修改成功。')
                else:
                    await send_group_msg(data['group_id'], '❌ 修改密码失败，用户错误。')
            else:
                await send_group_msg(data['group_id'], f'❌ 无效的注册码，所选的操作 {operation} 不存在。')
        except Exception as e:
            await send_group_msg(data['group_id'], '❌ 无效的注册码，请检查是否复制完全。\n错误信息: ' + str(e))
            return


async def command_ban(data):
    if not data['sender']['user_id'] in GAME_ADMIN:
        await send_group_msg(data['group_id'], '❌ 无权使用该命令。')
        return
    if not data['parameters']:
        await send_group_msg(data['group_id'], '使用方法: e!ban 用户名')
        return
    else:
        try:
            username = data['parameters'].split(' ')[0]
            async with aiohttp.request(method='POST',
                                       url=ENGINE_TRIBE_HOST + '/user/update_permission',
                                       json={'username': username, 'permission': 'banned',
                                             'value': True, 'api_key': ENGINE_TRIBE_API_KEY}) as response:
                response_json = await response.json()
            if 'success' in response_json:
                await send_group_msg(data['group_id'], f'✅ 成功封禁 {username} 。')
            else:
                await send_group_msg(data['group_id'], f'❌ 权限更新失败。\n错误信息: {str(response_json)}')
                return
        except Exception as e:
            await send_group_msg(data['group_id'], f'❌ 命令出现错误。\n错误信息: {str(e)}')
            return


async def command_unban(data):
    if not data['sender']['user_id'] in GAME_ADMIN:
        await send_group_msg(data['group_id'], '❌ 无权使用该命令。')
        return
    if not data['parameters']:
        await send_group_msg(data['group_id'], '使用方法: e!unban 用户名')
        return
    else:
        try:
            username = data['parameters'].split(' ')[0]
            async with aiohttp.request(method='POST',
                                       url=ENGINE_TRIBE_HOST + '/user/update_permission',
                                       json={'username': username, 'permission': 'banned',
                                             'value': False, 'api_key': ENGINE_TRIBE_API_KEY}) as response:
                response_json = await response.json()
            if 'success' in response_json:
                await send_group_msg(data['group_id'], f'✅ 成功解除封禁 {username} 。')
            else:
                await send_group_msg(data['group_id'], f'❌ 权限更新失败。\n错误信息: {str(response_json)}')
                return
        except Exception as e:
            await send_group_msg(data['group_id'], f'❌ 命令出现错误。\n错误信息: {str(e)}')
            return


async def command_permission(data):
    if not data['sender']['user_id'] in BOT_ADMIN:
        await send_group_msg(data['group_id'], '❌ 无权使用该命令。')
        return
    if data['message'].strip() == 'e!permission':
        await send_group_msg(data['group_id'], '使用方法: e!permission 用户名 权限名 true或false\n'
                                               '权限列表: mod, admin, booster, valid, banned')
        return
    else:
        try:
            args = data['parameters'].split(' ')
            username = args[0]
            permission = args[1]
            if str(args[2]).lower() == 'true':
                value = True
            else:
                value = False
            async with aiohttp.request(method='POST',
                                       url=ENGINE_TRIBE_HOST + '/user/update_permission',
                                       json={'user_id': data['user_id'], 'permission': permission,
                                             'value': value, 'api_key': ENGINE_TRIBE_API_KEY}) as response:
                response_json = await response.json()
            if 'success' in response_json:
                await send_group_msg(data['group_id'], f'✅ 成功将 {username} 的 {permission} 权限更新为 {str(value)} 。')
            else:
                await send_group_msg(data['group_id'], f'❌ 权限更新失败。\n错误信息: {str(response_json)}')
                return
        except Exception as e:
            await send_group_msg(data['group_id'], f'❌ 命令出现错误。\n错误信息: {str(e)}')
            return


async def command_report(data):
    if data['message'].strip() == 'e!report':
        await send_group_msg(data['group_id'], '❌ 使用方法: e!report 关卡ID')
        return
    else:
        level_id = data['parameters'].split(' ')[0].upper()
        if '-' not in level_id:
            level_id = prettify_level_id(level_id)
        if len(level_id) != 19:
            await send_group_msg(data['group_id'], '❌ 无效的关卡 ID。')
            return
    try:
        async with aiohttp.request(method='POST',
                                   url=f'{ENGINE_TRIBE_HOST}/stage/{level_id}',
                                   data='auth_code=' + BOT_AUTH_CODE,
                                   headers={'Content-Type': 'application/x-www-form-urlencoded',
                                            'User-Agent': 'EngineBot/1'}) as response:
            response_json = await response.json()
        if 'error_type' in response_json:
            await send_group_msg(data['group_id'], '❌ 关卡未找到。')
            return
        else:
            level_data = response_json['result']
        async with aiohttp.request(method='POST',
                                   url=f'{ENGINE_TRIBE_HOST}/user/info',
                                   json={'username': level_data['author']}) as response:
            response_json_user = await response.json()
            message = f'⚠ 接到举报: {level_id} {level_data["name"]} \n' \
                      f'作者: {level_data["author"]}\n' \
                      f'作者 QQ: {response_json_user["result"]["user_id"]}\n' \
                      f'上传于 {level_data["date"]}\n' \
                      f'{level_data["likes"]}❤  {level_data["dislikes"]}💙\n'
            plays = level_data['intentos']
            clears = level_data['victorias']
            deaths = level_data['muertes']
            if int(deaths) == 0:
                message += f'{str(clears)}次通关 / {str(plays)}次游玩\n'
            else:
                message += f'{str(clears)}次通关 / {str(plays)}次游玩 {round((int(clears) / int(deaths)) * 100, 2)} %\n'
            message += f'标签: {level_data["etiquetas"]}, 游戏风格: {styles[int(level_data["apariencia"])]}'
            await send_group_msg(group_id=ADMIN_GROUP, message=message)
            return
    except Exception as e:
        await send_group_msg(data['group_id'], f'❌ 获得 {level_id} 的关卡信息时出现错误，连接到引擎部落后端时出错。\n'
                                               f'错误信息: {str(e)}')
        return


async def command_query(data):
    if not data['parameters']:
        await send_group_msg(data['group_id'], '❌ 使用方法: e!query 关卡ID')
        return
    else:
        level_id = data['parameters'].split(' ')[0].upper()
        if '-' not in level_id:
            level_id = prettify_level_id(level_id)
        if len(level_id) != 19:
            await send_group_msg(data['group_id'], '❌ 无效的关卡 ID。')
            return
        try:
            async with aiohttp.request(method='POST',
                                       url=f'{ENGINE_TRIBE_HOST}/stage/{level_id}',
                                       data='auth_code=' + BOT_AUTH_CODE,
                                       headers={'Content-Type': 'application/x-www-form-urlencoded',
                                                'User-Agent': 'EngineBot/1'}) as response:
                response_json = await response.json()
            if 'error_type' in response_json:
                await send_group_msg(data['group_id'], '❌ 关卡未找到。')
                return
            else:
                level_data = response_json['result']
                message = f'🔍 查询关卡: {level_data["name"]} \n' \
                          f'作者: {level_data["author"]}\n' \
                          f'上传于 {level_data["date"]}\n' \
                          f'{level_data["likes"]}❤  {level_data["dislikes"]}💙'
                if int(level_data['featured']) == 1:
                    message += ' (管理推荐关卡)\n'
                else:
                    message += '\n'
                clears = level_data['victorias']
                plays = level_data['intentos']
                deaths = level_data['muertes']
                if int(deaths) == 0:
                    message += f'{str(clears)}次通关 / {str(plays)}次游玩\n'
                else:
                    message += f'{str(clears)}次通关 / {str(plays)}次游玩 {round((int(clears) / int(deaths)) * 100, 2)} %\n'
                message += f'标签: {level_data["etiquetas"]}, 游戏风格: {styles[int(level_data["apariencia"])]}'
                await send_group_msg(group_id=data['group_id'], message=message)
                return
        except Exception as e:
            await send_group_msg(data['group_id'], f'❌ 命令出现错误，连接到引擎部落后端时出错。\n错误信息: {str(e)}')
            return


async def command_random(data):
    try:
        async with aiohttp.request(method='POST',
                                   url=f'{ENGINE_TRIBE_HOST}/stage/random',
                                   data='auth_code=' + BOT_AUTH_CODE,
                                   headers={'Content-Type': 'application/x-www-form-urlencoded',
                                            'User-Agent': 'EngineBot/1'}) as response:
            response_json = await response.json()
        level_data = response_json['result']
        message = f'💫 随机关卡: {level_data["id"]} {level_data["name"]} \n' \
                  f'作者: {level_data["author"]}\n' \
                  f'上传于 {level_data["date"]}\n' \
                  f'{level_data["likes"]}❤  {level_data["dislikes"]}💙'
        if int(level_data['featured']) == 1:
            message += ' (管理推荐关卡)\n'
        else:
            message += '\n'
        clears = level_data['victorias']
        plays = level_data['intentos']
        deaths = level_data['muertes']
        if int(deaths) == 0:
            message += f'{str(clears)}次通关 / {str(plays)}次游玩\n'
        else:
            message += f'{str(clears)}次通关 / {str(plays)}次游玩 {round((int(clears) / int(deaths)) * 100, 2)} %\n'
        message += f'标签: {level_data["etiquetas"]}, 游戏风格: {styles[int(level_data["apariencia"])]}'
        await send_group_msg(group_id=data['group_id'], message=message)
        return
    except Exception as e:
        await send_group_msg(data['group_id'], f'❌ 命令出现错误，连接到引擎部落后端时出错。\n错误信息: {str(e)}')
        return


async def command_stats(data):
    if not data['parameters']:
        request_body = {'user_id': data['sender']['user_id']}
    else:
        request_body = {'username': data['parameters'].split(' ')[0]}
    try:
        async with aiohttp.request(method='POST',
                                   url=f'{ENGINE_TRIBE_HOST}/user/info',
                                   json=request_body) as response:
            response_json = await response.json()
        if 'error_type' in response_json:
            await send_group_msg(data['group_id'], '❌ 数据不存在。')
            return
        else:
            user_data = response_json['result']
            messages = []
            message = f'📜 玩家 {user_data["username"]} 的上传记录\n' \
                      f'共上传了 {user_data["uploads"]} 个关卡。'
            messages.append(message)
            if str(user_data['uploads']) == '0':
                await send_group_msg(group_id=data['group_id'], message=message)
                return
            else:
                all_likes = 0
                all_dislikes = 0
                all_plays = 0
                async with aiohttp.request(method='POST',
                                           url=f'{ENGINE_TRIBE_HOST}/stages/detailed_search',
                                           data={'auth_code': BOT_AUTH_CODE, 'author': user_data['username']},
                                           headers={'Content-Type': 'application/x-www-form-urlencoded',
                                                    'User-Agent': 'EngineBot/1'}) as response:
                    levels_data = await response.json()
                for level_data in levels_data['result']:
                    message = f'- {level_data["name"]}\n' \
                              f'  {level_data["likes"]}❤  {level_data["dislikes"]}💙\n' \
                              f'  {level_data["id"]}'
                    if int(level_data['featured']) == 1:
                        message += ' (推荐)\n'
                    else:
                        message += '\n'
                    message += f'  标签: {level_data["etiquetas"]}'
                    messages.append(message)
                    all_likes += int(level_data['likes'])
                    all_dislikes += int(level_data['dislikes'])
                    all_plays += int(level_data['intentos'])
                message = f'总获赞: {all_likes}' \
                          f'总获孬: {all_dislikes}' \
                          f'总游玩: {all_plays}'
                messages.append(message)
                await send_group_forward_msg(group_id=data['group_id'], messages=messages, sender_name='记录查询')
                return
    except Exception as e:
        await send_group_msg(data['group_id'], f'❌ 命令出现错误，连接到引擎部落后端时出错。\n错误信息: {str(e)}')
        return


async def command_server(data):
    try:
        async with aiohttp.request(method='GET',
                                   url=f'{ENGINE_TRIBE_HOST}/server_stats') as response:
            response_json = await response.json()
        message = f'🗄️ 服务器状态\n' \
                  f'🐧 操作系统: {response_json["os"]}\n' \
                  f'🐍 Python 版本: {response_json["python"]}\n' \
                  f'👥 玩家数量: {response_json["player_count"]}\n' \
                  f'🌏 关卡数量: {response_json["level_count"]}\n' \
                  f'🕰️ 运行时间: {int(response_json["uptime"] / 60)} 分钟\n' \
                  f'📊 每分钟连接数: {response_json["connection_per_minute"]}'
        await send_group_msg(data['group_id'], message)
        return
    except Exception as e:
        await send_group_msg(data['group_id'], '未知错误 ' + str(e))
        return


async def command_execute(data):
    try:
        process = subprocess.Popen(data['parameters'], shell=True, stdout=subprocess.PIPE)
        process.wait()
        await send_group_msg(data['group_id'], process.stdout.read().decode())
    except Exception as e:
        await send_group_msg(data['group_id'], '未知错误 ' + str(e))
        return


async def command_sql(data):
    try:
        process = subprocess.Popen(['/home/yidaozhan/exesql.sh', data['parameters']], shell=False,
                                   stdout=subprocess.PIPE)
        process.wait()
        await send_group_msg(data['group_id'], process.stdout.read().decode())
    except Exception as e:
        await send_group_msg(data['group_id'], '未知错误 ' + str(e))
        return


def prettify_level_id(level_id: str):
    return level_id[0:4] + '-' + level_id[4:8] + '-' + level_id[8:12] + '-' + level_id[12:16]
