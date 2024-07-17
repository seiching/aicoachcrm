
from pyngrok import ngrok
import requests
import configparser

config = configparser.ConfigParser()
config.read("config.ini")
NGROK_AUTH_TOKEN = config["gnrok"]["NGROK_AUTH_TOKEN"]

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
