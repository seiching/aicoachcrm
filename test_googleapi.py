# 測試google api讀取完成
# google create project https://console.cloud.google.com/?hl=zh-TW
# enable google spreaed sheet service https://console.cloud.google.com/marketplace/product/google/sheets.googleapis.com?q=search&referrer=search&hl=zh-TW&project=search-console-api-238810
# create service account 建立服務帳號及copy其地址
# download the id json file
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import configparser

# Connect to Google
# Scope: Enable access to specific links
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

config = configparser.ConfigParser()
config.read("config.ini")
key_file = config["google"]["key_file"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(key_file, scope)  # key_file: Google OAuth 2.0 憑證檔
client = gspread.authorize(credentials)
workbook = client.open("LLM_worksheet")  # 個人帳號授權給服務帳號的spread sheet
sheet = workbook.worksheet('limit')
user_limit = int(sheet.acell('A1').value)
print(user_limit)

log_sheet = workbook.worksheet('log')
rows = [
    ["Name", "Age", "City"],
    ["Alice", 30, "New York"],
    ["Bob", 25, "San Francisco"],
    ["Charlie", 35, "Los Angeles"]
]

# 追加多行數據到工作表
log_sheet.append_rows(rows)
print('Add data to worksheet')
