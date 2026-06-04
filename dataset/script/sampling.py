import json
import random
from pathlib import Path
from collections import defaultdict
from .score import quality_score


data_path = Path("dataset/mt560_cleaned.jsonl")
output_path = Path("dataset/mt560_sampled_10k.jsonl")

# Load and score
scored = []
with open(data_path, "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        text = row["text"]
        score = quality_score(text)
        scored.append((score, text))

# Keep top 80% by score
scored.sort(reverse=True)
cutoff = int(len(scored) * 0.8)
kept = scored[:cutoff]

# Stratify by length
buckets = defaultdict(list)
for _, text in kept:
    w = len(text.split())
    if w < 8:
        buckets["short"].append(text)
    elif w < 20:
        buckets["medium"].append(text)
    elif w < 40:
        buckets["long"].append(text)
    else:
        buckets["very_long"].append(text)

# Sample targets
targets = {"short": 2000, "medium": 4000, "long": 2500, "very_long": 1500}
sampled = []
for bucket, target in targets.items():
    pool = buckets[bucket]
    random.shuffle(pool)
    sampled.extend(pool[:target])

random.shuffle(sampled)

# Save as simple text lines (we will format for training next)
with open(output_path, "w", encoding="utf-8") as f:
    for text in sampled:
        f.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")

print(f"Sampled {len(sampled)} examples")