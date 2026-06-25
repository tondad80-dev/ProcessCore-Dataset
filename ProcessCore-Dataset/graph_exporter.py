import sqlite3
import json
import uuid
import datetime

DB_NAME = "processcore_v2.db"
EXPORT_FILE = "dataset_commercial_v1.json"

def clean_taxonomy(tech_list):
    cleaned = []
    if isinstance(tech_list, list):
        for tech in tech_list:
            t = str(tech).strip().title()
            if len(t) > 2 and t.lower() not in ["none", "null", "unknown", "n/a", "error"]:
                cleaned.append(t)
    return list(set(cleaned))

def export_commercial_dataset():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    nodes_raw = cursor.execute("""
        SELECT url, domain, llm_summary 
        FROM nodes 
        WHERE llm_summary IS NOT NULL 
        AND llm_summary NOT LIKE '%error%'
    """).fetchall()

    dataset = {
        "metadata": {
            "dataset_id": str(uuid.uuid4()),
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "schema": "ProcessCore_Commercial_V1",
            "total_nodes": 0,
            "total_edges": 0
        },
        "data": {
            "entities": [],
            "relations": []
        }
    }
    
    valid_urls = set()
    url_to_uuid = {}

    for url, domain, summary in nodes_raw:
        try:
            data = json.loads(summary)
            if data.get("status") in ["ignored", "system_ignored"]:
                continue

            techs = clean_taxonomy(data.get("domain_technologies", []))
            if not techs:
                continue

            entity_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
            org_name = data.get("organization_name", domain)
            
            entity = {
                "entity_id": entity_id,
                "label": org_name,
                "domain": domain,
                "source_url": url,
                "extracted_technologies": techs,
                "confidence_score": 0.95
            }
            
            dataset["data"]["entities"].append(entity)
            valid_urls.add(url)
            url_to_uuid[url] = entity_id

        except json.JSONDecodeError:
            continue

    edges_raw = cursor.execute("SELECT source, target FROM edges").fetchall()
    
    for source, target in edges_raw:
        if source in valid_urls and target in valid_urls:
            relation = {
                "relation_id": str(uuid.uuid4()),
                "source_id": url_to_uuid[source],
                "target_id": url_to_uuid[target],
                "relation_type": "HYPERLINK"
            }
            dataset["data"]["relations"].append(relation)

    dataset["metadata"]["total_nodes"] = len(dataset["data"]["entities"])
    dataset["metadata"]["total_edges"] = len(dataset["data"]["relations"])

    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    conn.close()

if __name__ == "__main__":
    export_commercial_dataset()
