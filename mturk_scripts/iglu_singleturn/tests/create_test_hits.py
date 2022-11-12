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

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

# Load dotenv before project imports
dotenv.load_dotenv(
    os.path.join(os.path.dirname(__file__), '..', '.env'))

import logger  # noqa: E402

from hit_manager import HITManager, BuilderTemplateRenderer  # noqa: E402
from singleturn_games_storage import IgluSingleTurnGameStorage  # noqa: E402
from utils import read_config  # noqa: E402

_LOGGER = logger.get_logger(__name__)


def builder_normal_template_kwargs(azure_sas, open_turn) -> Dict[str, Any]:
    """Creates a dictionary with necessary keys to render a normal_builder template.
    """
    return {
        "game_id": open_turn.game_id,
        "azure_sas": azure_sas,
        "initialized_world_game_id": open_turn.starting_world_id,
        "builder_data_path": open_turn.initial_game_blob_path,
        "step_screenshot_view": open_turn.screenshot_step_view,
        "step_screenshot_path": open_turn.starting_step,
    }


def main():

    config = read_config("sandbox")
    # Create hits without qualifiers
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
