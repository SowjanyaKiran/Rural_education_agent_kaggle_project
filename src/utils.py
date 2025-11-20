# src/utils.py
import os
import json
import logging
from typing import Any


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rural-ed-agent")




def load_json(path: str) -> Any:
with open(path, "r", encoding="utf-8") as f:
return json.load(f)




def save_json(path: str, data: Any):
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
json.dump(data, f, ensure_ascii=False, indent=2)