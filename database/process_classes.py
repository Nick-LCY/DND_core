import json, os, re
import warnings
from utils import build_effect, build_feature, build_selection, get_file
from utils import id_formating, add_to_files, add_to_filled


def process_hd(hd_obj: dict, feature_categories: list[str]):
    effect_id = build_effect(["effects"], f"hit_dice@{hd_obj['faces']}")
    feature_id = build_feature(
        feature_categories, "hit_dice", "class_traits", [id_formating(effect_id, True)]
    )
    return feature_id


def process_proficiencies(
    starting: dict, proficiencies: dict, feature_categories: list[str]
):
    CATEGORY_MAPPING = {
        "armor": ["effects", "proficiencies", "armor"],
        "skills": ["effects", "proficiencies", "skills"],
        "toolProficiencies": ["effects", "proficiencies", "tools"],
        "weapons": ["effects", "proficiencies", "weapons"],
    }
    features = []
    for key, value in starting.items():
        if key == "tools":
            continue
        effects = []
        for item in value:
            if isinstance(item, str):
                if item.startswith("{"):
                    item = item.split("|")[0].split("@item")[-1].strip()
                effect_id = build_effect(CATEGORY_MAPPING[key], item)
                effects.append(id_formating(effect_id, True))
            elif isinstance(item, dict):
                if "choose" in item:
                    available = []
                    for i in item["choose"]["from"]:
                        effect_id = build_effect(CATEGORY_MAPPING[key], i)
                        available.append(id_formating(effect_id, True))
                    effects.append(build_selection(available, item["choose"]["count"]))
                else:
                    for i in item:
                        if "any" in i:
                            effects.append(build_selection([], item[i]))
                        else:
                            effect_id = build_effect(CATEGORY_MAPPING[key], i)
                            effects.append(id_formating(effect_id, True))
            else:
                warnings.warn(f"{key} doesn't processed")
        features.append(
            build_feature(feature_categories, key, "class_proficiencies", effects)
        )
    effects = []
    for proficiency in proficiencies:
        effect_id = id_formating(
            build_effect(["effects", "proficiencies", "saves"], proficiency)
        )
        effects.append(id_formating(effect_id, True))
    features.append(
        build_feature(
            feature_categories, "save_proficiencies", "class_proficiencies", effects
        )
    )
    return features


def process_equipments(equipments: list, feature_categories: list[str]):
    categories_prefix = ["effects", "starting_equipments"]
    gold_name = equipments["goldAlternative"].split("|")[1]
    gold_effect_id = build_effect(categories_prefix, f"gold_{gold_name}")

    def process_item(item: dict | str):
        if isinstance(item, dict) and "equipmentType" not in item:
            item_name = item["item"]
            item_name = item_name.split("|")[0]
            if "quantity" in item:
                item_name = f"{item_name}@{item['quantity']}"
            elif re.match(r".*\(\d+\)", item_name):
                item_name = re.sub(r"(.*)\((\d+)\)", r"\1@\2", item_name)
            else:
                item_name = f"{item_name}@1"
            effect_id = build_effect(categories_prefix, item_name)
            return id_formating(effect_id, True)
        elif isinstance(item, str):
            item_name = item.split("|")[0]
            if re.match(r".*\(\d+\)", item_name):
                item_name = re.sub(r"(.*)\((\d+)\)", r"\1@\2", item_name)
            else:
                item_name = f"{item_name}@1"
            effect_id = build_effect(categories_prefix, item_name)
            return id_formating(effect_id, True)
        else:
            available = [item["equipmentType"]]
            return build_selection(available, 1)

    equipment_groups = []
    for equipment in equipments["defaultData"]:
        group = []
        if len(equipment) == 1:
            for item in equipment["_"]:
                group.append(process_item(item))
        else:
            available = []
            for option in equipment.values():
                for item in option:
                    available.append(process_item(item))
            group = build_selection(available, 1)
        equipment_groups.append(group)
    selection = [
        build_selection([equipment_groups, id_formating(gold_effect_id, True)], 1)
    ]
    return build_feature(
        feature_categories, "starting_equipments", "class_equipments", selection
    )


def build_class(class_name: str, features: list[str], class_obj: dict):
    class_id = "classes." + class_name
    class_id = id_formating(class_id)
    data = {
        "name": "",
        "description": "",
        "features": features,
        "additional": {},
        "subclass_name": "",
        "subclasses": [],
    }
    for key in class_obj:
        if key not in [
            "hd",
            "startingProficiencies",
            "proficiency",
            "startingEquipment",
            # Useless
            "name",
            "source",
            "page",
            "srd",
            "subclassTitle",
            "hasFluff",
            "hasFluffImages",
        ]:
            data["additional"][key] = class_obj[key]
    add_to_files(class_id, data)
    add_to_filled(f"{class_id}/name")
    add_to_filled(f"{class_id}/description")
    add_to_filled(f"{class_id}/subclass_name")
    return class_id


def process_class(class_obj: dict, features: list[dict]):
    class_name = class_obj["name"]
    feature_categories = ["features", class_name]
    feature_ids = []
    feature_id = process_hd(class_obj["hd"], feature_categories)
    feature_ids.append(id_formating(feature_id, True))
    proficiencies = process_proficiencies(
        class_obj["startingProficiencies"],
        class_obj["proficiency"],
        feature_categories,
    )
    feature_ids.extend([id_formating(x, True) for x in proficiencies])
    feature_id = process_equipments(class_obj["startingEquipment"], feature_categories)
    feature_ids.append(id_formating(feature_id, True))
    for feature in features:
        feature_id = build_feature(
            ["features", class_name],
            feature["name"],
            "class_level_traits",
            [],
        )
        feature_ids.append(id_formating(feature_id, True))
    build_class(class_name, feature_ids, class_obj)


def build_subclass(
    subclass_name: str, class_name: str, features: list[str], subclass: dict
):
    subclass_id = f"subclasses.{class_name}.{subclass_name}"
    subclass_id = id_formating(subclass_id)
    data = {
        "name": "",
        "description": "",
        "features": features,
        "additional": {},
    }
    for key in subclass.keys():
        if key not in ["className", "source", "page", "name", "shortName"]:
            data["additional"][key] = subclass[key]
    add_to_files(subclass_id, data)
    add_to_filled(f"{subclass_id}/name")
    add_to_filled(f"{subclass_id}/description")
    return subclass_id


def process_subclass(subclass: dict, features: list[dict]):
    subclass_name = subclass["shortName"]
    class_name = subclass["className"]
    feature_ids = []
    min_level = 20
    for feature in features:
        min_level = min(feature["level"], min_level)
        feature_id = build_feature(
            ["features", class_name, subclass_name],
            feature["name"],
            "subclass_level_traits",
            [],
        )
        feature_ids.append(id_formating(feature_id, True))
    get_file(f"classes.{class_name}")["subclasses_available_level"] = min_level
    subclass_id = build_subclass(subclass_name, class_name, feature_ids, subclass)
    get_file(f"classes.{class_name}")["subclasses"].append(
        id_formating(subclass_id, True)
    )


def main(original_data: str):
    for filename in os.listdir(original_data):
        if not filename.startswith("class"):
            continue
        with open(f"{original_data}/{filename}") as file:
            root = json.load(file)
            class_dict = {}
            if "class" in root:
                for class_obj in root["class"]:
                    if class_obj.get("source") != "PHB":
                        continue
                    class_dict[class_obj["name"]] = {
                        "class_obj": class_obj,
                        "features": [],
                    }
                for class_feature in root["classFeature"]:
                    if class_feature["source"] != "PHB":
                        continue
                    class_dict[class_feature["className"]]["features"].append(
                        class_feature
                    )
                for entry in class_dict.values():
                    process_class(**entry)
            subclass_dict = {}
            if "subclass" in root:
                for subclass in root["subclass"]:
                    if "source" not in subclass or subclass["source"] != "PHB":
                        continue
                    subclass_dict[subclass["shortName"]] = {
                        "subclass": subclass,
                        "features": [],
                    }
                for subclass_feature in root["subclassFeature"]:
                    if subclass_feature["source"] != "PHB":
                        continue
                    subclass_dict[subclass_feature["subclassShortName"]][
                        "features"
                    ].append(subclass_feature)
                for entry in subclass_dict.values():
                    process_subclass(**entry)
