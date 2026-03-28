import requests

TOKEN = "YOUR_TOKEN"
CHAT_ID = "2126714028"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": "✅ BOT WORKING - TEST MESSAGE"
})