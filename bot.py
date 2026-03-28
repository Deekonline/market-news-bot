
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

# ---------- MEMORY ----------
LAST_FILE = "last.json"

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

# ---------- TRENDLYNE ----------
try:
    url = "https://trendlyne.com/latest-news/"
    r = requests.get(url, headers=headers)
    html = r.text

    matches = re.findall(r'<a[^>]*class=".*?title.*?"[^>]*>(.*?)</a>', html)

    POSITIVE = ["order","wins","contract","agreement","acquire","acquisition",
                "stake buy","buy","investment","partnership","merger"]

    NEGATIVE = ["sell","stake sale","loss","decline","fraud","penalty",
                "resign","default","downgrade"]

    for title in matches[:10]:
        clean = title.lower().strip()
        stock = clean.split()[0].upper() if clean else "UNKNOWN"

        impact = "NEUTRAL"
        if any(k in clean for k in POSITIVE):
            impact = "BULLISH"
        elif any(k in clean for k in NEGATIVE):
            impact = "BEARISH"

        key = f"{stock}_{impact}"

        if impact != "NEUTRAL" and is_new(key):
            emoji = "🟢" if impact == "BULLISH" else "🔴"
            send(f"{emoji} TRENDLYNE ({impact})\n\nStock: {stock}\n\nNews:\n{title}")

            score += 2
            signals.append(f"Trendlyne {impact}")

except:
    pass

# ---------- NSE ----------
try:
    r = session.get("https://www.nseindia.com/api/corporate-announcements?index=equities", headers=headers)
    data = r.json()
    item = data["data"][0]

    if is_new(item["headline"]):
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

    if is_new(item["HEADLINE"]):
        send(f"🔵 BSE\n{item['SCRIPNAME']}\n{item['HEADLINE']}")
        score += 2
        signals.append("BSE news")

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

direction = fno("NIFTY")

if direction == "bullish":
    score += 3
    signals.append("F&O bullish")
elif direction == "bearish":
    score -= 3
    signals.append("F&O bearish")

# ---------- PRICE ----------
def get_price(symbol):
    try:
        url = f"https://www.nseindia.com/api/quote-derivative?symbol={symbol}"
        r = session.get(url, headers=headers)
        return r.json()["underlyingValue"]
    except:
        return None

nifty_price = get_price("NIFTY")
bank_price = get_price("BANKNIFTY")

# ---------- TRADE LOGIC ----------
def trade_logic(name, price, direction):
    if not price or direction == "neutral":
        return None

    strike = round(price / 50) * 50 if name == "NIFTY" else round(price / 100) * 100

    if direction == "bullish":
        option = f"{strike} CE"
        sl = price * 0.995
        target = price * 1.01
    else:
        option = f"{strike} PE"
        sl = price * 1.005
        target = price * 0.99

    return f"""
📊 {name} TRADE IDEA

Bias: {direction.upper()}

Entry: {round(price,2)}
SL: {round(sl,2)}
Target: {round(target,2)}

Option: Buy {option}
"""

# ---------- HIGH CONVICTION SIGNAL ----------
if score >= 4:
    msg = trade_logic("NIFTY", nifty_price, direction)
    if msg and is_new("nifty_trade"):
        send(msg)

    bank_dir = fno("BANKNIFTY")
    msg2 = trade_logic("BANKNIFTY", bank_price, bank_dir)
    if msg2 and is_new("bank_trade"):
        send(msg2)

# ---------- ALWAYS SEND UPDATE ----------
decision = "NEUTRAL"
if score >= 4:
    decision = "BULLISH"
elif score <= -4:
    decision = "BEARISH"

send(f"""
⏱️ MARKET UPDATE

Score: {score}
Bias: {decision}

Signals:
- {' | '.join(signals) if signals else 'No major signals'}
""")

save_last(last)