import re, os, json

FILES = {}
TO_FILLED = {}
NAMESPACE = "_dnd5e"


def add_to_files(file_id: str, data: dict):
    if file_id is None:
        pass
    file_id = re.sub(r"@.*$", "", file_id)
    if file_id in FILES:
        pass
        # warnings.warn(f"{file_id} repeated")
    FILES[file_id] = data


def add_to_filled(key: str, content: str = ""):
    key = re.sub(r"@.*/", "", key)
    TO_FILLED[key] = content


def id_formating(original_id: str, namespaced: bool = False) -> str:
    processed = re.sub(r"(?:'s|\(|\)|s')", "_", original_id)
    processed = re.sub(r"(?:\s|_|-)+", "_", processed)
    processed = re.sub(r"_+@", "@", processed)
    processed = processed.replace("\u00d7", "times")
    if namespaced:
        processed = f"{NAMESPACE}:{processed}"
    return processed.lower()


def build_effect(file_categories: list[str], en_name: str):
    effect_id = f"{'.'.join(file_categories)}.{en_name}"
    effect_id = id_formating(effect_id)
    data = {"name": "", "description": "", "expressions": []}
    add_to_files(effect_id, data)
    add_to_filled(f"{effect_id}/name")
    add_to_filled(f"{effect_id}/description")
    return effect_id


def build_selection(available: list[str], choose: int):
    selection = {"choose": choose, "available": []}
    for item in available:
        if isinstance(item, str):
            selection["available"] += [f"{NAMESPACE}:{item}"]
        else:
            selection["available"] += [item]
    return selection


def build_feature(
    file_categories: list[str], en_name: str, category: str, effects: list[str]
):
    feature_id = f"{'.'.join(file_categories)}.{en_name}"
    feature_id = id_formating(feature_id)
    data = {
        "name": f"",
        "description": f"",
        "category": category,
        "effects": [],
    }
    if len(effects) == 1 and not isinstance(effects[0], str):
        data["effects"] = effects[0]
    else:
        for effect in effects:
            if isinstance(effect, str):
                data["effects"].append(f"{NAMESPACE}:{effect}")
            else:
                data["effects"].append(effect)
    add_to_files(feature_id, data)
    add_to_filled(f"{feature_id}/name")
    add_to_filled(f"{feature_id}/description")
    return feature_id

def get_file(id):
    return FILES[id_formating(id)]

def save(root):
    os.system(f"rm -rf {root}")
    for path in FILES:
        dirs = path.split(".")[:-1]
        file = path.split(".")[-1] + ".json"
        os.system(f"mkdir -p {root}/{'/'.join(dirs)}")
        with open(f"{root}/{'/'.join(dirs)}/{file}", "w") as file:
            json.dump(FILES[path], file)
    with open(f"{root}/en_US.json", "w") as file:
        json.dump(TO_FILLED, file)