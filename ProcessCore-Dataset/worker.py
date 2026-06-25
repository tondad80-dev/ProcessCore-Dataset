import sqlite3, time, urllib.request, json, re

DB_NAME = "processcore_v2.db"

def get_next_batch(cursor, batch_size=5):
    query = """
    SELECT url, domain FROM nodes 
    WHERE llm_summary IS NULL 
    AND domain NOT LIKE '%wiki%'
    AND domain NOT LIKE '%doi.org%'
    AND domain NOT LIKE '%archive%'
    AND domain NOT LIKE '%google%'
    AND domain NOT LIKE '%harvard.edu%'
    GROUP BY domain 
    ORDER BY score DESC, RANDOM() 
    LIMIT ?;
    """
    cursor.execute(query, (batch_size,))
    return cursor.fetchall()

def fetch_text(url):
    try:
        if not url.startswith('http'): url = 'http://' + url
        req = urllib.request.Request(url, headers={'User-Agent': 'ProcessCore_AI/2.3'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            # Novinka: Odstranění Javascriptu a CSS pro čistší "čtení"
            html = re.sub(r'<(script|style).*?>.*?</\1>', ' ', html, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', html)
            return re.sub(r'\s+', ' ', text).strip()[:2500] 
    except Exception:
        return ""

def call_llama(domain, text):
    # Novinka: Tvrdá Anti-UI instrukce
    prompt = f"System: You are an expert AI data extractor. Extract the organization name and specific scientific/domain technologies from the text. IGNORE UI elements like 'img', 'button', 'link', 'login', 'menu'. Return ONLY a valid JSON object. Example: {{\"organization_name\": \"FermiLab\", \"domain_technologies\": [\"Quantum Computing\", \"Superconductors\"]}}\n\nText:\n{text}\n\nJSON:"
    data = {"prompt": prompt, "n_predict": 300, "temperature": 0.0}
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8080/completion",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=300) as response:
            res = json.loads(response.read().decode('utf-8'))
            raw_output = res.get("content", "").strip()
            
            match = re.search(r'\{.*?\}', raw_output, re.DOTALL)
            if match:
                clean_json = match.group(0)
                try:
                    parsed = json.loads(clean_json)
                    return json.dumps(parsed)
                except json.JSONDecodeError:
                    return json.dumps({"error": "JSONDecodeError", "raw": clean_json[:50]})
            return json.dumps({"organization_name": "", "domain_technologies": [], "error": "No_JSON_Found"})
    except Exception as e:
        return json.dumps({"error": f"Llama_API_Failed: {str(e)}"})

def process_worker():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    print("🚀 Bounded Epistemic Machine: Kognitivní vrstva V2.3 (Clean Text & Anti-UI)")
    
    batch = get_next_batch(cursor, 5)
    if not batch:
        print("✅ Žádná data k analýze.")
        return

    for url, domain in batch:
        print(f"📡 Stahuji data z: {domain} ...")
        text = fetch_text(url)
        
        if len(text) < 100:
            print(f"   ⚠️ Zahozeno (Nedostatek textu/Bot-block).")
            cursor.execute("UPDATE nodes SET llm_summary = ? WHERE url = ?", ('{"error": "no_content"}', url))
        else:
            print(f"🧠 Llama 3.2 analyzuje: {domain} ...")
            llm_summary = call_llama(domain, text)
            print(f"   ✅ AI JSON: {llm_summary}")
            cursor.execute("UPDATE nodes SET llm_summary = ? WHERE url = ?", (llm_summary, url))
        
        conn.commit()
        print("❄️ Termální pauza (10s)...")
        time.sleep(10)
        
    conn.close()
    print("🔄 Dávka dokončena.")

if __name__ == "__main__":
    process_worker()
