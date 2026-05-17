import json
import os

PROGRESS_FILE = "search_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"query_index": 0, "page": 1}

def save_progress(query_index, page):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"query_index": query_index, "page": page}, f)
