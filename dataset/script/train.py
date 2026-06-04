import torch
from unsloth import FastLanguageModel
from datasets import Dataset
from trl import SFTTrainer
from transformers import TrainingArguments
import json

# Load data
data = []
with open("dataset/malagasy_train.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

dataset = Dataset.from_list(data)

# Format for Qwen2.5 chat template
def format_messages(examples):
    texts = []
    for messages in examples["messages"]:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        texts.append(text)
    return {"text": texts}

dataset = dataset.map(format_messages, batched=True)

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="models/Qwen2.5-1.5B-Instruct",  # your local path
    max_seq_length=512,
    dtype=None,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=32,
    lora_dropout=0.05,
    use_gradient_checkpointing="unsloth",
)

# Train
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=512,
    args=TrainingArguments(
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=500,  # ~2-3 epochs on 10k examples
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        output_dir="outputs/malagasy_lora",
        report_to="none",
    ),
)

trainer.train()
model.save_pretrained("outputs/malagasy_lora/adapter")
tokenizer.save_pretrained("outputs/malagasy_lora/adapter")