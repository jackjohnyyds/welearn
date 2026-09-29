#!/usr/bin/env python3
"""每日抓取 englio.ai/explore 文章列表，生成 articles.json（含中文标题翻译）"""
import json, re, urllib.request, urllib.parse, os, datetime, sys
import html as htmlmod

EXPLORE_URL = "https://englio.ai/explore"
OUT = os.path.join(os.path.dirname(__file__), "..", "articles.json")

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def translate(title):
    """MyMemory 免费翻译 en->zh-CN"""
    try:
        q = urllib.parse.quote(title[:480])
        url = f"https://api.mymemory.translated.net/get?q={q}&langpair=en|zh-CN"
        with urllib.request.urlopen(url, timeout=15) as r:
            d = json.loads(r.read().decode())
            return d.get("responseData", {}).get("translatedText", "").strip()
    except Exception:
        return ""

def parse_articles(html):
    # 匹配 <a href="/article/uuid..."> ... 标题 ... </a> 卡片
    items = []
    # 文章卡片：a[href^="/article/"] 内第一个标题行
    pat = re.compile(r'<a[^>]*href="(/article/[a-f0-9\-]+)"[^>]*>(.*?)</a>', re.S)
    seen = set()
    for m in pat.finditer(html):
        href, inner = m.group(1), m.group(2)
        # 提取标题：去掉标签，取第一行非空
        text = re.sub(r'<[^>]+>', ' ', inner)
        text = re.sub(r'\s+', ' ', text).strip()
        text = htmlmod.unescape(text).split('☆')[0].split('★')[0].strip()
        if len(text) < 10 or len(text) > 180:
            continue
        # 分类/难度：卡片通常有 span 标签，取卡片外层
        card = m.group(0)
        cats = re.findall(r'>\s*(经济|政治|社会|科技|娱乐|文化|教育|健康|体育|环境|生活|其他)\s*<', card)
        lv = re.findall(r'>(A2|B1|B2|C1)\s*<', card)
        if text in seen:
            continue
        seen.add(text)
        items.append({
            "t": text,
            "cat": cats[0] if cats else "",
            "src": "englio·" + (lv[0] if lv else ""),
            "link": "https://englio.ai" + href
        })
        if len(items) >= 16:
            break
    return items

def main():
    html = fetch(EXPLORE_URL)
    arts = parse_articles(html)
    if not arts:
        print("ERROR: 未解析到文章", file=sys.stderr)
        sys.exit(1)
    # 翻译标题（限12条，避免超时）
    out = []
    for a in arts[:12]:
        a["zh"] = translate(a["t"])
        out.append(a)
    data = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "items": out}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"OK: {len(out)} 篇文章 -> {OUT}")
    for a in out[:5]:
        print("-", a["t"][:50], "|", a["zh"][:30], "|", a["cat"])

if __name__ == "__main__":
    main()
