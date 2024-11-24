import chardet, os
import re, json
from utils import id_formating, add_to_files, add_to_filled, save
from bs4 import BeautifulSoup, NavigableString, PageElement


def build_spell(spell_id: str, spell_obj):
    spell_id = f"spells.{spell_id}"
    data = {"name": "", "description": ""}
    data.update(spell_obj)
    add_to_files(spell_id, data)
    add_to_filled(f"{spell_id}/name")
    add_to_filled(f"{spell_id}/description")
    return spell_id


def build_spell_list(spell_list_id: str, spells: list[str]):
    spell_list_id = f"spell_lists.{spell_list_id}"
    data = {"name": "", "description": "", "list": spells}
    add_to_files(spell_list_id, data)
    add_to_filled(f"{spell_list_id}/name")
    add_to_filled(f"{spell_list_id}/description")
    return spell_list_id


def gen_data():
    spell_table: dict[str, list[str]] = {}
    with open("/dnd-core/5etools/data/spells/sources.json") as file:
        original_sources = json.load(file)["PHB"]
        sources = {id_formating(x): y for x, y in dict(original_sources).items()}
    with open("/dnd-core/5etools/data/spells/spells-phb.json") as file:
        data = json.load(file)["spell"]
        for spell in data:
            spell_obj = {}
            # id
            spell_id = id_formating(spell["name"])
            # 环位
            spell_level = spell["level"]
            # 学院
            spell_school = {
                "A": "abjuration",
                "C": "conjuration",
                "D": "divination",
                "E": "enchantment",
                "V": "evocation",
                "I": "illusion",
                "N": "necromancye",
                "T": "transmutation",
            }[spell["school"]]
            # 时间
            spell_cast_time = spell["time"]
            # 距离
            spell_range = spell["range"]
            # 成分
            spell_components = spell["components"]
            # 持续
            spell_duration = spell["duration"]
            spell_obj = {
                "school": spell_school,
                "spell_level": spell_level,
                "cast_time": spell_cast_time,
                "duration": spell_duration,
                "components": spell_components,
            }
            # 等级提升
            if "scalingLevelDice" in spell:
                spell_obj["level_dice"] = spell["scalingLevelDice"]["scaling"]
            # TODO 豁免类型 （没有就代表要投命中？）
            # if "savingThrow" in spell:
            #     spell_obj["saving_throw"] = spell["savingThrow"]
            # TODO 伤害类型
            # if "damageInflict" in spell:
            #     spell_obj["damage_inflict"] = spell["damageInflict"]
            # TODO 升环
            # 法表
            for c in sources[spell_id]["class"]:
                if c["source"] != "PHB":
                    continue
                class_id = id_formating(c["name"])
                if class_id not in spell_table:
                    spell_table[class_id] = []
                spell_table[class_id].append(
                    id_formating(build_spell(spell_id, spell_obj), True)
                )

    for class_name, table in spell_table.items():
        build_spell_list(class_name, table)


def gen_translation():
    PATH = "DND5e_chm/玩家手册/魔法/法术详述"
    spells = {}
    for filename in os.listdir(PATH):
        with open(f"{PATH}/{filename}", "rb") as file:
            content = file.read()
            encoding = chardet.detect(content)["encoding"]
            content = content.decode(encoding).replace("\n", "")
            content = re.sub(r"</*font[^>]*>", "", content)
            soup = BeautifulSoup(content, "html.parser")
            for tag in soup.find_all(["o:p"]):
                tag.decompose()
            for tag in soup.find_all(["span", "p"]):
                if re.sub(r"(?:\n|\s)*", "", tag.text) == "" and tag.br is None:
                    tag.decompose()
            description_list = []
            prev_id = None
            for content in soup.body.contents:
                if content.name == "p":
                    description = str(content)[3:]
                    description = description.replace("</p>", "<br/>")
                    description = description.replace("<em>", "*")
                    description = description.replace("</em>", "* ")
                    description = description.replace("<b>", "**")
                    description = description.replace("</b>", "** ")
                    description = description.replace("<strong>", "**")
                    description = description.replace("</strong>", "** ")
                    description = description.replace("<br/>", "  <br/>")
                    description = description.split("<br/>")
                    description = [
                        re.sub(r"<[/]{0,1}[^>]*>", "", x) for x in description
                    ]
                    description = [
                        re.sub(r"^\s+$", "", x) for x in description
                    ]
                    description = [
                        re.sub(r"\s+", " ", x) for x in description
                    ]
                    description_list.extend(description)
                if content.name == "h4":
                    zh_name, en_name = content.text.split("｜")
                    add_to_filled(id_formating(f"spells.{en_name}") + "/name", zh_name)
                    if prev_id is not None:
                        add_to_filled(f"{prev_id}/description", description_list[:-1])
                    description_list = []
                    prev_id = id_formating(f"spells.{en_name}")
            add_to_filled(f"{prev_id}/description", description_list[:-1])


if __name__ == "__main__":
    gen_data()
    gen_translation()
    save("gen_data/spells")
