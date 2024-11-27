import os, json, re


ROOT = "data"
OUTPUT_ROOT = "output"


def is_id(string: str) -> bool:
    return (
        re.match(
            r"^[a-zA-Z_0-9]*:(?:[a-zA-Z_0-9]*\.)+[a-zA-Z_0-9]+@*(?:[^,]+,{0,1})*$",
            string,
        )
        is not None
    )


def format_str(
    data_id: str,
    data_key: str | None,
    data_name: str,
    lang_code: str,
    data_params: str | None = None,
) -> str:
    namespace = data_id.split(":")[0]
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
    with open(f"{ROOT}/{namespace}/{lang_code}.json", "r") as file:
        value = json.load(file).get(data_name.strip("%"), data_name)
    if isinstance(value, list):
        value = "\n".join(value)
    if data_params is not None:
        value = value.format(*data_params.split(","))
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
                    {
                        "id": data_id,
                        "name": format_str(data_id, "name", data_name, lang_code),
                    }
                )
        return results
    except:
        raise RuntimeError(f"Error when processing {folder}.")


def find_data_by_id(data_id: str, lang_code: str = "zh_CN") -> dict:
    data_params = None
    if len(data_id.split("@")) > 1:
        data_id, data_params = data_id.split("@")
    namespace, data_path = data_id.split(":")
    if os.path.exists(f"{OUTPUT_ROOT}/{namespace}/{data_path}.json"):
        with open(f"{OUTPUT_ROOT}/{namespace}/{data_path}.json") as file:
            return json.load(file)
    file_path = f'{ROOT}/{namespace}/{data_path.replace(".", "/")}'

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
