import json
from pathlib import Path
from api.common.logger import logger
from dataset.utils.cleaner import  filter_dataset_batch

data_path = Path("dataset/data/malagasy_raw_emotions_corpus.jsonl").resolve()  

output_path = data_path.parent / "mt560_cleaned.jsonl"

if not data_path.exists():
    logger.error("No such file: %s", data_path)
    exit(1)

def reader(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

# Read all samples
samples = list(reader(data_path))
logger.info("Loaded %d raw samples", len(samples))

# Apply the statistical filter
filtered = filter_dataset_batch(samples, verbose=False)

# Write output
with open(output_path, "w", encoding="utf-8") as f:
    for row in filtered:
        f.write(json.dumps({
            "text": row.get("Malagasy_clean", row.get("Malagasy", "")),
            "emotion": row.get("emotion", "neutral"),
            "source": "mt560",
        }, ensure_ascii=False) + "\n")

logger.info("Wrote %d cleaned samples to %s", len(filtered), output_path)