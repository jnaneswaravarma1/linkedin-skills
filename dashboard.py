import json
import os
from datetime import datetime

LOG_FILE = "logs.json"

def load_logs():
    if not os.path.exists(LOG_FILE):
        return {"keys": {}, "runs": []}
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def print_separator(char="=", length=80):
    print(char * length)

def print_dashboard():
    logs = load_logs()

    print_separator()
    print("LINKEDIN SKILLS — DASHBOARD")
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()

    # API Keys section
    print("\n📌 API KEYS STATUS")
    print_separator("-")
    print(f"{'KEY NAME':<25} {'STATUS':<12} {'LAST UPDATED':<25} {'NOTE'}")
    print_separator("-")

    keys = logs.get("keys", {})
    if not keys:
        print("No keys logged yet. Run run.py or auto_reply.py first.")
    else:
        for key_name, key_data in keys.items():
            status = "✅ Connected" if key_data.get("connected") else "❌ Missing"
            updated = key_data.get("last_updated", "Never")
            note = key_data.get("note", "")
            print(f"{key_name:<25} {status:<12} {updated:<25} {note}")

    # Runs section
    print("\n\n📊 RUN HISTORY")
    print_separator("-")
    print(f"{'#':<4} {'DATE':<12} {'TIME':<10} {'TYPE':<15} {'TOPIC/URN':<35} {'STATUS':<12} {'PUBLISHED AT'}")
    print_separator("-")

    runs = logs.get("runs", [])
    if not runs:
        print("No runs logged yet.")
    else:
        for i, run in enumerate(reversed(runs[-20:]), 1):
            run_type = run.get("type", "unknown")
            date = run.get("date", "")
            time_val = run.get("time", "")
            topic = run.get("topic", run.get("post_urn", ""))[:33]
            status = "✅ Success" if run.get("success") else "❌ Failed"
            published_at = run.get("published_at", "-")
            print(f"{i:<4} {date:<12} {time_val:<10} {run_type:<15} {topic:<35} {status:<12} {published_at}")

    print_separator()
    print(f"Total runs: {len(runs)}")
    print_separator()

if __name__ == "__main__":
    print_dashboard()