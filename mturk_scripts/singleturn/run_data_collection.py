"""Create HITs for a single turn of builder role.

Continuously monitor and approve submitted assignments for created hits. Script
runs until there are no more open hits, i.e., hits that are not expired and that
are not already reviewed. It can be terminated prematurely with a kill signal,
in which case the new submitted assignments can be retrieved and approved if
the script is executed again, before the assignment expires.
"""

import argparse
import sys
import dotenv
import os
import time

# Project root
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from hit_manager import HITManager
from singleturn.builder_template_renderer import BuilderTemplateRenderer
from singleturn.singleturn_games_storage import SingleTurnGameStorage, SingleTurnDatasetTurn
from common import utils, logger

dotenv.load_dotenv()

_LOGGER = logger.get_logger(__name__)
logger.set_logger_level('azure')


def read_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--config', choices=['production', 'sandbox'], default='sandbox',
                        help='Environment to use for operations')

    parser.add_argument('--config_filepath', type=str, default='env_config.json',
                        help='Path to json file with environment configuration')

    parser.add_argument("--hit_count", type=int, required=True,
                        help="Total number of accepted HITs to be created")

    parser.add_argument("--template_filepath", type=str, default='templates/builder_normal.xml',
                        help="Path to the file with the xml/html template to render for each HIT.")

    return parser.parse_args()


def validate_assignment(assignment_dict) -> bool:
    """Asserts whether the assignment should be approved or not.

    The HIT manager will receive the assignment, parse the response and store it
    into the 'Answer' key of `assignment_dict`. The structure of the dictionary
    under Answer is dependant on the structure of the layout used to create the
    HIT.

    Additionally, this function can apply changes to the assignment_dict. The same
    reference will be returned by `HitManager.complete_open_assignments()`.

    Args:
        assignment_dict (dictionary): A dictionary representation of the
            assignment, with at least key 'Answer'.

    Returns:
        bool: Whether the assignment should be approved.
    """
    # Extract input instruction from answer
    input_instruction = None
    answer_list = []
    if not type(assignment_dict['Answer']) is list:
        # One field found in HIT layout
        answer_list = [assignment_dict['Answer']]
    else:
        # Multiple fields in HIT layout
        answer_list = assignment_dict['Answer']

    for answer_field in answer_list:
        if answer_field['QuestionIdentifier'] == 'InputInstructionSingleTurn':
            input_instruction = answer_field['FreeText']
            break

    # Save the relevant fields for easier access later
    assignment_dict['InputInstruction'] = input_instruction

    qualified = False
    if (input_instruction is not None and
            len(input_instruction.strip()) > 5 and
            utils.is_english(input_instruction)):
        qualified = True
    return qualified


def run_hits(hit_count, template_filepath, config, seconds_to_wait=60):

    with SingleTurnGameStorage(**config) as game_storage:
        turn_type = 'builder-normal'
        open_turns = game_storage.get_open_turns(turn_type, hit_count)
        _LOGGER.info(f"Creating hits for turns {len(open_turns)}")

        renderer = BuilderTemplateRenderer(template_filepath)
        hit_manager = HITManager(
            templates_dirname='templates', verification_function=validate_assignment, **config)

        for open_turn in open_turns:
            template = renderer.render_template_from_turn(config['azure_sas'], open_turn)
            new_hit_id = hit_manager.create_hit(template, hit_type=turn_type, **config)
            _LOGGER.info(f"Hit created {new_hit_id}")
            open_turn.set_hit_id(new_hit_id)

            game_storage.save_new_turn(open_turn)

        _LOGGER.info("HITs created successfully, waiting for assignments submissions")

        wait_for_assignments(config, seconds_to_wait, game_storage, turn_type, hit_manager)


def wait_for_assignments(config, seconds_to_wait, game_storage, turn_type, hit_manager):
    while True:
        # Look for further open hits
        open_hit_ids = hit_manager.get_open_hit_ids(hit_type=turn_type)
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
    config = utils.read_config(args.config, config_filepath=args.config_filepath)

    config['azure_connection_str'] = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    config['azure_sas'] = os.getenv('AZURE_STORAGE_SAS')
    config['aws_access_key'] = os.getenv("AWS_ACCESS_KEY_ID_LIT")
    config['aws_secret_key'] = os.getenv("AWS_SECRET_ACCESS_KEY_LIT")

    run_hits(args.hit_count, args.template_filepath, config)


if __name__ == '__main__':
    main()
