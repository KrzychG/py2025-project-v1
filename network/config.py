import yaml
import os

def load_config(path: str = None) -> dict:
    if path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "config.yaml")

    with open(path, "r") as f:
        return yaml.safe_load(f)