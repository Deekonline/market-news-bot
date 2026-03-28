
import requests

TOKEN = "YOUR_TOKEN"
CHAT_ID = "2126714028"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.bseindia.com/"
}

url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?strCat=-1&strPrevDate=&strScrip=&strSearch=P&strToDate=&strType=C"

r = requests.get(url, headers=headers)

print(r.text)

try:
    data = r.json()

    for item in data["Table"][:5]:
        title = item["HEADLINE"]
        company = item["SCRIPNAME"]

        send(f"🚨 {company}\n{title}")

except Exception as e:
    send("Bot running but no data yet")