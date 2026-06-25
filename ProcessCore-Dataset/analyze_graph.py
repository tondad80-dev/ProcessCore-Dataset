import json
from collections import Counter

print("📊 Analyzuji Knowledge Graph...")
with open("knowledge_graph.json", "r", encoding="utf-8") as f:
    graph = json.load(f)

tech_counter = Counter()
for node in graph["nodes"]:
    techs = node.get("technologies", [])
    if isinstance(techs, list):
        for tech in techs:
            # Rychlé čištění textu
            clean_tech = str(tech).strip().title()
            if len(clean_tech) > 2 and clean_tech.lower() not in ["none", "null", "unknown", "n/a"]:
                tech_counter[clean_tech] += 1

print("\n🏆 TOP 15 NEJČASTĚJŠÍCH TECHNOLOGIÍ V GRAFU:")
print("-" * 40)
for tech, count in tech_counter.most_common(15):
    print(f"🔹 {tech} (výskyt: {count}x)")
