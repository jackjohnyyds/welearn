#!/usr/bin/env python3
"""每日抓取医学病例：BMJ Case Reports RSS + PubMed 最新病例报告"""
import json, re, urllib.request, os, datetime, sys

OUT = os.path.join(os.path.dirname(__file__), "..", "medical.json")

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 WeLearn/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def fetch_bmj():
    xml = fetch("https://casereports.bmj.com/rss/current.xml")
    # RSS 1.0: <item><title>..</title><link>..</link><description>..</description></item>
    items = []
    for m in re.finditer(r'<item rdf:about="([^"]+)">(.*?)</item>', xml, re.S):
        link = m.group(1).strip()
        t = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', m.group(2), re.S)
        c = re.search(r'<dc:creator><!\[CDATA\[(.*?)\]\]></dc:creator>', m.group(2), re.S)
        if t:
            title = t.group(1).strip()
            items.append({"t": title, "link": link, "desc": "BMJ Case Reports" + (" · " + c.group(1)[:40] if c else "")})
            if len(items) >= 8:
                break
    return items

def fetch_pubmed():
    ids = fetch("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=case+reports%5Bpt%5D+AND+english%5Bla%5D&retmax=6&retmode=json")
    idlist = json.loads(ids)["esearchresult"]["idlist"]
    if not idlist:
        return []
    sm = fetch(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(idlist)}&retmode=json")
    out = []
    for pmid, info in json.loads(sm)["result"].items():
        if pmid == "uids":
            continue
        out.append({"t": info.get("title", "")[:120], "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "desc": "PubMed 最新病例报告"})
    return out

def main():
    bmj = fetch_bmj()
    pm = fetch_pubmed()
    if not bmj and not pm:
        print("ERROR: 无数据", file=sys.stderr)
        sys.exit(1)
    data = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "bmj": bmj, "pubmed": pm}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"OK: BMJ {len(bmj)} 条, PubMed {len(pm)} 条 -> {OUT}")
    for a in bmj[:3]: print("- BMJ:", a["t"][:50])
    for a in pm[:3]: print("- PM:", a["t"][:50])

if __name__ == "__main__":
    main()
