import sys
import configparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Azure OpenAI
import os
from openai import AzureOpenAI

from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from collections import deque

# 用於儲存使用者對話記錄的字典
user_conversations = {}
from datetime import datetime, timezone, timedelta

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
def add_user_msg(user_id, user_input, agent_output):
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

def pop_user_msg(user_id):
    """
    返回指定使用者的所有對話記錄,按時間順序排列。
    """
    if user_id in user_conversations:
        return list(user_conversations[user_id])
    else:
        return []

# google drive access 
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("aicoach-xxxxxxxx.json", scope)
client = gspread.authorize(credentials)
#workbook = client.open("customerlog")
workbook = client.open("aicoach")
# spredsheet url 
# https://docs.google.com/spreadsheets/d/1U8Xa8UaJYWISzoaQEEn6AUpKDiO7ROwL11PBQYe-m1w/edit?usp=sharing
# spreadsheet url
#sheets = client.open("customerlog")
# Config Parser
config = configparser.ConfigParser()
config.read("config.ini")

# Azure OpenAI Key
# client = AzureOpenAI(
#     api_key=config["AzureOpenAI"]["KEY"],
#     api_version=config["AzureOpenAI"]["VERSION"],
#     azure_endpoint=config["AzureOpenAI"]["BASE"],
# )

from openai import OpenAI
#hugapikey=os.environ['openaikey']
#print(hugapikey)
hugapikey=config["openai"]["API_KEY"]
client = OpenAI( api_key=hugapikey)
# client = AzureOpenAI(
#     api_key=config["AzureOpenAIchat"]["KEY"],
#     api_version=config["AzureOpenAIchat"]["VERSION"],
#     azure_endpoint=config["AzureOpenAIchat"]["BASE"],
# )

app = Flask(__name__)
user_calls = {}

sheet = workbook.get_worksheet(1) # user limit sheet
user_limit= int(sheet.acell('A1').value)
sheet = workbook.get_worksheet(3) #  sheet get live guide
liveguide= sheet.get_all_records()
liveguide=" ".join(str(element) for element in liveguide)
sheet = workbook.get_worksheet(4) #  sysmtem prompt about action
actoraction= sheet.get_all_records()
actoraction=" ".join(str(element) for element in actoraction)

sheet = workbook.get_worksheet(0) # user log sheet
#user_limit=2000
from datetime import datetime, timedelta
def track_calls(user_id):
    # 获取当前时间
    now = get_taipeitime()

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
            #print('over',user_calls[user_id]['count'] ,user_limit)
            return False
        else :
            #print('notover')
            return True
import hashlib
def idhash(lineid):

   # 建立 SHA1 物件
   s = hashlib.sha1()

   s.update(lineid.encode("utf-8"))

   h = s.hexdigest()
   return h
channel_access_token = config["Line"]["CHANNEL_ACCESS_TOKEN"]
channel_secret = config["Line"]["CHANNEL_SECRET"]
if channel_secret is None:
    #print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    #print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(access_token=channel_access_token)

@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    #app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    print('ok')
    if (event.message.text[0]=='/'):
        
        from datetime import datetime,timezone,timedelta
        twtimenow = get_taipeitime()
        twtimenow=twtimenow.strftime("%m/%d/%Y, %H:%M:%S")
        userid=event.source.user_id
        userinput=event.message.text[1:]

        if(not track_calls(userid)):
            msgresult='您已超過今天使用額度，請明天再來'
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
        #username=line_bot_api.get_profile (event.source.user_id)
          
                sheet.append_rows([[idhash(userid),twtimenow,userinput,msgresult]])
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=msgresult)],
                   )
                )
            return   
        
        # msgresult='請等一下'
        # with ApiClient(configuration) as api_client:
        #         line_bot_api = MessagingApi(api_client)
        # #username=line_bot_api.get_profile (event.source.user_id)
          
        # #        sheet.append_rows([[idhash(userid),twtimenow,userinput,msgresult]])
        #         line_bot_api.reply_message_with_http_info(
        #             ReplyMessageRequest(
        #                 reply_token=event.reply_token,
        #                 messages=[TextMessage(text=msgresult)],
        #            )
        #         )     
           

        azure_openai_result = azure_openai(userid,event.message.text[1:])
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
        #username=line_bot_api.get_profile (event.source.user_id)
            sheet.append_rows([[idhash(userid),twtimenow,userinput,azure_openai_result]])
            add_user_msg(userid, {'role':'user','content':userinput}, {'role':'assistant','content':azure_openai_result})
                
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=azure_openai_result)],
                )
            )

        
    else:
        return
    
def azure_openai(userid,user_input):
    message_text = [
        {
            "role": "system",
            "content": "",
        },
        #{"role": "user", "content": user_input},
    ]
    

   # message_text[0]["content"] += "你是一個中油訓練所學員管理人員,負責回答有關<學員注意事項>中有關<食>，<衣>，<住>，<行>，<育>，<樂> 的問題，"

    #message_text[0]["content"] += "請一律用肯定句的繁體中文回答，不可用疑問句反問使用者，根據以下<學員注意事項>的內容將使用者問題分類成，<食>，<衣>，<住>，<行>，<育>，<樂>，回答時要說明根據 <學員注意事項>的內容那一個分類進行回答，如<樂>"
    #message_text[0]["content"] += "然後根據分類在<學員注意事項>中找出合適的答案，並在回答前一步一步重新檢查分類是否正確及是否為<學員注意事項>的內容，若根據<學員注意事項>不屬於<食>，<衣>，<住>，<行>，<育>，<樂> 分類，且<學員注意事項>沒有寫的內容，請很客氣的回答根據<學員注意事項>沒有相關資訊，例如有人請你介紹健身房，你要根據<學員注意事項>找<樂>，並回答根據<學員注意事項>的<樂>分類中有關健身房內容，再接你的回答；若有人問政治問題，你根據<學員注意事項>先分類，不屬於其中的<食>，<衣>，<住>，<行>，<育>，<樂> 的分類，也要很客氣的回答不清楚；總之只要使用者問題不屬於以下分類<食>，<衣>，<住>，<行>，<育>，<樂>或<學員注意事項>中沒有寫的你都要很客氣的回答不清楚；不要反問使用者，例如你不可以回答<你是學員嗎？>，你必須以肯定的語句回答，即使對使用者問題不清楚，請很客氣回答根據<學員注意事項>沒有相關資訊；總之你的所有回答必須基於<學員注意事項>，不能回答根據<學員注意事項>沒有的資訊。"
    message_text[0]["content"] += actoraction+'。'+liveguide

    chathistory=pop_user_msg(userid)
    #print(type(message_text),len(message_text))
    #print('ok')
    newmessage=message_text.copy()
    for chatitem in chathistory:
       newmessage.append(chatitem[0])
       newmessage.append(chatitem[1])
       #print('item', chatitem[0],chatitem[1])
    # print('okok')
    #newmessage.append(chathistory)
    #print('before',len(newmessage))
    #newmessage=list(newmessage)
    #print(type(newmessage),len(newmessage))
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
    #print(completion)
    return completion.choices[0].message.content

#https://60d8-2401-e180-8850-6677-6d56-d31c-cc46-9b48.ngrok-free.app
# https://60d8-2401-e180-8850-6677-6d56-d31c-cc46-9b48.ngrok-free.app 
#https://60d8-2401-e180-8850-6677-6d56-d31c-cc46-9b48.ngrok-free.app/callback
#https://cpchotel.azurewebsites.net/callback
#https://twstoryteller.azurewebsites.net/callback
if __name__ == "__main__":
    app.run()
