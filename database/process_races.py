import json
from utils import (
    id_formating,
    add_to_files,
    add_to_filled,
    build_effect,
    build_feature,
    build_selection,
    get_file,
)

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
                lines.append("")
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
            case "list":
                for item in entry["items"]:
                    lines.append(
                        f"{prefix}+ **{item['name']}** {item['entry']}{suffix}"
                    )
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
        "features": feature_ids,
        "subraces": [],
        "additional": additionals,
    }
    add_to_files(race_id, data)
    add_to_filled(f"{race_id}/name")
    add_to_filled(f"{race_id}/description")
    return race_id


def process_speed(speed, feature_categories: list[str], category: str) -> str:
    effect_ids = []
    if not isinstance(speed, int):
        for key, value in speed.items():
            if value == True:
                continue
            effect_id = build_effect(["effects", "speed"], f"{key}_{value}")
            effect_ids.append(id_formating(effect_id, True))
    else:
        effect_id = build_effect(["effects", "speed"], f"walk_{speed}")
        effect_ids.append(id_formating(effect_id, True))
    feature_id = build_feature(feature_categories, "speed", category, effect_ids)
    return feature_id


def process_size(size, feature_categories: list[str], category: str) -> str:
    if len(size) > 1:
        effect_ids = []
        for s in size:
            effect_id = build_effect(["effects", "size"], str(s))
            effect_ids.append(id_formating(effect_id, True))
        selection = build_selection(effect_ids, 1)
        feature_id = build_feature(
            feature_categories, "size", "race_traits", [selection]
        )
    else:
        effect_id = build_effect(["effects", "size"], str(size[0]))
        feature_id = build_feature(
            feature_categories, "size", category, [id_formating(effect_id, True)]
        )

    return feature_id


def process_darkvision(darkvision, feature_categories: list[str], category: str) -> str:
    effect_id = build_effect(["effects"], f"darkvision@{darkvision}")
    feature_id = build_feature(
        feature_categories, "darkvision", category, [id_formating(effect_id, True)]
    )
    return feature_id


def process_language_proficiencies(
    language_proficiencies, feature_categories: list[str], category: str
) -> str:
    effect_ids = []
    if "anyStandard" not in language_proficiencies[0]:
        for key in language_proficiencies[0]:
            effect_id = build_effect(["effects", "languages"], key.lower())
            effect_ids.append(id_formating(effect_id, True))
    feature_id = build_feature(feature_categories, "languages", category, effect_ids)
    return feature_id


def process_skill_proficiencies(
    skill_proficiencies, feature_categories: list[str], category: str
) -> str:
    effect_ids = []
    if "any" not in skill_proficiencies[0]:
        for key in skill_proficiencies[0]:
            effect_id = build_effect(
                ["effects", "proficiencies", "skills"], key.lower()
            )
            effect_ids.append(id_formating(effect_id, True))
    feature_id = build_feature(feature_categories, "skills", category, effect_ids)
    return feature_id


def process_tool_proficiencies(
    tool_proficiencies, feature_categories: list[str], category: str
) -> str:
    effect_ids = []
    if "choose" in tool_proficiencies[0]:
        available = []
        for tool in tool_proficiencies[0]["choose"]["from"]:
            item_id = build_effect(["effects", "proficiencies", "tools"], tool)
            available.append(id_formating(item_id, True))
        print(tool_proficiencies[0])
        effect_ids.append(build_selection(available, 1))
    else:
        for tool in tool_proficiencies[0]:
            effect_id = build_effect(["effects", "proficiencies", "tools"], tool)
            effect_ids.append(id_formating(effect_id, True))
    feature_id = build_feature(feature_categories, "tools", category, effect_ids)
    return feature_id


def process_weapon_proficiencies(
    weapon_proficiencies, feature_categories: list[str], category: str
) -> str:
    effect_ids = []
    for key in weapon_proficiencies[0]:
        effect_id = build_effect(
            ["effects", "proficiencies", "weapons"],
            key.split("|")[0].replace(" ", "_"),
        )
        effect_ids.append(id_formating(effect_id))
    feature_id = build_feature(feature_categories, "weapons", category, effect_ids)
    return feature_id


def process_abilities(ability, feature_categories: list[str], category: str) -> str:
    effects = []
    for key, value in ability[0].items():
        if key != "choose":
            effect_id = build_effect(["effects", "abilities"], f"{key}_add@{value}")
            effects.append(id_formating(effect_id, True))
        else:
            available = []
            for a in value["from"]:
                effect_id = build_effect(
                    ["effects", "abilities"],
                    f"{a}_add@{value.get('count', 1)}",
                )
                available.append(id_formating(effect_id, True))
                selection = build_selection(available, 1)
            effects.append(selection)
    feature_id = build_feature(feature_categories, "abilities", category, effects)
    return feature_id


def process_resists(resists, feature_categories: list[str], category: str) -> str:
    effect_ids = []
    for value in resists:
        if isinstance(value, str):
            effect_id = build_effect(["effects", "resists"], value.lower())
            effect_ids.append(id_formating(effect_id, True))
        else:
            available = []
            for item in value["choose"]["from"]:
                effect_id = build_effect(["effects", "resists"], item.lower())
                available.append(id_formating(effect_id, True))
                selection = build_selection(available, 1)
            effect_ids.append(selection)
    feature_id = build_feature(feature_categories, "resists", category, effect_ids)
    return feature_id


def process_armor_proficiencies(
    armar_proficiencies, feature_categories: list[str], category: str
) -> str:
    effect_ids = []
    for key in armar_proficiencies:
        effect_id = build_effect(["effects", "proficiencies", "armor"], key)
        effect_ids.append(id_formating(effect_id, True))
    feature_id = build_feature(feature_categories, "armor", category, effect_ids)
    return feature_id


def process_races(race):
    race_name = race["name"]
    feature_categories = ["features", race_name]
    feature_ids = []

    feature_id = process_speed(race["speed"], feature_categories, "race_traits")
    feature_ids.append(id_formating(feature_id))
    feature_id = process_size(race["size"], feature_categories, "race_traits")
    feature_ids.append(id_formating(feature_id))
    if "darkvision" in race:
        feature_id = process_darkvision(
            race["darkvision"], feature_categories, "race_traits"
        )
    feature_ids.append(id_formating(feature_id))
    feature_id = process_language_proficiencies(
        race["languageProficiencies"], feature_categories, "race_traits"
    )
    feature_ids.append(id_formating(feature_id))
    if "skillProficiencies" in race:
        feature_id = process_skill_proficiencies(
            race["skillProficiencies"], feature_categories, "race_proficiencies"
        )
        feature_ids.append(id_formating(feature_id))
    if "toolProficiencies" in race:
        feature_id = process_tool_proficiencies(
            race["toolProficiencies"], feature_categories, "race_proficiencies"
        )
        feature_ids.append(id_formating(feature_id))
    if "weaponProficiencies" in race:
        feature_id = process_weapon_proficiencies(
            race["weaponProficiencies"], feature_categories, "race_proficiencies"
        )
        feature_ids.append(id_formating(feature_id))
    if "ability" in race:
        feature_id = process_abilities(
            race["ability"], feature_categories, "race_traits"
        )
        feature_ids.append(id_formating(feature_id))
    if "resist" in race:
        feature_id = process_resists(race["resist"], feature_categories, "race_traits")
        feature_ids.append(id_formating(feature_id))

    build_race(
        ["races"],
        race_name,
        feature_ids,
        {k: v for k, v in race.items() if k not in PROCESSED_KEYS},
    )


def process_subraces(subrace):
    if "name" not in subrace:
        return
    subrace_name = subrace["name"]
    race_name = subrace["raceName"]
    feature_categories = ["features", race_name, subrace_name]
    feature_ids = []

    if "speed" in subrace:
        feature_id = process_speed(
            subrace["speed"], feature_categories, "subrace_traits"
        )
        feature_ids.append(id_formating(feature_id))
    if "size" in subrace:
        feature_id = process_size(subrace["size"], feature_categories, "subrace_traits")
        feature_ids.append(id_formating(feature_id))
    if "darkvision" in subrace:
        feature_id = process_darkvision(
            subrace["darkvision"], feature_categories, "subrace_traits"
        )
        feature_ids.append(id_formating(feature_id))
    if "languageProficiencies" in subrace:
        feature_id = process_language_proficiencies(
            subrace["languageProficiencies"], feature_categories, "subrace_traits"
        )
        feature_ids.append(id_formating(feature_id))
    if "skillProficiencies" in subrace:
        feature_id = process_skill_proficiencies(
            subrace["skillProficiencies"], feature_categories, "subrace_proficiencies"
        )
        feature_ids.append(id_formating(feature_id))
    if "toolProficiencies" in subrace:
        feature_id = process_tool_proficiencies(
            subrace["toolProficiencies"], feature_categories, "subrace_proficiencies"
        )
        feature_ids.append(id_formating(feature_id))
    if "weaponProficiencies" in subrace:
        feature_id = process_weapon_proficiencies(
            subrace["weaponProficiencies"], feature_categories, "subrace_proficiencies"
        )
        feature_ids.append(id_formating(feature_id))
    if "armorProficiencies" in subrace:
        feature_id = process_armor_proficiencies(
            subrace["armorProficiencies"], feature_categories, "subrace_proficiencies"
        )
        feature_ids.append(id_formating(feature_id))
    if "ability" in subrace:
        feature_id = process_abilities(
            subrace["ability"], feature_categories, "subrace_traits"
        )
        feature_ids.append(id_formating(feature_id))
    if "resist" in subrace:
        feature_id = process_resists(
            subrace["resist"], feature_categories, "subrace_traits"
        )
        feature_ids.append(id_formating(feature_id))

    subrace_id = build_race(
        ["subraces", race_name],
        subrace_name,
        feature_ids,
        {k: v for k, v in subrace.items() if k not in PROCESSED_KEYS},
    )
    race_id = id_formating(f"races.{race_name}")
    get_file(race_id)["subraces"].append(id_formating(subrace_id, True))


def main(original_data: str):
    with open(f"{original_data}/races.json") as file:
        root = json.load(file)
        for race in root["race"]:
            if "PHB" not in race.get("source"):
                continue
            process_races(race)
        for subrace in root["subrace"]:
            if "PHB" not in subrace.get("source"):
                continue
            process_subraces(subrace)
