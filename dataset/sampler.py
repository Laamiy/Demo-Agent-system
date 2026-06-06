# dataset/sampler.py
import json
import random
from pathlib import Path
from collections import defaultdict
from api.common.logger import logger 
input_path = Path("dataset/data/mt560_cleaned.jsonl")
output_path = Path("dataset/data/mt560_sampled_10k.jsonl")

samples = []
with open(input_path, "r", encoding="utf-8") as f:
    for line in f:
        samples.append(json.loads(line))

print(f"Loaded {len(samples)} cleaned samples")

buckets = defaultdict(list)
for s in samples:
    w = len(s["text"].split())
    if w < 8:
        continue  # discard garbage
    elif w < 20:
        buckets["medium"].append(s)
    elif w < 40:
        buckets["long"].append(s)
    else:
        buckets["very_long"].append(s)

print(f"Buckets: medium={len(buckets['medium'])}, long={len(buckets['long'])}, very_long={len(buckets['very_long'])}")

# Redistributed targets (short mass moved to medium/long)
targets = {"medium": 5000, "long": 3500, "very_long": 1500}
sampled = []

for bucket, target in targets.items():
    pool = buckets[bucket]
    random.seed(42)
    random.shuffle(pool)
    sampled.extend(pool[:target])

random.shuffle(sampled)

with open(output_path, "w", encoding="utf-8") as f:
    for s in sampled:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

logger.info(f"Wrote {len(sampled)} samples to {output_path}")