import json
from utils import (
    id_formating,
    build_effect,
    build_feature,
    add_to_files,
    add_to_filled,
    build_selection,
    save,
)


def build_background(bg_name: str, features: list[str]):
    bg_id = "backgrounds." + bg_name
    bg_id = id_formating(bg_id)
    data = {"name": "", "description": "", "features": features}
    add_to_files(bg_id, data)
    add_to_filled(f"{bg_id}/name")
    add_to_filled(f"{bg_id}/description")
    return bg_id


with open("5etools/data/backgrounds.json") as file:
    data = json.load(file)

tmp = set(data["background"][0].keys())
for background in data["background"]:
    if background["source"] != "PHB":
        continue
    tmp.update(background.keys())
    bg_id = id_formating(background["name"])
    if "custom" in bg_id or "variant" in bg_id:
        continue
    features = []
    if "toolProficiencies" in background:
        tools = []
        for k, v in dict(background["toolProficiencies"][0]).items():
            if type(v) == type(True):
                tools.append(
                    id_formating(
                        build_effect(["effects", "proficiencies", "tools"], k), True
                    )
                )
            if "any" in k:
                tools.append(f"_dnd5e:effects.todo@{id_formating(k)}")
            if k == "choose":
                options = []
                for option in v["from"]:
                    options.append(
                        id_formating(
                            build_effect(["effects", "proficiencies", "tools"], option),
                            True,
                        )
                    )
                tools.append(build_selection(options, 1))
        features.append(
            id_formating(
                build_feature(
                    ["features", bg_id], "tools", "background_proficiencies", tools
                ),
                True,
            )
        )
    if "languageProficiencies" in background:
        features.append(
            id_formating(
                build_feature(
                    ["features", bg_id],
                    "languages",
                    "background_feature",
                    [
                        build_selection(
                            [
                                "_dnd5e:effects.languages.common",
                                "_dnd5e:effects.languages.draconic",
                                "_dnd5e:effects.languages.dwarvish",
                                "_dnd5e:effects.languages.elvish",
                                "_dnd5e:effects.languages.gnomish",
                                "_dnd5e:effects.languages.halfling",
                                "_dnd5e:effects.languages.infernal",
                                "_dnd5e:effects.languages.orc",
                            ],
                            background["languageProficiencies"][0]["anyStandard"],
                        )
                    ],
                ),
                True,
            )
        )
    if "skillProficiencies" in background:
        skills = []
        for key, v in dict(background["skillProficiencies"][0]).items():
            if key == "any":
                skills.append(build_selection([], v))
            else:
                skills.append(
                    f"_dnd5e:effects.proficiencies.skills.{id_formating(key)}"
                )
        features.append(
            id_formating(
                build_feature(
                    ["features", bg_id], "skills", "background_proficiencies", skills
                ),
                True,
            )
        )
        features.append(
            id_formating(
                build_feature(
                    ["features", bg_id], "equipment", "background_equipment", []
                ),
                True,
            ),
        )
    for key in ["personality_trait", "ideal", "bond", "flaw"]:
        features.append(
            id_formating(
                build_feature(
                    ["features", bg_id],
                    key,
                    "background_traits",
                    [build_selection([], 1)],
                ),
                True,
            )
        )

    build_background(bg_id, features)

save("gen_data/background")
