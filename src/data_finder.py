import os, json, re


ROOT = "/dnd-core/data"

def is_id(string: str) -> bool:
    return  re.match(r"^[a-zA-Z_0-9]*:(?:[a-zA-Z_0-9]*\.)+[a-zA-Z_0-9]+$", string) is not None

def find_data_by_type(namespace: str, data_type: str) -> list[dict]:
    folder = f"{ROOT}/{namespace}/{data_type}"
    id_prefix = f"{namespace}:{data_type}"
    results = []
    try:
        for root, _, files in os.walk(folder):
            for file in files:
                file_path = f"{root}/{file}"
                data_id = file_path.replace(folder, id_prefix).replace("/", ".").strip(".json")
                with open(file_path) as json_file:
                    data_name = json.load(json_file)["name"]
                results.append({"id": data_id, "name": data_name})
        return results
    except:
        raise RuntimeError(f"Error when processing {folder}.")


def find_data_by_id(data_id: str) -> dict:
    namespace, data_path = data_id.split(":")
    file_path = f'{ROOT}/{namespace}/{data_path.replace(".", "/")}'

    try:
        if not os.path.exists(file_path + ".json"):
            with open(file_path + ".md") as file:
                data = '\n'.join(file.readlines())
                return data
        
        def visit(obj):
            if isinstance(obj, list):
                processed_list = []
                for v in obj:
                    processed_list.append(visit(v))
                return processed_list
            if isinstance(obj, dict):
                processed_dict = {}
                for k, v in obj.items():
                    processed_dict[k] = visit(v)
                return processed_dict
            if is_id(str(obj)):
                return find_data_by_id(str(obj))
            else:
                return obj

        with open(file_path + ".json") as json_file:
            data: dict = json.load(json_file)
            data = visit(data)
            data["id"] = data_id
            return data
    except:
        raise RuntimeError(f"Error when load {data_id}.")
