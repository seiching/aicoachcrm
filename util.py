from pyngrok import ngrok
import requests
import time
import json
import configparser

config = configparser.ConfigParser()
config.read("config.ini")
Line_Channel_Access_Token = config["Line"]["CHANNEL_ACCESS_TOKEN"]
NGROK_AUTH_TOKEN = config["gnrok"]["NGROK_AUTH_TOKEN"]

def auto_update_webhook_url(stop_event):
    global ngrok_url
    print('NGROK_AUTH_TOKEN',NGROK_AUTH_TOKEN)
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
