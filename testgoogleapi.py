# 測試google api讀取完成
# google create project https://console.cloud.google.com/?hl=zh-TW
# enable google spreaed sheet service https://console.cloud.google.com/marketplace/product/google/sheets.googleapis.com?q=search&referrer=search&hl=zh-TW&project=search-console-api-238810
# create service account 建立服務帳號及copy其地址
# download the id json file
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime
# Connect to Google
# Scope: Enable access to specific links
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("aicoach-xxx.json", scope)
client = gspread.authorize(credentials)
workbook = client.open("testapi") #個人帳號授權給服務帳號的spread sheet
sheet=workbook.get_worksheet(0)
user_limit= int(sheet.acell('A1').value)
print(user_limit)
