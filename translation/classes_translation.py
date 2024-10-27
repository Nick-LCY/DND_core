import chardet
import re, json
from bs4 import BeautifulSoup, NavigableString, PageElement

PATH = "DND5e_chm/玩家手册/职业"
PREFIX_MAPPING = {
    "text": "",
    "h2": "## ",
}

attributes = {}
markdown = []
markdown_cache = ""


def process_markdown(content: str, attributes: dict):
    if attributes.get("bold", False) and attributes.get("pre", "text") == "text":
        content = f"**{content}**"
    return content


def check_append(name: str, attributes: dict) -> bool:
    global markdown_cache
    if markdown_cache == "":
        return False
    if attributes.get("is_td", False):
        return False
    if name not in ["h2", "p", "br", "h4", "table", "tr"]:
        return False
    match attributes.get("pre"):
        case "h1":
            markdown_cache = f"# {markdown_cache}"
        case "h2":
            markdown_cache = f"## {markdown_cache}"
        case "h3":
            markdown_cache = f"### {markdown_cache}"
        case "h4":
            markdown_cache = f"#### {markdown_cache}"
        case "table":
            markdown_cache = f"| {markdown_cache}"
    markdown_cache += "  "
    markdown_cache = re.sub(r"\*{3,}", "", markdown_cache)
    markdown_cache = re.sub(r"\*\*([^*]+)\*\*", r"**\1** ", markdown_cache)
    markdown.append(markdown_cache)
    markdown_cache = ""
    return True


def visit(soup: PageElement, attributes: dict | None = None):
    global markdown_cache
    if attributes is None:
        attributes = {}
    backup_attributes = attributes.copy()
    for content in soup.contents:
        if not isinstance(content, NavigableString):
            if check_append(content.name, attributes):
                attributes.update(backup_attributes)
                to_del = []
                for key in attributes:
                    if key not in backup_attributes:
                        to_del.append(key)
                for key in to_del:
                    del attributes[key]
                attributes = backup_attributes.copy()
            if content.name == "h2":
                attributes["pre"] = "h2"
            if "18pt" in content.get("style", ""):
                attributes["pre"] = "h3"
            if content.name == "h4":
                attributes["pre"] = "h4"
            if "bold" in content.get("style", ""):
                attributes["bold"] = True
            if content.name in ["table", "tr"]:
                attributes["pre"] = "table"
            if not content.name == "td":
                visit(content, attributes)
            else:
                attributes["is_td"] = True
                visit(content, attributes)
                markdown_cache += " | "
                attributes["is_td"] = False
        else:
            markdown_cache += process_markdown(content, attributes)
        attributes["bold"] = False


def main():
    global markdown
    data = {}
    for name in [
        "吟游诗人",
        "圣武士",
        "德鲁伊",
        "战士",
        "术士",
        "武僧",
        "法师",
        "游侠",
        "游荡者",
        "牧师",
        "邪术师",
        "野蛮人",
    ]:
        path = f"{PATH}/{name}.html"
        with open(path, "rb") as file:
            content = file.read()
            encoding = chardet.detect(content)["encoding"]
            content = content.decode(encoding).replace("\n", "")
            content = re.sub(r"</*font[^>]*>", "", content)
            soup = BeautifulSoup(content, "html.parser")
            markdown.append(f"# {soup.title.text}  ")
            for tag in soup.find_all(["o:p"]):
                tag.decompose()
            for tag in soup.find_all(["span", "p"]):
                if re.sub(r"(?:\n|\s)*", "", tag.text) == "" and tag.br is None:
                    tag.decompose()
            visit(soup.body)
            markdown.append(markdown_cache)
            data[soup.title.text] = markdown
            markdown = []
    with open("translation/classes.json", "w") as file:
        json.dump(data, file, ensure_ascii=False)


main()
