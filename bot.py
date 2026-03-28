
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

# ---------- GLOBAL ----------
score = 0
signals = []
found_news = False

POSITIVE = ["order","wins","contract","agreement","acquire","acquisition",
            "stake","buy","investment","merger"]

NEGATIVE = ["sell","loss","decline","fraud","penalty",
            "resign","default","downgrade"]

# ---------- PROCESS NEWS ----------
def process_news(title):
    global score, signals, found_news

    clean = title.lower().strip()
    if len(clean) < 20:
        return

    stock = clean.split()[0].upper()

    impact = "NEUTRAL"
    if any(k in clean for k in POSITIVE):
        impact = "BULLISH"
    elif any(k in clean for k in NEGATIVE):
        impact = "BEARISH"

    key = f"{stock}_{impact}"

    if impact != "NEUTRAL" and is_new(key):
        emoji = "🟢" if impact == "BULLISH" else "🔴"

        send(f"""{emoji} NEWS ({impact})

Stock: {stock}

News:
{title}
""")

        score += 2
        signals.append(f"News {impact}")
        found_news = True

# ---------- TRENDLYNE ----------
try:
    r = requests.get("https://trendlyne.com/latest-news/", headers=headers)
    html = r.text
    matches = re.findall(r'>([^<>]{20,120})</a>', html)

    for title in matches[:20]:
        process_news(title)
except:
    pass

# ---------- MONEYCONTROL ----------
try:
    r = requests.get("https://www.moneycontrol.com/news/business/stocks/", headers=headers)
    html = r.text
    matches = re.findall(r'<h2.*?>(.*?)</h2>', html)

    for title in matches[:10]:
        process_news(title)
except:
    pass

# ---------- ECONOMIC TIMES ----------
try:
    r = requests.get("https://economictimes.indiatimes.com/markets/stocks/news", headers=headers)
    html = r.text
    matches = re.findall(r'<a[^>]*>([^<>]{20,120})</a>', html)

    for title in matches[:15]:
        process_news(title)
except:
    pass

# ---------- NO NEWS ----------
if not found_news:
    send("ℹ️ No high-impact news from sources")

# ---------- NSE ----------
try:
    r = session.get("https://www.nseindia.com/api/corporate-announcements?index=equities", headers=headers)
    item = r.json()["data"][0]

    if is_new(item["headline"]):
        send(f"🟢 NSE\n{item['symbol']}\n{item['headline']}")
        score += 2
        signals.append("NSE")
except:
    pass

# ---------- BSE ----------
try:
    r = requests.get("https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?strCat=-1", headers=headers)
    item = r.json()["Table"][0]

    if is_new(item["HEADLINE"]):
        send(f"🔵 BSE\n{item['SCRIPNAME']}\n{item['HEADLINE']}")
        score += 2
        signals.append("BSE")
except:
    pass

# ---------- MARKET MOVERS ----------
try:
    r = session.get("https://www.nseindia.com/api/live-analysis-variations?index=gainers", headers=headers)
    for s in r.json()["data"][:5]:
        if float(s["pChange"]) > 2 and is_new(s["symbol"]+"_g"):
            send(f"🟢 GAINER {s['symbol']} ↑ {s['pChange']}%")
            score += 2
            signals.append("Gainers")
            break
except: pass

try:
    r = session.get("https://www.nseindia.com/api/live-analysis-variations?index=losers", headers=headers)
    for s in r.json()["data"][:5]:
        if float(s["pChange"]) < -2 and is_new(s["symbol"]+"_l"):
            send(f"🔴 LOSER {s['symbol']} ↓ {s['pChange']}%")
            score -= 2
            signals.append("Losers")
            break
except: pass

# ---------- F&O ----------
def fno(symbol):
    try:
        r = session.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}", headers=headers)
        data = r.json()

        ce = pe = 0
        for i in data["records"]["data"]:
            if "CE" in i and "PE" in i:
                ce = max(ce, i["CE"]["openInterest"])
                pe = max(pe, i["PE"]["openInterest"])

        return "bullish" if pe > ce else "bearish"
    except:
        return "neutral"

direction = fno("NIFTY")

if direction == "bullish":
    score += 3
elif direction == "bearish":
    score -= 3

# ---------- PRICE ----------
def price(sym):
    try:
        r = session.get(f"https://www.nseindia.com/api/quote-derivative?symbol={sym}", headers=headers)
        return r.json()["underlyingValue"]
    except:
        return None

nifty = price("NIFTY")
bank = price("BANKNIFTY")

# ---------- BREAKOUT DETECTION ----------
def breakout(symbol):
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        r = session.get(url, headers=headers)
        data = r.json()

        high = data["priceInfo"]["intraDayHighLow"]["max"]
        low = data["priceInfo"]["intraDayHighLow"]["min"]
        last = data["priceInfo"]["lastPrice"]

        if last >= high * 0.995:
            return "bullish"
        elif last <= low * 1.005:
            return "bearish"
        else:
            return "none"

    except:
        return "none"


# ---- NIFTY BREAKOUT ----
b = breakout("NIFTY")

if b == "bullish":
    if is_new("nifty_breakout_up"):
        send("🚀 NIFTY BREAKOUT ↑ → Possible CE Buy")
        score += 2
        signals.append("Breakout bullish")

elif b == "bearish":
    if is_new("nifty_breakout_down"):
        send("🔻 NIFTY BREAKDOWN ↓ → Possible PE Buy")
        score -= 2
        signals.append("Breakout bearish")

# ---------- TRADE ----------
def trade(name, p, d):
    if not p: return None
    strike = round(p/50)*50 if name=="NIFTY" else round(p/100)*100
    opt = f"{strike} CE" if d=="bullish" else f"{strike} PE"
    return f"{name} → {opt} | Entry:{round(p,2)} SL:{round(p*0.995,2)} Target:{round(p*1.01,2)}"

if score >= 4:
    t = trade("NIFTY", nifty, direction)
    if t and is_new("nifty"): send("📊 "+t)

# ---------- UPDATE ----------
bias = "NEUTRAL"
if score >= 4: bias="BULLISH"
elif score <= -4: bias="BEARISH"

send(f"⏱️ UPDATE\nScore:{score}\nBias:{bias}\nSignals:{signals}")

save_last(last)