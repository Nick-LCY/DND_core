import json
import os
from src.data_finder import find_data_by_id

ROOT = "data/_dnd5e"
NAMESPACE = "_dnd5e"
OUTPUT = "output"
LANG = "zh_CN"
os.system(f"rm -rf {OUTPUT}/{NAMESPACE}")
os.system(f"mkdir -p {OUTPUT}/{NAMESPACE}")
for folder in ["classes", "races", "backgrounds"]:
    for root, _, filenames in os.walk(f"{ROOT}/{folder}"):
        for filename in filenames:
            path = f"{root}/{filename}"
            file_id = ".".join(path[:-5].split("/")[2:])
            data = find_data_by_id(f"{NAMESPACE}:{file_id}", LANG)
            with open(f"{OUTPUT}/{NAMESPACE}/{file_id}.json", "w") as file:
                json.dump(data, file, ensure_ascii=False)
