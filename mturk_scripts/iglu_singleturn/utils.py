import json
import os
from typing import Any, Dict, Optional


def read_config(environment: str, config_filepath: Optional[str] = None) -> Dict[str, Any]:
    if config_filepath is None:
        config_filepath = os.path.join(os.path.dirname(__file__), 'env_configs.json')
    with open(config_filepath, 'r') as config_file:
        config = json.load(config_file)
    return config[environment]
