from process_classes import main as process_classes
from process_races import main as process_races
from utils import save

process_races("5etools/data")
process_classes("5etools/data/class")
save("classes_data/_dnd5e")