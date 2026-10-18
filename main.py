
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def convert(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {
            "true", "1", "yes", "on"
        }
    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # YAML configuration layer
    env_name = os.getenv("APP_ENV", "development")
    yaml_path = BASE_DIR / f"config.{env_name}.yaml"

    if yaml_path.exists():
        with open(yaml_path, encoding="utf-8") as f:
            config.update(yaml.safe_load(f) or {})

    # .env configuration layer
    env_values = dotenv_values(BASE_DIR / ".env")
    for key, value in env_values.items():
        if value is not None:
            key = key.lower()
            if key == "num_workers":
                key = "workers"
            config[key] = value

    # OS environment layer
    for key, value in os.environ.items():
        if key.startswith("APP_") and key != "APP_ENV":
            config[key[4:].lower()] = value

    # Query-string overrides have highest priority
    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip().lower()

        if key == "num_workers":
            key = "workers"

        if key in DEFAULTS:
            config[key] = value

    # Return only the five expected keys
    result = {
        key: convert(key, config[key])
        for key in DEFAULTS
    }
    result["api_key"] = "****"

    return result
