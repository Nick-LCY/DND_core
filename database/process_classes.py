import json, os, re
import warnings
from utils import build_effect, build_feature, build_selection, save, get_file
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
                        available.append(build_effect(CATEGORY_MAPPING[key], i))
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
        effect_id = id_formating(build_effect(["effects", "proficiencies", "saves"], proficiency))
        effects.append(id_formating(effect_id, True))
    features.append(
        build_feature(
            feature_categories, "save_proficiencies", "class_proficiencies", effects
        )
    )
    return features


def process_equipments(
    equipments: list, feature_categories: list[str], class_name: str
):
    categories_prefix = ["effects", "starting_equipments"]
    gold_name = equipments["goldAlternative"].split("|")[1]
    gold_effect_id = build_effect(categories_prefix, gold_name)
    effects = [id_formating(gold_effect_id, True)]

    def process_item(item: dict | str):
        if isinstance(item, dict) and "equipmentType" not in item:
            item_name = item["item"]
            item_name = item_name.split("|")[0]
            if "quantity" in item:
                item_name = f"{item_name}@{item['quantity']}"
            item_name = re.sub(r"(.*)\((\d+)\)", r"\1@\2", item_name)
            effect_id = build_effect(categories_prefix + [class_name], item_name)
            return id_formating(effect_id, True)
        elif isinstance(item, str):
            item_name = item.split("|")[0]
            item_name = re.sub(r"(.*)\((\d+)\)", r"\1@\2", item_name)
            effect_id = build_effect(categories_prefix + [class_name], item_name)
            return id_formating(effect_id, True)
        else:
            available = [item["equipmentType"]]
            return build_selection(available, 1)

    for equipment in equipments["defaultData"]:
        if len(equipment) == 1:
            for item in equipment["_"]:
                effects.append(process_item(item))
        else:
            for option in equipment.values():
                available = []
                for item in option:
                    available.append(process_item(item))
                effects.append(build_selection(available, 1))
        selection = [build_selection(effects, 1)]
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


def process_class(class_obj: dict):
    class_name = class_obj["name"]
    feature_categories = ["features", class_name]
    features = []
    feature_id = process_hd(class_obj["hd"], feature_categories)
    features.append(id_formating(feature_id, True))
    feature_ids = process_proficiencies(
        class_obj["startingProficiencies"],
        class_obj["proficiency"],
        feature_categories,
    )
    features.extend([id_formating(x, True) for x in feature_ids])
    feature_id = process_equipments(
        class_obj["startingEquipment"], feature_categories, class_name
    )
    features.append(id_formating(feature_id, True))
    build_class(class_name, features, class_obj)


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
            "subclass_traits",
            [],
        )
        feature_ids.append(id_formating(feature_id, True))
    get_file(f"classes.{class_name}")["subclasses_available_level"] = min_level
    subclass_id = build_subclass(subclass_name, class_name, features, subclass)
    get_file(f"classes.{class_name}")["subclasses"].append(
        id_formating(subclass_id, True)
    )


def main(original_data: str):
    for filename in os.listdir(original_data):
        if not filename.startswith("class"):
            continue
        with open(f"{original_data}/{filename}") as file:
            root = json.load(file)
            if "class" in root:
                if root["class"][0]["source"] == "PHB":
                    class_obj = root["class"][0]
                    # {'subclassTitle', 'classFeatures', 'multiclassing'}
                    # hd, startingProficiencies, proficiency, startingEquipment
                    process_class(class_obj)
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


main("5etools/data/class")
save("classes_data/_dnd5e")
