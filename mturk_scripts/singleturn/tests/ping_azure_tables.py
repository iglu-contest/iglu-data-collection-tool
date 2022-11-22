"""
Query azure resources and retrieve random existing turns from database.

The script is read-only and meant to test the access to tables.
"""

import argparse
import dotenv
import os
import sys

# Project root
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import logger  # noqa: E402
from singleturn.singleturn_games_storage import (
    IgluSingleTurnGameStorage, SingleTurnDatasetTurn)  # noqa: E402
from utils import read_config  # noqa: E402

# Load dotenv before project imports
dotenv.load_dotenv(
    os.path.join(os.path.dirname(__file__), '..', '.env'))

_LOGGER = logger.get_logger(__name__)


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
       '--config',
       help='Environment to use for operations',
       choices=['production', 'sandbox'],
       default='sandbox',
    )
    return parser.parse_args()


def main():
    args = read_args()
    connection_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    config = read_config(args.config, config_filepath='../env_configs.json')

    turn_type = 'builder-normal'
    with IgluSingleTurnGameStorage(
            config['hits_table_name'], connection_str, config['starting_structures_container_name'],
            config['starting_structures_blob_prefix']) as game_storage:

        random_row = game_storage.retrieve_turn_entity(
            key=turn_type, column_name='HitType', qualified_value=True)

        _LOGGER.info("Random turn row successfully retrieved")

        new_turn = SingleTurnDatasetTurn.from_database_entry(random_row)
        generated_row = new_turn.to_database_entry(game_storage.starting_structures_container_name)

        _LOGGER.info("Turn created from database row")

        # Compare initial and final encodings
        for generated_key, generated_value in generated_row.items():
            if generated_key not in random_row:
                _LOGGER.warning(f'Key {generated_key} was not in original row')
                continue
            original_value = random_row[generated_key]
            if original_value != generated_value:
                _LOGGER.warning(
                    f'Incorrect value for {generated_key}. Expected {original_value}, '
                    f'Obtained {generated_value}')

        if args.config == 'sandbox':
            _LOGGER.info(f"Upserting row with RowKey {new_turn.hit_id}")
            # Attempt to upsert row adding a space to the instruction.
            new_turn.input_instructions += '.'

            game_storage.upsert_turn(new_turn)

            # Re-query the table
            retrieved_row = game_storage.retrieve_turn_entity(
                key=new_turn.hit_id, column_name='RowKey', qualified_value=True)

            recreated_turn = SingleTurnDatasetTurn.from_database_entry(retrieved_row)
            if recreated_turn.input_instructions != new_turn.input_instructions:
                _LOGGER.error(
                    f"Upserting entity did not replace field. Expected: "
                    f"{new_turn.input_instructions} - Received {recreated_turn.input_instructions}")
            else:
                _LOGGER.info("Entry successfully upserted!")


if __name__ == '__main__':
    main()
