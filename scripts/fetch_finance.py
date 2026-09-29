#!/usr/bin/env python3
"""每日抓取金融数据：新浪财经国内资讯 + 腾讯ETF实时涨幅排行"""
import json, re, urllib.request, os, datetime, sys

OUT = os.path.join(os.path.dirname(__file__), "..", "finance.json")
EM_API = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_104_ajaxResult_50_1_.html"
ETF_CODES = ["sh510300","sh510500","sh510050","sz159915","sh512880","sh512760","sh515790",
             "sh512010","sh515700","sh588000","sh512690","sh512480","sz159920","sh518880","sh513100",
             "sh512170","sh510880","sh516970","sh512980","sz159949","sh515030","sh512400","sz159915"]
UA = {"User-Agent": "Mozilla/5.0 WeLearn/1.0"}

def fetch(url, timeout=20, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def fetch_news():
    t = fetch(EM_API).decode()
    d = json.loads(t[t.index('{'):])
    news = []
    for it in d.get("LivesList", []):
        title = it.get("title", "").strip()
        url = it.get("url_w", "") or it.get("url_m", "")
        if not title or not url:
            continue
        news.append({"t": title, "link": url})
        if len(news) >= 15:
            break
    return news

def fetch_etf():
    url = "https://qt.gtimg.cn/q=" + ",".join(ETF_CODES)
    raw = fetch(url).decode("gbk", "ignore")
    etfs = []
    for line in raw.split(";"):
        m = re.match(r'v_(\w+)="(.*)"', line.strip())
        if not m:
            continue
        parts = m.group(2).split("~")
        if len(parts) < 33:
            continue
        name = parts[1]
        try:
            chg = float(parts[32])
            price = parts[3]
        except (ValueError, IndexError):
            continue
        etfs.append({"n": name, "p": price, "c": chg})
    etfs.sort(key=lambda x: x["c"], reverse=True)
    return etfs[:10]

def main():
    news = fetch_news()
    etf = fetch_etf()
    if not news or not etf:
        print("ERROR: 数据为空 news=%d etf=%d" % (len(news), len(etf)), file=sys.stderr)
        sys.exit(1)
    data = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "news": news, "etf": etf}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"OK: 资讯 {len(news)} 条, ETF {len(etf)} 只 -> {OUT}")
    for a in news[:3]: print("- N:", a["t"][:40])
    for a in etf[:3]: print("- E:", a["n"], a["c"], "%")

if __name__ == "__main__":
    main()
