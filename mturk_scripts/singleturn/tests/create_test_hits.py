"""
Script to create new valid hits in sandbox environment without adding more data to Tables.

New blobs may be created if any hit is submitted.

All hits will have turn type "test_hit", stored in field RequesterAnnotation.
Use corresponding remove_test_hits.py to eliminate all created hits, regardless of their
review status.
"""
import dotenv
import os
import sys

from typing import Any, Dict

# Project root
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# Load dotenv before project imports
dotenv.load_dotenv(
    os.path.join(os.path.dirname(__file__), '..', '.env'))

import logger  # noqa: E402

from hit_manager import HITManager  # noqa: E402
from singleturn.builder_template_renderer import BuilderTemplateRenderer  # noqa: E402
from singleturn.singleturn_games_storage import IgluSingleTurnGameStorage  # noqa: E402
from utils import read_config  # noqa: E402

_LOGGER = logger.get_logger(__name__)


def main():

    config = read_config("sandbox", config_filepath='../env_configs.json')
    # Create hits without qualifiers
    if 'qualification_type_id' in config:
        config.pop('qualification_type_id')

    config['azure_connection_str'] = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    config['azure_sas'] = os.getenv('AZURE_STORAGE_SAS')
    config['aws_access_key'] = os.getenv("AWS_ACCESS_KEY_ID_LIT")
    config['aws_secret_key'] = os.getenv("AWS_SECRET_ACCESS_KEY_LIT")

    hit_count = 3

    with IgluSingleTurnGameStorage(**config) as game_storage:
        turn_type = 'builder-normal'
        open_turns = game_storage.get_open_turns(turn_type, hit_count)
        _LOGGER.info(f"Creating hits for turns {len(open_turns)}")

        renderer = BuilderTemplateRenderer('test_data/no_write_builder_normal.xml')
        hit_manager = HITManager(**config)

        for open_turn in open_turns:
            template = renderer.render_template_from_turn(config['azure_sas'], open_turn)
            hit_type = 'test_hit'
            new_hit_id = hit_manager.create_hit(template, hit_type=hit_type, **config)
            _LOGGER.info(f'Hit created {new_hit_id}')


if __name__ == '__main__':
    main()
