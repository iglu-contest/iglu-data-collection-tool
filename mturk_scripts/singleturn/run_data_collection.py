"""Create HITs for a single turn of builder role.

Continuously monitor and approve submitted assignments for created hits. Script
runs until there are no more open hits, i.e., hits that are not expired and that
are not already reviewed. It can be terminated prematurely with a kill signal,
in which case the new submitted assignments can be retrieved and approved if
the script is executed again, before the assignment expires.
"""

import argparse
import dotenv
import os
import time
from typing import Dict, Any

import logger

from hit_manager import HITManager, BuilderTemplateRenderer
from singleturn.singleturn_games_storage import IgluSingleTurnGameStorage, SingleTurnDatasetTurn
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

    parser.add_argument(
       "--hit_count",
       help="Total number of accepted HITs to be created",
       type=int,
       required=True,
    )

    parser.add_argument(
       "--template_filepath",
       help="Path to the file with the xml or html template to render for each HIT.",
       type=str,
       default='templates/normal_builder.xml',
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
        "step_screenshot_path": open_turn.starting_step,
    }


def run_hits(hit_count, template_filepath, config, seconds_to_wait=60):

    with IgluSingleTurnGameStorage(**config) as game_storage:
        turn_type = 'builder-normal'
        open_turns = game_storage.get_open_turns(turn_type, hit_count)
        _LOGGER.info(f"Creating hits for turns {len(open_turns)}")

        renderer = BuilderTemplateRenderer(template_filepath)
        hit_manager = HITManager(templates_dirname='templates', **config)

        for open_turn in open_turns:
            template = renderer.render_template_from_turn(config['azure_sas'], open_turn)
            new_hit_id = hit_manager.create_hit(template, hit_type=turn_type, **config)
            _LOGGER.info(f"Hit created {new_hit_id}")
            open_turn.set_hit_id(new_hit_id)

            game_storage.save_new_turn(open_turn)

        _LOGGER.info("HITs created successfully, waiting for assignments submissions")
        while True:
            # Look for further open hits
            open_hit_ids = game_storage.get_open_hit_ids(hit_type=turn_type)
            if len(open_hit_ids) == 0:
                _LOGGER.warning("No more non-expired hits to review for this type of turn. "
                                "Exiting script.")
                break

            # Look for new submitted assignments and review them.
            completed_assignments = hit_manager.complete_open_assignments(open_hit_ids)

            # If there were assignments completed in the previous function, save the
            # results into the game storage.
            if len(completed_assignments) == 0:
                _LOGGER.info(f"No new assignments, waiting for {seconds_to_wait} seconds.")
                time.sleep(seconds_to_wait)
                continue

            for hit_id, assignment_answers in completed_assignments.items():

                entity = game_storage.retrieve_turn_entity(hit_id)
                if entity is None:
                    _LOGGER.error(f'No turn found for HIT {hit_id}')

                hit_turn = SingleTurnDatasetTurn.from_database_entry(entity)

                # Storing action data path
                hit_turn.update_result_blob_path(
                    container_name=config['result_structures_container_name'],
                    blob_subpaths='actionHit')

                # Update turn with assignment values after processing Hit
                hit_turn.input_instructions = assignment_answers['InputInstruction']
                hit_turn.is_qualified = assignment_answers['IsHITQualified']
                hit_turn.worker_id = assignment_answers['WorkerId']

                game_storage.upsert_turn(hit_turn)
                _LOGGER.info(f"Assignment for hit {hit_id} successfully saved.")


def main():

    args = read_args()
    config = read_config(args.config, config_filepath='./env_configs.json')

    config['azure_connection_str'] = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    config['azure_sas'] = os.getenv('AZURE_STORAGE_SAS')
    config['aws_access_key'] = os.getenv("AWS_ACCESS_KEY_ID_LIT")
    config['aws_secret_key'] = os.getenv("AWS_SECRET_ACCESS_KEY_LIT")

    run_hits(args.hit_count, args.template_filepath, config)


if __name__ == '__main__':
    main()
