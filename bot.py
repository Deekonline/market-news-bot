import requests

TOKEN = "8637154006:AAH5n2BM9y9T7AzHPXWhcywG0vuAcQ2mkMM"
CHAT_ID = "2126714028"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# -------- BSE --------
try:
    bse_url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?strCat=-1&strPrevDate=&strScrip=&strSearch=P&strToDate=&strType=C"
    r = requests.get(bse_url, headers=headers)

    if "Table" in r.text:
        data = r.json()

        for item in data["Table"][:3]:
            company = item["SCRIPNAME"]
            title = item["HEADLINE"]

            send(f"🔵 BSE\n{company}\n{title}")

except:
    pass


# -------- NSE --------
try:
    session = requests.Session()

    session.get("https://www.nseindia.com", headers=headers)

    nse_url = "https://www.nseindia.com/api/corporate-announcements?index=equities"
    r = session.get(nse_url, headers=headers)

    if "data" in r.text:
        data = r.json()

        for item in data["data"][:3]:
            company = item["symbol"]
            title = item["headline"]

            send(f"🟢 NSE\n{company}\n{title}")

except:
    pass

