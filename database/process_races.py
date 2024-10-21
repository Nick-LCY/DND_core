import json, os, warnings, re
from typing import Any

TO_FILLED: dict[str, str] = {}
FILES: dict[str, dict] = {}
NAMESPACE = "_dnd5e"
PROCESSED_KEYS = [
    "speed",
    "size",
    "darkvision",
    "ability",
    "resist",
    "languageProficiencies",
    "toolProficiencies",
    "skillProficiencies",
    "weaponProficiencies",
    "armorProficiencies",
    "entries",
    "name",
    "raceName",
    "source",
    "raceSource",
]


def id_formating(original_id: str) -> str:
    processed = re.sub(r"(?:'s|\(|\))", "", original_id)
    processed = re.sub(r"(?:\s|_|-)+", "_", processed)
    return processed.lower()


def add_to_files(file_id: str, data: dict):
    if file_id is None:
        pass
    if file_id in FILES:
        warnings.warn(f"{file_id} repeated")
    FILES[file_id] = data


def build_effect(file_categories: list[str], en_name: str):
    effect_id = f"{'.'.join(file_categories)}.{en_name}"
    effect_id = id_formating(effect_id)
    data = {
        "name": f"%{NAMESPACE}:{effect_id}/name%",
        "description": f"%{NAMESPACE}:{effect_id}/description%",
        "expressions": [],
    }
    add_to_files(effect_id, data)
    TO_FILLED[f"{effect_id}/name"] = ""
    TO_FILLED[f"{effect_id}/description"] = ""
    return effect_id


def build_feature(
    file_categories: list[str], en_name: str, category: str, effect_ids: list[str]
):
    feature_id = f"{'.'.join(file_categories)}.{en_name}"
    feature_id = id_formating(feature_id)
    data = {
        "name": f"%{NAMESPACE}:{feature_id}/name%",
        "description": f"%{NAMESPACE}:{feature_id}/description%",
        "category": category,
        "effects": [
            {"type": "permanent", "effect": f"{NAMESPACE}:{x}"} for x in effect_ids
        ],
    }
    add_to_files(feature_id, data)
    TO_FILLED[f"{feature_id}/name"] = ""
    TO_FILLED[f"{feature_id}/description"] = ""
    return feature_id


def build_selection_feature(
    categories: list[str],
    en_name: str,
    category: str,
    effect_ids: list[str],
    choose: int,
):
    feature_id = f"{'.'.join(categories)}.{en_name}"
    feature_id = id_formating(feature_id)
    data = {
        "name": f"%{feature_id}/name%",
        "description": f"%{feature_id}/description%",
        "category": category,
        "effects": {
            "choose": choose,
            "available": [
                {"type": "permanent", "effect": f"{NAMESPACE}:{x}"} for x in effect_ids
            ],
        },
    }
    add_to_files(feature_id, data)
    return feature_id


def process_entries(
    entries, prefix="", suffix="  ", mod_configs: dict[str, str] = None
):
    configs = {"entries": "## {}", "inset": "**{}**", "table": "**{}**"}
    if mod_configs is not None:
        configs.update(mod_configs)
    lines = []
    for entry in entries:
        if not isinstance(entry, dict):
            lines.append(f"{prefix}{entry}{suffix}")
            continue
        match entry["type"]:
            case "entries":
                if "name" in entry:
                    lines.append(
                        f"{prefix}{configs['entries'].format(entry['name'])}{suffix}"
                    )
                lines.extend(process_entries(entry["entries"], mod_configs=configs))
            case "inset":
                if "name" in entry:
                    lines.append(
                        f"{prefix}> {configs['inset'].format(entry['name'])}{suffix}"
                    )
                lines.extend(
                    process_entries(
                        entry["entries"],
                        prefix=prefix + "> ",
                        mod_configs=configs.update({"entries": "**{}**"}),
                    )
                )
            case "table":
                if "caption" in entry:
                    lines.append(f"{prefix}{configs['table'].format(entry['caption'])}")
                lines.append(f'{prefix}| {" | ".join(entry["colLabels"])} |')
                lines.append(
                    f"{prefix}| {' | '.join(['---' for _ in entry['colLabels']])} |"
                )
                for row in entry["rows"]:
                    lines.append(f"{prefix}| {' | '.join(row)} |")
            case "section":
                lines.extend(process_entries(entry["entries"], mod_configs=configs))
    return lines


def build_race(
    categories: list[str],
    en_name: str,
    feature_ids: list[str],
    additionals: dict | None = None,
):
    race_id = f"{'.'.join(categories)}.{en_name}"
    race_id = id_formating(race_id)
    data = {
        "name": f"%{race_id}/name%",
        "description": f"%{race_id}/description%",
        "features": [f"{NAMESPACE}:{x}" for x in feature_ids if x is not None],
        "additional": additionals,
    }
    add_to_files(race_id, data)
    return race_id


def speed(data, feature_categories: list[str], category: str) -> str:
    if "speed" in data:
        effect_ids = []
        if not isinstance(data["speed"], int):
            for key, value in data["speed"].items():
                if value == True:
                    continue
                effect_id = build_effect(["effects", "speed"], f"{key}_{value}")
                effect_ids.append(effect_id)
        else:
            effect_id = build_effect(["effects", "speed"], f"walk_{data['speed']}")
            effect_ids.append(effect_id)
        feature_id = build_feature(feature_categories, "speed", category, effect_ids)
        return feature_id


def size(data, feature_categories: list[str], category: str) -> str:
    if "size" in data:
        if len(data["size"]) > 1:
            effect_ids = []
            for size in data["size"]:
                effect_ids.append(build_effect(["effects", "size"], str(size)))
            feature_id = build_selection_feature(
                feature_categories, "size", "race_traits", effect_ids, 1
            )
        else:
            effect_id = build_effect(["effects", "size"], str(data["size"][0]))
            feature_id = build_feature(
                feature_categories, "size", category, [effect_id]
            )

        return feature_id


def darkvision(data, feature_categories: list[str], category: str) -> str:
    if "darkvision" in data:
        effect_id = build_effect(["effects", "darkvision"], str(data["darkvision"]))
        feature_id = build_feature(
            feature_categories, "darkvision", category, [effect_id]
        )
        return feature_id


def language_proficiencies(data, feature_categories: list[str], category: str) -> str:
    if "languageProficiencies" in data:
        effect_ids = []
        if "anyStandard" not in data["languageProficiencies"][0]:
            for key in data["languageProficiencies"][0]:
                effect_id = build_effect(["effects", "language"], key.lower())
                TO_FILLED[f"{effect_id}/name"] = key
                effect_ids.append(effect_id)
        feature_id = build_feature(
            feature_categories, "languages", category, effect_ids
        )
        return feature_id


def skill_proficiencies(data, feature_categories: list[str], category: str) -> str:
    if "skillProficiencies" in data:
        effect_ids = []
        if "any" not in data["skillProficiencies"][0]:
            for key in data["skillProficiencies"][0]:
                effect_id = build_effect(
                    ["effects", "proficiencies", "skills"], key.lower()
                )
                TO_FILLED[f"{effect_id}/name"] = key
                effect_ids.append(effect_id)
        feature_id = build_feature(feature_categories, "skills", category, effect_ids)
        return feature_id


def tool_proficiencies(data, feature_categories: list[str], category: str) -> str:
    if "toolProficiencies" in data:
        effect_ids = []
        if "choose" in data["toolProficiencies"][0]:
            for tool in data["toolProficiencies"][0]["choose"]["from"]:
                effect_id = build_effect(
                    ["effects", "proficiencies", "tools"],
                    tool.replace("'s", "").replace(" ", "_"),
                )
                TO_FILLED[f"{effect_id}/name"] = tool
                effect_ids.append(effect_id)
            feature_id = build_feature(
                feature_categories, "tools", category, effect_ids
            )
            return feature_id


def weapon_proficiencies(data, feature_categories: list[str], category: str) -> str:
    if "weaponProficiencies" in data:
        effect_ids = []
        for key in data["weaponProficiencies"][0]:
            effect_id = build_effect(
                ["effects", "proficiencies", "weapons"],
                key.split("|")[0].replace(" ", "_"),
            )
            TO_FILLED[f"{effect_id}/name"] = key.split("|")[0]
            effect_ids.append(effect_id)
        feature_id = build_feature(feature_categories, "weapons", category, effect_ids)
        return feature_id


def abilities(data, feature_categories: list[str], category: str) -> str:
    if "ability" in data:
        effect_ids = []
        for key, value in data["ability"][0].items():
            if key != "choose":
                effect_id = build_effect(["effects", "abilities"], f"{key}_add_{value}")
                effect_ids.append(effect_id)
            else:
                selection = {"choose": 1, "available": []}
                for ability in value["from"]:
                    effect_id = build_effect(
                        ["effects", "abilities"],
                        f"{ability}_add_{value.get('count', 1)}",
                    )
                    selection["available"].append(effect_id)
                effect_ids.append(selection)
        feature_id = build_feature(
            feature_categories, "abilities", category, effect_ids
        )
        return feature_id


def resists(data, feature_categories: list[str], category: str) -> str:
    if "resist" in data:
        effect_ids = []
        for value in data["resist"]:
            if isinstance(value, str):
                effect_id = build_effect(["effects", "resists"], value.lower())
                effect_ids.append(effect_id)
            else:
                selection = {"choose": 1, "available": []}
                for item in value["choose"]["from"]:
                    effect_id = build_effect(["effects", "resists"], item.lower())
                    selection["available"].append(effect_id)
                effect_ids.append(selection)
        feature_id = build_feature(feature_categories, "resists", category, effect_ids)
        return feature_id


def armor_proficiencies(data, feature_categories: list[str], category: str) -> str:
    if "armorProficiencies" in data:
        effect_ids = []
        for key in data["armorProficiencies"]:
            effect_id = build_effect(["effects", "proficiencies", "armor"], key)
            effect_ids.append(effect_id)
        feature_id = build_feature(feature_categories, "armor", category, effect_ids)
        return feature_id


def process_races(raw_races, fluff):
    for race in raw_races:
        race_name = race["name"]
        feature_categories = ["features", race_name]
        feature_ids = []

        feature_id = speed(race, feature_categories, "race_traits")
        feature_ids.append(feature_id)
        feature_id = size(race, feature_categories, "race_traits")
        feature_ids.append(feature_id)
        feature_id = darkvision(race, feature_categories, "race_traits")
        feature_ids.append(feature_id)
        feature_id = language_proficiencies(race, feature_categories, "race_traits")
        feature_ids.append(feature_id)
        feature_id = skill_proficiencies(race, feature_categories, "race_proficiencies")
        feature_ids.append(feature_id)
        feature_id = tool_proficiencies(race, feature_categories, "race_proficiencies")
        feature_ids.append(feature_id)
        feature_id = weapon_proficiencies(
            race, feature_categories, "race_proficiencies"
        )
        feature_ids.append(feature_id)
        feature_id = abilities(race, feature_categories, "race_traits")
        feature_ids.append(feature_id)
        feature_id = resists(race, feature_categories, "race_traits")
        feature_ids.append(feature_id)

        description = [f"# {race_name}"]
        if race.get("hasFluff", False):
            for content in fluff:
                if race_name == content["name"]:
                    target_fluff = content
                    break
            description.extend(process_entries(target_fluff["entries"]))
        if "entries" in race:
            description.append("## Race Traits")
            description.extend(
                process_entries(race["entries"], mod_configs={"entries": "**{}**"})
            )

        race_id = build_race(
            ["races"],
            race_name,
            feature_ids,
            {k: v for k, v in race.items() if k not in PROCESSED_KEYS},
        )
        TO_FILLED[f"{race_id}/name"] = race_name
        TO_FILLED[f"{race_id}/description"] = description


def process_subraces(raw_subraces, fluff):
    for subrace in raw_subraces:
        if "name" not in subrace:
            continue
        subrace_name = subrace["name"]
        race_name = subrace["raceName"]
        feature_categories = ["features", race_name, subrace_name]
        feature_ids = []

        feature_id = speed(subrace, feature_categories, "subrace_traits")
        feature_ids.append(feature_id)
        feature_id = size(subrace, feature_categories, "subrace_traits")
        feature_ids.append(feature_id)
        feature_id = darkvision(subrace, feature_categories, "subrace_traits")
        feature_ids.append(feature_id)
        feature_id = language_proficiencies(
            subrace, feature_categories, "subrace_traits"
        )
        feature_ids.append(feature_id)
        feature_id = skill_proficiencies(
            subrace, feature_categories, "subrace_proficiencies"
        )
        feature_ids.append(feature_id)
        feature_id = tool_proficiencies(
            subrace, feature_categories, "subrace_proficiencies"
        )
        feature_ids.append(feature_id)
        feature_id = weapon_proficiencies(
            subrace, feature_categories, "subrace_proficiencies"
        )
        feature_ids.append(feature_id)
        feature_id = armor_proficiencies(
            subrace, feature_categories, "subrace_proficiencies"
        )
        feature_ids.append(feature_id)
        feature_id = abilities(subrace, feature_categories, "subrace_traits")
        feature_ids.append(feature_id)
        feature_id = resists(subrace, feature_categories, "subrace_traits")
        feature_ids.append(feature_id)

        description = [f"# {subrace_name}"]
        if subrace.get("hasFluff", False):
            for content in fluff:
                if race_name in content["name"] and subrace_name in content["name"]:
                    target_fluff = content
                    break
            if "_copy" in target_fluff:
                description.extend(
                    process_entries(target_fluff["_copy"]["_mod"]["entries"]["items"])
                )
            if "entries" in target_fluff:
                description.extend(process_entries(target_fluff["entries"]))
        if "entries" in subrace:
            description.append("## Subclass Traits")
            description.extend(
                process_entries(subrace["entries"], mod_configs={"entries": "**{}**"})
            )

        subrace_id = build_race(
            ["subraces", race_name],
            subrace_name,
            feature_ids,
            {k: v for k, v in subrace.items() if k not in PROCESSED_KEYS},
        )
        TO_FILLED[f"{subrace_id}/name"] = subrace["name"]
        if "entries" in subrace:
            TO_FILLED[f"{subrace_id}/description"] = process_entries(subrace["entries"])

        race_id = id_formating(f"races.{race_name}")
        if "subraces" in FILES[race_id]:
            FILES[race_id]["subraces"].append(subrace_id)
        else:
            FILES[race_id]["subraces"] = [subrace_id]


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


def main():
    with open("database/races.json") as file:
        root = json.load(file)

    with open("database/fluff-races.json") as file:
        fluff = json.load(file)

    raw_races: list[dict[str, Any]] = [
        x for x in root["race"] if "PHB" in x.get("source")
    ]
    process_races(raw_races, fluff["raceFluff"])

    raw_subraces: list[dict[str, Any]] = [
        x for x in root["subrace"] if "PHB" in x.get("source")
    ]
    process_subraces(raw_subraces, fluff["raceFluff"])


main()
save("database/data")
