import os
import json
import urllib.request

DRUID_URL = "http://localhost:8082/druid/v2/sql"
BASE_DIR = "scripts/sql/stakeholders"

results = {}

for root, dirs, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".sql"):
            filepath = os.path.join(root, file)
            with open(filepath, "r") as f:
                query = f.read()
            
            payload = json.dumps({"query": query}).encode('utf-8')
            req = urllib.request.Request(DRUID_URL, data=payload, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    results[file] = {"status": "success", "row_count": len(res_data), "sample": res_data[:2]}
            except Exception as e:
                try:
                    err_msg = e.read().decode('utf-8')
                except:
                    err_msg = str(e)
                results[file] = {"status": "error", "error": err_msg}

with open("query_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Queries executadas. Resultados salvos em query_results.json")
