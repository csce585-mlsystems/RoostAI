import json
import re


def preprocess_json(file_path):
    # read uncleaned file
    with open("test.json", "r", encoding="utf-8") as f:
        content = f.read()

    # replace all pesky \uXXXX characters
    modified_content = re.sub(r"\\u[0-9A-Fa-f]{4}", " ", content)

    # shrink all unnecessary whitespaces (\t, \n, etc.)
    json_dict = json.loads(modified_content)

    def shrink_whitespaces(str_):
        return " ".join(str_.split())

    json_dict["main_text"] = shrink_whitespaces(json_dict["main_text"])

    json_dict["chunks"] = [shrink_whitespaces(chunk) for chunk in json_dict["chunks"]]

    # write cleaned file
    with open(
        "test.json",
        "w",
    ) as file:
        file.write(modified_content)
