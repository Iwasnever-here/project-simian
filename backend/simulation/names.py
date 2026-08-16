import csv
import random
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"

MALE_NAMES_FILE = DATA_DIR / "male_names.csv"
FEMALE_NAMES_FILE = DATA_DIR / "female_names.csv"


def load_names(file_path):
    names = []

    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            name = row["name"].strip()

            if name:
                names.append(name)

    return names


MALE_NAMES = load_names(MALE_NAMES_FILE)
FEMALE_NAMES = load_names(FEMALE_NAMES_FILE)


def generate_monkey_identity():
    gender = random.choice([
        "male",
        "female",
    ])

    if gender == "male":
        name = random.choice(MALE_NAMES)
    else:
        name = random.choice(FEMALE_NAMES)

    return name, gender