"""Create HITs for a single turn of architect or builder roles.


"""

import argparse
import os
from typing import Any, Dict
import dotenv

import logger

from hit_manager import HITManager
from singleturn_games_storage import IgluSingleTurnGameStorage
from utils import read_config

dotenv.load_dotenv()

_LOGGER = logger.get_logger(__name__)


def read_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
       '--config',
       help='Environment to use for operations',
       choices=['production', 'sandbox'],
       default='sandbox',
    )

    # TODO decide if accepted hits or just created hits.
    parser.add_argument(
       "--hit_count",
       help="Total number of accepted HITs to be created",
       type=int,
       required=True,
    )

    return parser.parse_args()


def builder_normal_template_kwargs(azure_sas, open_turn) -> Dict[str, Any]:
    """Creates a dictionary with necessary keys to render a normal_builder template.
    """
    return {
        "game_id": open_turn.game_id,
        "azure_sas": azure_sas,
        "initialized_world_game_id": open_turn.starting_world_id,
        "builder_data_path": open_turn.builder_data_path_in_blob,
        "step_screenshot_view": open_turn.screenshot_step_view,
        "step_screenshot_path": open_turn.screenshot_step_in_blob,
    }


def main():

    args = read_args()
    config = read_config(args.config)

    config['azure_connection_str'] = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    config['azure_sas'] = os.getenv('AZURE_STORAGE_SAS')
    config['aws_access_key'] = os.getenv("AWS_ACCESS_KEY_ID_LIT")
    config['aws_secret_key'] = os.getenv("AWS_SECRET_ACCESS_KEY_LIT")

    with IgluSingleTurnGameStorage(**config) as game_storage:
        next_game_id = game_storage.get_last_game_index() + 1
        starting_world_ids = game_storage.select_start_worlds_ids(game_count=args.hit_count)
        if len(starting_world_ids) != args.hit_count:
            _LOGGER.error("Error retrieving data from container")
            return 1

        # TODO evaluate here if this function should receive a turn_type.
        open_turns = [game_storage.get_open_turn(next_game_id, starting_world_id)
                      for starting_world_id in starting_world_ids]
        _LOGGER.info(f"Creating hits for turns {len(open_turns)}")

        hit_manager = HITManager(templates_dirname='templates', **config)
        turn_type = 'builder_normal'
        # TODO move this to different function?
        for open_turn in open_turns:
            template = hit_manager.create_template_given_type(
                turn_type,
                renderer_kwargs=builder_normal_template_kwargs(config['azure_sas'], open_turn))
            open_turn.turn_type = turn_type
            next_game_id += 1
            new_hit_id = hit_manager.create_hit(template, **config)
            _LOGGER.info(f"Hit created {new_hit_id}")
            open_turn.open_hits.append(new_hit_id)
            # TODO save new turn into game_storage

        while True:
            # TODO add the code to process the hits
            # For now, just delete the hits recently created.
            hit_to_delete = list(hit_manager.open_hits.keys())[0]
            del hit_manager.open_hits[hit_to_delete]
            # This would only work for submitted hits
            # hit_manager.delete_hit(hit_to_delete)

            if not hit_manager.has_open_hits():
                break


if __name__ == '__main__':
    main()
