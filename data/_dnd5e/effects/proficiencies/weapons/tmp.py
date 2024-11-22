import os, json

for filename in os.listdir("."):
    if filename == "tmp.py":
        continue
    print(filename)
    with open(filename, "r+") as file:
        obj = json.load(file)
        obj["expressions"] = [
            {
                "target": "character.proficiencies",
                "operation": "push",
                "values": [f"%effects.proficiencies.weapons.{filename[:-5]}/name%"],
            }
        ]
    with open(filename, "w+") as file:
        json.dump(obj, file)
