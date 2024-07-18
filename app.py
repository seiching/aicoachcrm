import sys
import configparser
import threading
import util
# Azure OpenAI
import os
from openai import AzureOpenAI

from flask import Flask, request, abort
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

# 用於儲存使用者對話記錄的字典
user_conversations = {}
from datetime import datetime, timezone, timedelta

config = configparser.ConfigParser()
config.read("config.ini")
LLM_api_key = config["openai"]["API_KEY"]
print('LLM_api_key', LLM_api_key)
line_channel_access_token = config["Line"]["CHANNEL_ACCESS_TOKEN"]
print('line_channel_access_token', line_channel_access_token)
line_channel_secret = config["Line"]["CHANNEL_SECRET"]
print('line_channel_secret', line_channel_secret)
key_file = config["google"]["key_file"]

from openai import OpenAI

app = Flask(__name__)
run_with_ngrok(app)

client = OpenAI(api_key=LLM_api_key)
# client = AzureOpenAI(
#     api_key=config["AzureOpenAIchat"]["KEY"],
#     api_version=config["AzureOpenAIchat"]["VERSION"],
#     azure_endpoint=config["AzureOpenAIchat"]["BASE"],
# )
handler = WebhookHandler(line_channel_secret)
configuration = Configuration(
    access_token=line_channel_access_token
)

user_calls = {}
user_limit, liveguide, actoraction, sheet_log = util.get_google_sheet(key_file)


def track_calls(user_id):
    # 获取当前时间
    now = util.get_taipeitime()

    # 如果用户第一次调用,初始化计数
    if user_id not in user_calls:
        # print('first')
        user_calls[user_id] = {
            'last_reset': now.replace(hour=0, minute=0, second=0, microsecond=0),
            'count': 1
        }
        return True
    else:
        # 检查是否需要重置计数器
        if now >= user_calls[user_id]['last_reset'] + timedelta(days=1):
            user_calls[user_id] = {
                'last_reset': now.replace(hour=0, minute=0, second=0, microsecond=0),
                'count': 1
            }
        else:
            # 增加计数
            user_calls[user_id]['count'] += 1

        # 检查是否超出限制
        if user_calls[user_id]['count'] > user_limit:
            # print('over',user_calls[user_id]['count'] ,user_limit)
            return False
        else:
            # print('notover')
            return True


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    # app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    print('event.message.text', event.message.text)
    if event.message.text[0] == '/':
        twtimenow = util.get_taipeitime()
        twtimenow = twtimenow.strftime("%m/%d/%Y, %H:%M:%S")
        userid = event.source.user_id
        userinput = event.message.text[1:]
        if (not track_calls(userid)):
            msg_result = '您已超過今天使用額度，請明天再來'
            # username=line_bot_api.get_profile (event.source.user_id)
            sheet_log.append_rows([[util.idhash(userid), twtimenow, userinput, msg_result]])
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=msg_result)]
                    )
                )
            return

        azure_openai_result = azure_openai(userid, userinput)
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            # username=line_bot_api.get_profile (event.source.user_id)
            sheet_log.append_rows([[util.idhash(userid), twtimenow, userinput, azure_openai_result]])
            util.add_user_msg(userid, {'role': 'user', 'content': userinput},
                              {'role': 'assistant', 'content': azure_openai_result}, user_conversations)

            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=azure_openai_result)]
                )
            )
    else:
        msg_result = '客服小幫手\n1. 請於每則要發送的問題之前加上斜線（/），以啟用智能客服。\n2. 因客服系統為透過生成式 AI 產生答覆，故可能發生錯誤，請查核重要資訊。'
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=msg_result)]
                )
            )


def azure_openai(userid, user_input):
    message_text = [
        {"role": "system", "content": ""},
        # {"role": "user", "content": user_input},
    ]
    message_text[0]["content"] += actoraction + '。' + liveguide
    chat_history = util.pop_user_msg(userid, user_conversations)

    newmessage = message_text.copy()
    for chatitem in chat_history:
        newmessage.append(chatitem[0])
        newmessage.append(chatitem[1])
        # print('item', chatitem[0], chatitem[1])

    newmessage.append({"role": "user", "content": user_input})
    completion = client.chat.completions.create(
        model=config["model"]["modelname"],
        messages=newmessage,
        max_tokens=2800,
        top_p=0.5,
        frequency_penalty=0,
        presence_penalty=0,
        temperature=0,
        stop=None,
    )

    return completion.choices[0].message.content


if __name__ == "__main__":
    stop_event = threading.Event()
    x = threading.Thread(target=util.auto_update_webhook_url, args=(stop_event,))
    x.start()
    # prepare_ngrok()
    app.run()
