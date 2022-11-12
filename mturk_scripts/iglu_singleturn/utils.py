import json
import langdetect
import os
import re

from typing import Any, Dict, Optional


def read_config(environment: str, config_filepath: Optional[str] = None) -> Dict[str, Any]:
    if config_filepath is None:
        config_filepath = os.path.join(os.path.dirname(__file__), 'env_configs.json')
    with open(config_filepath, 'r') as config_file:
        config = json.load(config_file)
    return config[environment]


def is_english(input: str) -> bool:
    """Returns whether the input is probably correct English and not gibberish

    Args:
        input (str): the text to analyze

    Returns:
        bool: whether or not is English
    """
    return (input is not None and bool(re.match('^(?=.*[a-zA-Z])', input)) and
            langdetect.detect(input) == 'en')
