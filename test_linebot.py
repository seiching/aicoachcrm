from flask import *
from flask_ngrok import run_with_ngrok

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
import threading
import configparser

from util import auto_update_webhook_url, prepare_ngrok

app = Flask(__name__)
run_with_ngrok(app)

config = configparser.ConfigParser()
config.read("config.ini")
LLM_api_key = config["openai"]["API_KEY"]
print('LLM_api_key', LLM_api_key)
line_channel_access_token = config["Line"]["CHANNEL_ACCESS_TOKEN"]
print('line_channel_access_token', line_channel_access_token)
line_channel_secret = config["Line"]["CHANNEL_SECRET"]
print('line_channel_secret', line_channel_secret)

# Basic settings/Channel secret
handler = WebhookHandler(line_channel_secret)
configuration = Configuration(
    access_token=line_channel_access_token
)


@app.route("/")
def home():
    return "我是大帥哥"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)]
            )
        )


if __name__ == "__main__":
    stop_event = threading.Event()
    x = threading.Thread(target=auto_update_webhook_url, args=(stop_event,))
    x.start()
    # prepare_ngrok()
    app.run()
