import sqlite3
import json

DB_NAME = "processcore_v2.db"
EXPORT_FILE = "knowledge_graph.json"

def export_graph_state():
    print("📥 ProcessCore_NET: Generuji Graph State Export...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Extrakce validních uzlů (pouze ty, co Llama úspěšně zpracovala)
    print("🔍 Hledám obohacené uzly...")
    nodes_raw = cursor.execute("""
        SELECT url, domain, llm_summary 
        FROM nodes 
        WHERE llm_summary IS NOT NULL 
        AND llm_summary NOT LIKE '%error%'
    """).fetchall()

    graph = {
        "nodes": [],
        "edges": []
    }

    valid_urls = set()

    for url, domain, summary in nodes_raw:
        try:
            data = json.loads(summary)
            org_name = data.get("organization_name", domain)
            techs = data.get("domain_technologies", [])
            
            # Přidáme uzel do grafu
            graph["nodes"].append({
                "id": url,
                "label": org_name if org_name else domain,
                "domain": domain,
                "technologies": techs
            })
            valid_urls.add(url)
        except json.JSONDecodeError:
            continue

    print(f"✅ Nalezeno {len(graph['nodes'])} sémanticky bohatých uzlů.")

    # 2. Extrakce existujících vazeb (edges) mezi těmito uzly
    print("🔗 Rekonstruuji vazby (Edges)...")
    edges_raw = cursor.execute("SELECT source, target FROM edges").fetchall()
    
    edge_count = 0
    for source, target in edges_raw:
        # Exportujeme jen ty hrany, kde známe alespoň zdrojový uzel
        if source in valid_urls:
            graph["edges"].append({
                "source": source,
                "target": target
            })
            edge_count += 1

    print(f"✅ Přidáno {edge_count} relevantních vazeb.")

    # 3. Uložení Graph Payloadu
    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    conn.close()
    print(f"🚀 HOTOVO! Knowledge Graph exportován do souboru: {EXPORT_FILE}")

if __name__ == "__main__":
    export_graph_state()
