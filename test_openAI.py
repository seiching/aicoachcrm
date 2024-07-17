from openai import OpenAI
import configparser

config = configparser.ConfigParser()
config.read("config.ini")
LLM_api_key = config["openai"]["API_KEY"]

client = OpenAI(api_key=LLM_api_key)
completion = client.chat.completions.create(
  model="gpt-3.5-turbo-0125",
  messages=[
    {"role": "system", "content": ""},
    {"role": "user", "content": "你是誰？"}
  ]
)

print(completion.choices[0].message)
