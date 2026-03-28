import requests
import time

TOKEN = "YOUR_TOKEN"
CHAT_ID = "2126714028"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

seen = set()

url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?strCat=-1&strPrevDate=&strScrip=&strSearch=P&strToDate=&strType=C"
data = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}).json()

for item in data["Table"][:10]:
    title = item["HEADLINE"]
    company = item["SCRIPNAME"]

    msg = f"🚨 {company}\n{title}"
    send(msg)
