import os, json

TARGET_DIR = "data"
CURRENT_DIR = "gen_data"


def file_merge():
    ignored = 0
    appended = 0
    for root, _, files in os.walk(CURRENT_DIR):
        for file in files:
            relative_dir = root[len(CURRENT_DIR) :].strip("/")
            relative_path = f"{relative_dir}/{file}"
            if os.path.exists(f"{TARGET_DIR}/{relative_path}"):
                ignored += 1
                continue
            os.system(f"mkdir -p {TARGET_DIR}/{relative_dir}")
            os.system(f"cp {CURRENT_DIR}/{relative_path} {TARGET_DIR}/{relative_path}")
            appended += 1

    print(f"Ignored: {ignored}")
    print(f"Appended: {appended}")

def translation_merge():
    with open(f"{TARGET_DIR}/_dnd5e/zh_CN.json", encoding="utf8") as file:
        old_file = json.load(file)
    with open(f"{CURRENT_DIR}/_dnd5e/zh_CN.json", encoding="utf8") as file:
        new_file = json.load(file)
    
    new_file.update(old_file)
    with open(f"{TARGET_DIR}/_dnd5e/zh_CN.json", "w", encoding="utf8") as file:
        json.dump(new_file, file, ensure_ascii=False)

file_merge()
translation_merge()