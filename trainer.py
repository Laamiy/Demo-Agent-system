import torch
from unsloth import FastLanguageModel
from datasets import Dataset
from trl import SFTTrainer
from transformers import TrainingArguments
import json
from api.common.logger import logger 

MODEL_PATH = "models/Qwen2.5-1.5B-Instruct"  
MAX_SEQ_LENGTH = 256
LORA_RANK = 8
OUTPUT_DIR = "models/output_model/malagasy_lora"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_PATH,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=LORA_RANK * 2,
    lora_dropout=0,
    use_gradient_checkpointing="unsloth",
)

data = []
with open("dataset/data/malagasy_train.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

dataset = Dataset.from_list(data)

def format_messages(examples):
    input_ids_list = []
    attention_mask_list = []
    for messages in examples["messages"]:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        tokens = tokenizer(
            text,
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            add_special_tokens=False,
        )
        input_ids_list.append(tokens["input_ids"])
        attention_mask_list.append(tokens["attention_mask"])
    return {
        "input_ids": input_ids_list,
        "attention_mask": attention_mask_list
    }

dataset = dataset.map(format_messages, batched=True)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    max_seq_length=MAX_SEQ_LENGTH,
    args=TrainingArguments(
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        warmup_steps=50,
        max_steps=1000,
        learning_rate=2e-4,
        bf16=True,
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir=OUTPUT_DIR,
        report_to="none",
        save_steps=500,
        gradient_checkpointing=True,
    ),
)

logger.info("Starting training...")
trainer.train()

model.save_pretrained(f"{OUTPUT_DIR}/adapter")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/adapter")
logger.info(f"Saved adapter to {OUTPUT_DIR}/adapter")