#!/usr/bin/env python3
"""Unsloth QLoRA finetuning script for Qwen2.5-VL-7B on Indian Fashion data.

Usage (Colab T4 Free):
    !pip install unsloth transformers datasets peft
    !python training/finetune_vlm.py --config training/configs/fashion_vlm.yaml

Local (requires GPU):
    python training/finetune_vlm.py --config training/configs/fashion_vlm.yaml
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]


def load_config(config_path: str) -> dict:
    """Load YAML training config."""
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_dataset(dataset_path: str) -> list[dict]:
    """Load ShareGPT-format dataset."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info("Loaded %d training examples from %s", len(data), dataset_path)
    return data


def format_sharegpt_to_chat(examples: list[dict]) -> list[dict]:
    """Convert ShareGPT format to chat format for training."""
    formatted = []
    for ex in examples:
        messages = []
        for turn in ex.get("conversations", []):
            role = "user" if turn["from"] == "human" else "assistant"
            messages.append({"role": role, "content": turn["value"]})
        if messages:
            formatted.append({"messages": messages})
    return formatted


def finetune(config: dict) -> None:
    """Run QLoRA finetuning with Unsloth."""
    try:
        from unsloth import FastLanguageModel
    except ImportError:
        logger.error(
            "Unsloth not installed. Install with:\n"
            "  pip install unsloth\n"
            "Or run on Google Colab (T4 free tier)."
        )
        sys.exit(1)

    from transformers import TrainingArguments
    from trl import SFTTrainer

    model_name = config["model"]["name"]
    max_seq_length = config["model"].get("max_seq_length", 2048)
    lora_config = config.get("lora", {})
    train_config = config.get("training", {})
    output_dir = str(ROOT / config["output"]["dir"])

    # Load model with Unsloth 4-bit quantization
    logger.info("Loading model: %s (4-bit QLoRA)", model_name)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        load_in_4bit=config["model"].get("load_in_4bit", True),
        dtype=None,
    )

    # Apply LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_config.get("rank", 64),
        lora_alpha=lora_config.get("alpha", 128),
        lora_dropout=lora_config.get("dropout", 0.05),
        target_modules=lora_config.get("target_modules", [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ]),
        bias=lora_config.get("bias", "none"),
        use_gradient_checkpointing="unsloth",
    )

    # Load and format dataset
    dataset_path = str(ROOT / config["dataset"]["path"])
    raw_data = load_dataset(dataset_path)
    formatted_data = format_sharegpt_to_chat(raw_data)

    # Split into train/val
    val_split = config["dataset"].get("validation_split", 0.1)
    split_idx = int(len(formatted_data) * (1 - val_split))
    train_data = formatted_data[:split_idx]
    val_data = formatted_data[split_idx:]
    logger.info("Train: %d examples, Val: %d examples", len(train_data), len(val_data))

    # Format with system prompt
    system_prompt = config["dataset"].get("prompt_template", "You are AURA, an AI fashion stylist.")

    def format_example(example):
        messages = [{"role": "system", "content": system_prompt}] + example["messages"]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        return {"text": text}

    from datasets import Dataset

    train_dataset = Dataset.from_list(train_data).map(format_example)
    val_dataset = Dataset.from_list(val_data).map(format_example) if val_data else None

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=train_config.get("epochs", 3),
        per_device_train_batch_size=train_config.get("per_device_batch_size", 2),
        gradient_accumulation_steps=train_config.get("gradient_accumulation_steps", 4),
        learning_rate=train_config.get("learning_rate", 2e-4),
        warmup_ratio=train_config.get("warmup_ratio", 0.1),
        weight_decay=train_config.get("weight_decay", 0.01),
        max_grad_norm=train_config.get("max_grad_norm", 1.0),
        fp16=train_config.get("fp16", True),
        optim=train_config.get("optim", "adamw_8bit"),
        lr_scheduler_type=train_config.get("lr_scheduler_type", "cosine"),
        logging_steps=train_config.get("logging_steps", 10),
        save_steps=train_config.get("save_steps", 100),
        eval_steps=train_config.get("eval_steps", 50),
        evaluation_strategy="steps" if val_dataset else "no",
        seed=train_config.get("seed", 42),
        report_to="none",
    )

    # Train
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        args=training_args,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
    )

    logger.info("Starting training...")
    trainer.train()

    # Save
    logger.info("Saving model to %s", output_dir)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Push to Hub (optional)
    if config["output"].get("push_to_hub", False):
        hub_id = config["output"].get("hub_model_id")
        if hub_id:
            logger.info("Pushing to HuggingFace Hub: %s", hub_id)
            model.push_to_hub(hub_id)
            tokenizer.push_to_hub(hub_id)

    logger.info("Finetuning complete! ✅")


def main():
    parser = argparse.ArgumentParser(description="AURA Fashion VLM Finetuning")
    parser.add_argument("--config", default="training/configs/fashion_vlm.yaml", help="Training config YAML")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without training")
    args = parser.parse_args()

    config_path = str(ROOT / args.config)
    config = load_config(config_path)
    logger.info("Config loaded: %s", config_path)

    if args.dry_run:
        dataset_path = str(ROOT / config["dataset"]["path"])
        data = load_dataset(dataset_path)
        formatted = format_sharegpt_to_chat(data)
        logger.info("Dry run: %d examples would be used for training", len(formatted))
        logger.info("Model: %s, LoRA rank: %d", config["model"]["name"], config["lora"]["rank"])
        return

    finetune(config)


if __name__ == "__main__":
    main()
