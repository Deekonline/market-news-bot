import requests
import json
import os


TOKEN = "8637154006:AAH5n2BM9y9T7AzHPXWhcywG0vuAcQ2mkMM"
CHAT_ID = "2126714028"


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

headers = {"User-Agent":"Mozilla/5.0","Accept":"application/json"}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers)

LAST_FILE = "last.json"

# ---------- MEMORY ----------
def load_last():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE,"r") as f:
            return json.load(f)
    return {"history": []}

def save_last(data):
    with open(LAST_FILE,"w") as f:
        json.dump(data,f)

def is_new(key):
    if key in last["history"]:
        return False
    last["history"].append(key)
    if len(last["history"]) > 100:
        last["history"].pop(0)
    return True

last = load_last()

score = 0
signals = []

# ---------- LIVE PRICE ----------
def get_price(symbol):
    try:
        url = f"https://www.nseindia.com/api/quote-derivative?symbol={symbol}"
        r = session.get(url, headers=headers)
        data = r.json()
        return data["underlyingValue"]
    except:
        return None

nifty_price = get_price("NIFTY")

# ---------- NSE NEWS ----------
try:
    r = session.get("https://www.nseindia.com/api/corporate-announcements?index=equities", headers=headers)
    data = r.json()
    item = data["data"][0]

    key = item["headline"]

    if is_new(key):
        send(f"🟢 NSE\n{item['symbol']}\n{item['headline']}")
        score += 2
        signals.append("NSE news")
except:
    pass

# ---------- BSE ----------
try:
    r = requests.get("https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?strCat=-1", headers=headers)
    data = r.json()
    item = data["Table"][0]

    key = item["HEADLINE"]

    if is_new(key):
        send(f"🔵 BSE\n{item['SCRIPNAME']}\n{item['HEADLINE']}")
        score += 2
        signals.append("BSE news")
except:
    pass

# ---------- TRENDLYNE ----------
try:
    r = requests.get("https://trendlyne.com/api/market-news/", headers=headers)
    data = r.json()
    title = data["results"][0]["title"]

    if is_new(title):
        send(f"🟠 TRENDLYNE\n{title}")
        score += 2
        signals.append("Trendlyne")
except:
    pass

# ---------- F&O ----------
def fno(symbol):
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        r = session.get(url, headers=headers)
        data = r.json()

        ce_max = pe_max = 0

        for i in data["records"]["data"]:
            if "CE" in i and "PE" in i:
                ce_max = max(ce_max, i["CE"]["openInterest"])
                pe_max = max(pe_max, i["PE"]["openInterest"])

        return "bullish" if pe_max > ce_max else "bearish"
    except:
        return "neutral"

nifty_dir = fno("NIFTY")

if nifty_dir == "bullish":
    score += 3
    signals.append("F&O bullish")
elif nifty_dir == "bearish":
    score -= 3
    signals.append("F&O bearish")

# ---------- VOLUME ----------
try:
    r = session.get("https://www.nseindia.com/api/live-analysis-volume?index=all", headers=headers)
    data = r.json()

    for stock in data["data"][:5]:
        if float(stock["totalTradedVolume"]) > 5000000:
            key = stock["symbol"] + "_vol"

            if is_new(key):
                score += 2
                signals.append("Volume spike")
            break
except:
    pass

# ---------- DECISION ----------
decision = "NEUTRAL"

if score >= 6:
    decision = "BULLISH"
elif score <= -6:
    decision = "BEARISH"

# ---------- TRADE ----------
def round_strike(price, step):
    return int(round(price / step) * step)

if decision != "NEUTRAL" and nifty_price:

    entry = nifty_price
    sl = entry * 0.995 if decision == "BULLISH" else entry * 1.005
    target = entry * 1.01 if decision == "BULLISH" else entry * 0.99

    strike = round_strike(nifty_price, 50)
    option = f"{strike} CE" if decision == "BULLISH" else f"{strike} PE"

    confidence = min(abs(score) * 15, 95)

    key = decision + str(strike)

    if is_new(key):
        send(f"""
🚨 HIGH CONVICTION TRADE

Bias: {decision}
Confidence: {confidence}%

Entry: {round(entry,2)}
SL: {round(sl,2)}
Target: {round(target,2)}

Option: Buy {option}

Signals:
- {' | '.join(signals)}
""")

save_last(last)