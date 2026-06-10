
import re
import json
import torch
from typing import List 
from common.logger import logger
from orchestrator.model.schema import chatModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

class QwenModelAgent:
    
    def __init__(self, model_name: str = "models/Qwen2.5-1.5B-Instruct"):
        logger.info(f"Loading {model_name}...")
        
        bnb_config = BitsAndBytesConfig(
                                            load_in_4bit=True,
                                            bnb_4bit_compute_dtype=torch.float16,
                                            bnb_4bit_quant_type="nf4",
                                            bnb_4bit_use_double_quant=True,
                                        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(
                                                            model_name,
                                                            trust_remote_code=True,
                                                            padding_side="left"
                                                        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16,
        )
        
        self.model.eval()
        logger.info("Model loaded. VRAM used: ~%.2f GB", torch.cuda.memory_allocated() / 1e9)
    
    def chat(self, messages: List[chatModel], tools: list = None, max_new_tokens: int = 512) -> str:
        """Generate response from messages. Returns raw text (may contain <tool_call>)."""
        messages = [ m if isinstance(m, chatModel) else chatModel(**m) for m in messages]

        text = self.tokenizer.apply_chat_template(
                                                        messages,
                                                        tools=tools,
                                                        tokenize=False,
                                                        add_generation_prompt=True
                                                    )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        
        return self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], 
            skip_special_tokens=True
        )
    
    def parse_tool_calls(self, text: str) -> list[dict]:
        """
        Extract all tool calls from model response.
        Qwen 2.5 format: <tool_call>{"name": "...", "arguments": {...}}</tool_call>
        Returns list of {"name": str, "arguments": dict}
        """
        calls = []
        # Find all tool_call blocks
        for match in re.finditer(r'<tool_call>(.*?)</tool_call>', text, re.DOTALL):
            try:
                data = json.loads(match.group(1).strip())
                # Normalize keys
                name = data.get("name") or data.get("function", {}).get("name")
                args = data.get("arguments") or data.get("parameters") or data.get("function", {}).get("arguments", {})
                if name:
                    calls.append({"name": name, "arguments": args})
            except json.JSONDecodeError:
                continue
        
        if not calls:
            try:
                # Look for standalone JSON that looks like a tool call
                for match in re.finditer(r'\{[^{}]*"name"[^{}]*\}', text):
                    data = json.loads(match.group(0))
                    if "name" in data:
                        calls.append({
                            "name": data["name"],
                            "arguments": data.get("arguments", data.get("params", {}))
                        })
            except:
                pass
        
        return calls
    
