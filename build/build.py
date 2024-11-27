import json, os, re


def is_id(string: str) -> bool:
    return (
        re.match(
            r"^[a-zA-Z_0-9]*:(?:[a-zA-Z_0-9]*\.)+[a-zA-Z_0-9]+@*(?:[^,]+,{0,1})*$",
            string,
        )
        is not None
    )


def find_data_by_id(data_id: str, lang_code: str = "zh_CN") -> dict:
    data_params = None
    if len(data_id.split("@")) > 1:
        data_id, data_params = data_id.split("@")
    # TODO: NS之后怎么结合进来？
    _, data_path = data_id.split(":")
    file_path = f'{ROOT}/{data_path.replace(".", "/")}'

    try:

        def visit(val, key: str | None):
            if isinstance(val, list):
                processed_list = []
                for v in val:
                    processed_list.append(visit(v, None))
                return processed_list
            if isinstance(val, dict):
                processed_dict = {}
                for k, v in val.items():
                    processed_dict[k] = visit(v, k)
                return processed_dict
            if isinstance(val, str):
                val = format_str(data_id, key, val, lang_code, data_params)
            if is_id(str(val)):
                return find_data_by_id(str(val))
            else:
                return val

        with open(file_path + ".json") as json_file:
            data: dict = json.load(json_file)
            data = visit(data, None)
            data["id"] = data_id
            return data
    except:
        raise RuntimeError(f"Error when load {data_id}.")


def format_str(
    data_id: str,
    data_key: str | None,
    data_name: str,
    lang_code: str,
    data_params: str | None = None,
) -> str:
    file_id = data_id.split(":")[1]
    if data_name == "":
        if data_key is None:
            return data_name
        data_name = f"%{file_id}/{data_key}%"
    if re.match(r"^\%.*\%$", data_name) is None:
        if data_params is not None:
            return data_name.format(*data_params.split(","))
        else:
            return data_name
    with open(f"{ROOT}/{lang_code}.json", "r") as file:
        value = json.load(file).get(data_name.strip("%"), data_name)
    if isinstance(value, list):
        value = "\n".join(value)
    if data_params is not None:
        value = value.format(*data_params.split(","))
    return value


def find_name(file_path: str):
    data_id = (
        file_path.replace(f"{ROOT}/", f"{NAMESPACE}:")
        .replace("/", ".")
        .replace(".json", "")
    )
    try:
        with open(file_path) as file:
            data_name = json.load(file)["name"]
        return format_str(data_id, "name", data_name, LANG)
    except:
        return ""


ROOT = "data/_dnd5e"
NAMESPACE = "_dnd5e"
OUTPUT = "output"
LANG = "zh_CN"
if __name__ == "__main__":
    os.system(f"rm -rf {OUTPUT}/{NAMESPACE}")
    os.system(f"mkdir -p {OUTPUT}/{NAMESPACE}")
    for folder in ["classes", "races", "backgrounds"]:
        for root, _, filenames in os.walk(f"{ROOT}/{folder}"):
            for filename in filenames:
                path = f"{root}/{filename}"
                print(path)
                file_id = ".".join(path[:-5].split("/")[2:])
                data = find_data_by_id(f"{NAMESPACE}:{file_id}", LANG)
                with open(f"{OUTPUT}/{NAMESPACE}/{file_id}.json", "w") as file:
                    json.dump(data, file, ensure_ascii=False)

    index = {"files": [], "dirs": {}}
    for root, dirs, files in os.walk(ROOT):
        paths = root.replace(ROOT, "").strip("/")
        target = index
        for path in paths.split("/"):
            if path != "":
                target = target["dirs"][path]
        for dir in dirs:
            target["dirs"][dir] = {"files": [], "dirs": {}}
        files = sorted(files)
        for file in files:
            file_path = f"{root}/{file}"
            print(file_path)
            file_id = (
                file_path.replace(f"{ROOT}/", f"{NAMESPACE}:")
                .replace("/", ".")
                .replace(".json", "")
            )
            file_obj = {"id": file_id, "name": find_name(f"{root}/{file}")}
            target["files"].append(file_obj)

    with open(f"{OUTPUT}/{NAMESPACE}/index.json", "w") as file:
        json.dump(index, file, ensure_ascii=False)
