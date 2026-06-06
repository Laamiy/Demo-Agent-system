from datasets import load_dataset
from api.common.logger import logger
import json

# Download from Hugging Face
repos = ["Lo-Renz-O/malagasy-sentence" , "Lo-Renz-O/vaovao_malagasy_sentiment_corpus","michsethowusu/malagasy-emotions-corpus"]
# dataset = load_dataset("Lo-Renz-O/malagasy-sentence")
dataset_name =[repo.split(sep  =r'/')[1] + '.jsonl'  for repo in repos]
for name in dataset_name : 
    print(name)
    
if 0  : 
    dataset = load_dataset("michsethowusu/malagasy-emotions-corpus")
    # dataset = load_dataset("Lo-Renz-O/vaovao_malagasy_sentiment_corpus")

    # Inspect structure
    logger.info("Dataset splits:", dataset.keys())
    logger.info("Train size: %s ", len(dataset["train"]) if "train" in dataset else "N/A")

    # Show first 20 samples
    logger.info("--- First 20 samples ---")
    for i, sample in enumerate(dataset["train"].select(range(20))):
        logger.info(f"{i}: {sample}")

    # Save locally as JSONL for inspection
    output_path = "dataset/malagasy_raw_emotions_corpus.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for sample in dataset["train"]:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    logger.info(f"Saved {len(dataset['train'])} rows to {output_path}")

logger.info("Downloading Alpaca for English retention...")
alpaca = load_dataset("tatsu-lab/alpaca", split="train")
sampled = alpaca.shuffle(seed=42).select(range(2500))

with open("dataset/data/english_retention.jsonl", "w", encoding="utf-8") as f:
    for ex in sampled:
        instruction = ex["instruction"]
        inp = ex["input"]
        output = ex["output"]
        user_content = instruction + (f"\n\n{inp}" if inp else "")
        
        f.write(json.dumps({
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": output}
            ]
        }, ensure_ascii=False) + "\n")

logger.info("Saved 2500 English retention examples")