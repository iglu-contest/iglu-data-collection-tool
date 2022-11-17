"""
Query azure resources and retrieve random starting structures, stored in containers.

The script is read-only and meant to test the access to tables.
"""

import argparse
import dotenv
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

import logger  # noqa: E402
from singleturn_games_storage import IgluSingleTurnGameStorage  # noqa: E402
from utils import read_config  # noqa: E402

# Load dotenv before project imports
dotenv.load_dotenv(
    os.path.join(os.path.dirname(__file__), '..', '.env'))

_LOGGER = logger.get_logger(__name__)


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
       '--game_count',
       help='Total number games to query',
       type=int,
       default=30,
    )
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
    config = read_config(args.config, '../env_configs.json')

    with IgluSingleTurnGameStorage(
            config['hits_table_name'], connection_str, config['starting_structures_container_name'],
            config['starting_structures_blob_prefix']) as game_storage:

        random_seed_structures = game_storage.select_start_worlds_ids(game_count=10)
        if len(random_seed_structures) != 10:
            _LOGGER.error("Error retrieving initial structure ids")
        else:
            _LOGGER.info(f"{len(random_seed_structures)} initial structure ids correctly restored "
                         "from azure tables.")

        last_game_index = game_storage.get_last_game_index()
        if last_game_index == 0:
            _LOGGER.error("Error retrieving data from container")
        else:
            _LOGGER.info(f"Last game id {last_game_index} read from  container")


if __name__ == '__main__':
    main()
