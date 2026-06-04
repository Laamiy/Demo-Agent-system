import json
import random
from pathlib import Path

input_path = Path("dataset/mt560_sampled_10k.jsonl")
output_path = Path("dataset/malagasy_train.jsonl")

tasks = []

with open(input_path, "r", encoding="utf-8") as f:
    texts = [json.loads(line)["text"] for line in f]

# Task 1: Sentence completion (40%)
random.shuffle(texts)
for text in texts[:len(texts)//3]:
    split_point = text.find(" ", len(text)//3)
    if split_point == -1:
        continue
    prefix = text[:split_point]
    suffix = text[split_point:].strip()
    
    tasks.append({
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Respond in Malagasy."},
            {"role": "user", "content": f"Farito io fehezanteny io: \"{prefix}...\""},
            {"role": "assistant", "content": suffix}
        ]
    })

# Task 2: Paraphrase / rephrase (30%)
random.shuffle(texts)
for text in texts[:len(texts)//3]:
    tasks.append({
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Respond in Malagasy."},
            {"role": "user", "content": f"Lazao amin'ny fomba hafa: \"{text}\""},
            {"role": "assistant", "content": text}  # Self-paraphrase; model learns to vary
        ]
    })

# Task 3: Direct response (30%) — model learns to answer in Malagasy
random.shuffle(texts)
for text in texts[:len(texts)//3]:
    tasks.append({
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Respond in Malagasy."},
            {"role": "user", "content": f"Inona no hevitr'ity fehezanteny ity? \"{text}\""},
            {"role": "assistant", "content": text}
        ]
    })

random.shuffle(tasks)

with open(output_path, "w", encoding="utf-8") as f:
    for task in tasks:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")

print(f"Generated {len(tasks)} training examples")