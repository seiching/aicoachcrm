from pyngrok import ngrok
import requests
import time
import json
import configparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import deque
from datetime import datetime, timezone, timedelta

config = configparser.ConfigParser()
config.read("config.ini")
Line_Channel_Access_Token = config["Line"]["CHANNEL_ACCESS_TOKEN"]
NGROK_AUTH_TOKEN = config["ngrok"]["NGROK_AUTH_TOKEN"]


def auto_update_webhook_url(stop_event):
    global ngrok_url
    print('NGROK_AUTH_TOKEN', NGROK_AUTH_TOKEN)
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    public_url = ngrok.connect(5000)
    print("ngrok URL:", public_url)
    while not stop_event.is_set():
        time.sleep(5)  # 等候5秒讓ngrok完成註冊新網址
        try:
            # 取得ngrok最新產生的url
            self_url = "http://localhost:4040/api/tunnels"
            res = requests.get(self_url)
            res.raise_for_status()
            res_unicode = res.content.decode("utf-8")
            res_json = json.loads(res_unicode)
            ngrok_url = res_json["tunnels"][0]["public_url"]

            # 開始更新
            line_put_endpoint_url = "https://api.line.me/v2/bot/channel/webhook/endpoint"
            data = {"endpoint": ngrok_url + '/callback'}
            headers = {
                "Authorization": "Bearer " + Line_Channel_Access_Token,
                "Content-Type": "application/json"
            }
            print(data)
            res = requests.put(line_put_endpoint_url, headers=headers, json=data)
            res.raise_for_status()  # 檢查響應狀態碼

            print("WebhookURL更新成功！")
            stop_event.set()  # 更新成功后停止线程
        except requests.ConnectionError as e:
            print(f"連接錯誤：{e}")
        except requests.RequestException as e:
            print(f"請求錯誤：{e}")
        except json.JSONDecodeError as e:
            print(f"JSON解析錯誤：{e}")
        except Exception as e:
            print(f"其他錯誤：{e}")
            stop_event.set()  # 發生未知錯誤時停止线程


def prepare_ngrok():
    from pyngrok import ngrok
    import requests

    ngrok.set_auth_token(NGROK_AUTH_TOKEN)

    public_url = ngrok.connect(5000)
    print("ngrok URL:", public_url)

    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        response.raise_for_status()
        tunnels_info = response.json()
        print(tunnels_info)
    except requests.ConnectionError as e:
        print(f"连接错误：{e}")
    except requests.RequestException as e:
        print(f"请求错误：{e}")


def get_google_sheet(key_file):
    # google drive access
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive"]
    # spredsheet url
    # https://docs.google.com/spreadsheets/d/1U8Xa8UaJYWISzoaQEEn6AUpKDiO7ROwL11PBQYe-m1w/edit?usp=sharing
    # spreadsheet url
    # sheets = client.open("customerlog")
    # Config Parser
    credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file, scope)
    client = gspread.authorize(credentials)
    workbook = client.open("LLM_worksheet")

    sheet_limit = workbook.worksheet('limit')  # user limit sheet
    user_limit = int(sheet_limit.acell('A1').value)
    sheet_data = workbook.worksheet('data')  # sheet get live guide
    liveguide = sheet_data.get_all_records()
    liveguide = " ".join(str(element) for element in liveguide)

    sheet_prompt = workbook.worksheet('prompt')  # sysmtem prompt about action
    actoraction = sheet_prompt.acell('A1').value
    sheet_log = workbook.worksheet('log')  # user log sheet

    return user_limit, liveguide, actoraction, sheet_log


def add_user_msg(user_id, user_input, agent_output, user_conversations):
    """
    添加使用者輸入和代理輸出到對話記錄中。
    如果使用者的對話記錄超過7筆,就用新的記錄替換最舊的記錄。
    """
    if user_id in user_conversations:
        # 如果對話記錄已存在,就添加新的記錄
        user_conversations[user_id].append((user_input, agent_output))
        # 如果對話記錄超過7筆,就刪除最舊的記錄
        if len(user_conversations[user_id]) > 7:
            user_conversations[user_id].popleft()
    else:
        # 如果對話記錄不存在,就創建新的記錄
        user_conversations[user_id] = deque([(user_input, agent_output)], maxlen=7)


def get_taipeitime():
    """
    取得當地時間並轉換為台北時間

    Returns:
        datetime: 台北時間
    """
    # 取得當前時區
    local_tz = datetime.now(timezone.utc).astimezone().tzinfo

    # 台北時區
    taipei_tz = timezone(timedelta(hours=8))

    # 取得當地時間
    local_time = datetime.now().replace(tzinfo=local_tz)

    # 轉換為台北時間
    taipei_time = local_time.astimezone(taipei_tz)

    return taipei_time


def pop_user_msg(user_id, user_conversations):
    """
    返回指定使用者的所有對話記錄,按時間順序排列。
    """
    if user_id in user_conversations:
        return list(user_conversations[user_id])
    else:
        return []

import hashlib


def idhash(lineid):
    # 建立 SHA1 物件
    s = hashlib.sha1()
    s.update(lineid.encode("utf-8"))
    h = s.hexdigest()
    return h
