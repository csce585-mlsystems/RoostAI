import pandas as pd
import os
import statistics
import json

res_path = os.path.abspath(
    "C:\\Users\\2002v\\Desktop\\Fall2024\\CSCE585\\RoostAI\\eval\\ragas_evaluation\\data\\results"
)

db_res = [os.path.join(res_path, folder) for folder in os.listdir(res_path)]

db_res = [
    os.path.join(folder, subfolder)
    for folder in db_res
    for subfolder in os.listdir(folder)
    if "v3_50" not in folder
]


v3_scores = {
    "semantic_50": {
        "faithfulness": None,
        "context_precision": None,
        "context_recall": None,
    },
    "semantic_95": {
        "faithfulness": None,
        "context_precision": None,
        "context_recall": None,
    },
    "sentence_splitting": {
        "faithfulness": None,
        "context_precision": None,
        "context_recall": None,
    },
    "fixed_token": {
        "faithfulness": None,
        "context_precision": None,
        "context_recall": None,
    },
}

v3_50_res = "C:\\Users\\2002v\\Desktop\\Fall2024\\CSCE585\\RoostAI\\eval\\ragas_evaluation\\data\\results\\v3_50_thresh\\20241212_035048\\rag_scores.csv"

v3_50_res = pd.read_csv(v3_50_res)
for score in ("faithfulness", "context_precision", "context_recall"):
    scores = list(v3_50_res[score])
    v3_scores["semantic_50"][score] = {"raw": scores, "avg": statistics.mean(scores)}


for res_dir in db_res:
    if "v3_95" in res_dir:
        key = "semantic_95"
    elif "sentence" in res_dir:
        key = "sentence_splitting"
    elif "token" in res_dir:
        key = "fixed_token"

    faith_csv = os.path.join(res_dir, "faithfulness_scores.csv")
    faith_csv = pd.read_csv(faith_csv)
    faith_scores = list(faith_csv["faithfulness"])
    v3_scores[key]["faithfulness"] = {
        "raw": faith_scores,
        "avg": statistics.mean(faith_scores),
    }

    precision_recall_csv = os.path.join(res_dir, "precision_recall_scores.csv")
    precision_recall_csv = pd.read_csv(precision_recall_csv)
    precision_scores = list(precision_recall_csv["context_precision"])
    recall_scores = list(precision_recall_csv["context_recall"])
    v3_scores[key]["context_precision"] = {
        "raw": precision_scores,
        "avg": statistics.mean(precision_scores),
    }
    v3_scores[key]["context_recall"] = {
        "raw": recall_scores,
        "avg": statistics.mean(recall_scores),
    }


# save res as json
with open("rag_res.json", "w") as f:
    json.dump(v3_scores, f)

# save res as csv
df = pd.DataFrame(
    [
        {
            "method": method,
            "faithfulness": scores["faithfulness"]["avg"],
            "context_precision": scores["context_precision"]["avg"],
            "context_recall": scores["context_recall"]["avg"],
        }
        for method, scores in v3_scores.items()
    ]
)

df.to_csv("rag_res.csv")
