"""
Fine-tuning entry points: LoRA SFT on chat-format jsonl → adapter on disk.
"""

from pathlib import Path


def run_tuning(jsonl_path: Path, base_model: str, out_dir: Path, epochs: int = 1) -> None:
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    # Load the messages list from each line, drop the split tag if present.
    dataset = load_dataset("json", data_files=str(jsonl_path), split="train")
    if "messages" not in dataset.column_names:
        # Old flat shape; nothing to do (messages already at top level).
        pass

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(base_model)
    model.config.use_cache = False

    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM")
    config = SFTConfig(
        output_dir=str(out_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=4,
        logging_steps=10,
        save_strategy="no",
        report_to=[],
        max_length=1024,
    )
    trainer = SFTTrainer(model=model, args=config, train_dataset=dataset, peft_config=lora)
    trainer.train()
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
