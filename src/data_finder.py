import os, json, re


ROOT = "/dnd-core/data"


def is_id(string: str) -> bool:
    return (
        re.match(r"^[a-zA-Z_0-9]*:(?:[a-zA-Z_0-9#]*\.)+[a-zA-Z_0-9#]+$", string)
        is not None
    )


def format_str(data_id: str, data_key: str | None, data_name: str, lang_code: str) -> str:
    namespace = data_id.split(":")[0]
    file_id = data_id.split(":")[1]
    if data_name == "":
        if data_key is None:
            return data_name
        data_name = f"%{file_id}/{data_key}%"
    if re.match(r"^\%.*\%$", data_name) is None:
        return data_name
    with open(f"{ROOT}/{namespace}/{lang_code}.json", "r") as file:
        value = json.load(file).get(data_name.strip("%"), data_name)
    if isinstance(value, list):
        value = "\n".join(value)
    return value


def find_data_by_type(
    namespace: str, data_type: str, lang_code: str = "zh_CN"
) -> list[dict]:
    folder = f"{ROOT}/{namespace}/{data_type}"
    id_prefix = f"{namespace}:{data_type}"
    results = []
    try:
        for root, _, files in os.walk(folder):
            for file in files:
                file_path = f"{root}/{file}"
                data_id = (
                    file_path.replace(folder, id_prefix)
                    .replace("/", ".")
                    .replace(".json", "")
                )
                with open(file_path) as json_file:
                    data_name = json.load(json_file)["name"]
                results.append(
                    {"id": data_id, "name": format_str(data_id, "name", data_name, lang_code)}
                )
        return results
    except:
        raise RuntimeError(f"Error when processing {folder}.")


def find_data_by_id(data_id: str, lang_code: str = "zh_CN") -> dict:
    namespace, data_path = data_id.split(":")
    file_path = f'{ROOT}/{namespace}/{data_path.replace(".", "/")}'

    try:
        if not os.path.exists(file_path + ".json"):
            with open(file_path + ".md") as file:
                data = "\n".join(file.readlines())
                return data

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
            if is_id(str(val)):
                return find_data_by_id(str(val))
            if isinstance(val, str):
                return format_str(data_id, key, val, lang_code)
            else:
                return val

        with open(file_path + ".json") as json_file:
            data: dict = json.load(json_file)
            data = visit(data, None)
            data["id"] = data_id
            return data
    except:
        raise RuntimeError(f"Error when load {data_id}.")
