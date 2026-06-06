# dataset/formatter.py
import json
import random
from pathlib import Path
from api.common.logger import logger
input_path = Path("dataset/data/mt560_sampled_10k.jsonl")
output_path = Path("dataset/data/malagasy_train.jsonl")

tasks = []

with open(input_path, "r", encoding="utf-8") as f:
    samples = [json.loads(line) for line in f]

# Task 1: Sentence completion (40%) — model learns to continue text
random.seed(42)
random.shuffle(samples)
for s in samples[:4000]:
    text = s["text"]
    words = text.split()
    split = len(words) // 3
    prefix = " ".join(words[:split])
    suffix = " ".join(words[split:])
    
    tasks.append({
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Respond in Malagasy."},
            {"role": "user", "content": f"Farito io fehezanteny io: \"{prefix}...\""},
            {"role": "assistant", "content": suffix}
        ]
    })

# Task 2: Paraphrase / rephrase (30%) — model learns variation
random.shuffle(samples)
for s in samples[4000:7000]:
    text = s["text"]
    tasks.append({
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Respond in Malagasy."},
            {"role": "user", "content": f"Lazao amin'ny fomba hafa: \"{text}\""},
            {"role": "assistant", "content": text}
        ]
    })

# Task 3: Direct response / comprehension (30%) — model learns to answer
random.shuffle(samples)
for s in samples[7000:]:
    text = s["text"]
    tasks.append({
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Respond in Malagasy."},
            {"role": "user", "content": f"Inona no hevitr'ity fehezanteny ity? \"{text}\""},
            {"role": "assistant", "content": text}
        ]
    })

# Add English retention (20% of total = ~2500 examples)
# Use a slice of Alpaca or your existing English instruction data
english_samples = []
try:
    with open("dataset/data/english_retention.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            english_samples.append(json.loads(line))
except FileNotFoundError:
    logger.info("WARNING: No english_retention.jsonl found. Generate it or training will forget English.")
    logger.info("Create it with 2000-2500 standard English instruction-following examples.")

random.shuffle(english_samples)
tasks.extend(english_samples[:2500])

random.shuffle(tasks)

with open(output_path, "w", encoding="utf-8") as f:
    for t in tasks:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")

logger.info(f"Wrote {len(tasks)} training examples to {output_path}")
logger.info(f"  Malagasy completion: 4000")
logger.info(f"  Malagasy paraphrase: 3000")
logger.info(f"  Malagasy comprehension: 3000")
logger.info(f"  English retention: {len(english_samples[:2500])}")