import os
import random
import sys

from azure.core.exceptions import ResourceExistsError
from typing import Any, Dict, List, Optional, Tuple

# Project root
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

import logger
from game_storage import AzureGameStorage
from turn import Turn

_LOGGER = logger.get_logger(__name__)


class SingleTurnDatasetTurn(Turn):
    """Class that acts as buffer between the database tables and the mturk scripts.

    Contains all the data necessary to keep track of a turn, and maps its attributes
    into the database schema.
    """
    def __init__(
            self, game_id: str, turn_type: str,
            initialized_structure_id: str,
            starting_world_blob_path: str, starting_world_blob_name: str,
            starting_step: str) -> None:
        """Create a new turn instance that has no hit assigned yet.

        Args:
            game_id (str): The identifier of the game and turn. Will be used to retrieve the
                turns from database.
            turn_type (str): A string to describe the turn. Will be used to retrieve the
                turns from database.
            initialized_structure_id (str): Id of the target structure for the original game from
                where this turn was created.
            starting_world_blob_path (str): Path inside container with the initial world file.
            starting_world_blob_name (str): Name of the blob with the initial world file, located
                inside starting_world_blob_path.
            starting_step (str): Step or episode number in game corresponding to initial
                world, i.e., previous turn.
        """
        # In singleturn, the game_id also identifies the turn.
        super().__init__(game_id, turn_type, initialized_structure_id)

        self.starting_world_blob_path = starting_world_blob_path
        self.starting_world_blob_name = starting_world_blob_name
        self.starting_step = starting_step

        # Path to a sample screenshot of the starting world
        self.screenshot_step_view = starting_step + "_north"

    @staticmethod
    def _add_legacy_keys(row: Dict[str, Any]):
        row['InstructionToExecute'] = 'NA'

    @classmethod
    def from_database_entry(cls, row: Dict[str, Any]):
        if 'InitializedWorldPath' in row:
            initial_world_path = row['InitializedWorldPath']
        elif 'InitializedWorld' in row:
            # From a different table, the screenshot path is saved instead of world path
            initial_world_path = row['InitializedWorld'].replace('.png', '')
        else:
            _LOGGER.error(f'Error reading initial world path from database entry '
                          f'for key {row["PartitionKey"]}')
            return None

        _, starting_world_blob_path, starting_world_blob_name, starting_step = \
            cls._split_starting_world_path(initial_world_path)

        new_turn = cls(
            game_id=row["PartitionKey"],
            turn_type=row['HitType'],
            initialized_structure_id=row.get('InitializedWorldStructureId', None),
            starting_world_blob_path=starting_world_blob_path,
            starting_world_blob_name=starting_world_blob_name,
            starting_step=starting_step,
        )
        new_turn.set_hit_id(row['RowKey'])
        # These values are NA until HIT is completed
        new_turn.input_instructions = row.get('InputInstruction', 'NA')
        new_turn.is_qualified = row.get('IsHITQualified', 'NA')
        new_turn.worker_id = row.get('WorkerId', 'NA')

        # Path to blob where the player actions and resulting world description is
        # stored inside blobs. It is prefixed by the container name. Example:
        # mturk-single-turn/builder-data/actionHit/game-1/
        new_turn.result_blob_path = row.get('ActionDataPath', 'NA')
        return new_turn

    @staticmethod
    def _build_starting_world_path(container_name, blob_path, blob_name, step):
        # Example container_name="mturk-vw/", blob_path="builder-data"
        # blob_name="23-c161", step="step-4"
        return '/'.join([p.strip('/') for p in [
            container_name, blob_path, blob_name, step
        ]])

    @staticmethod
    def _split_starting_world_path(initial_world_path) -> Tuple[str, str, str, str]:
        # Example initial_world_path="mturk-vw/builder-data/34-c135/step-20"
        splitted_path = initial_world_path.split('/')
        if len(splitted_path) != 4:
            _LOGGER.error(f'Error parsing initial world path {initial_world_path} from database')
            return None

        return splitted_path

    def update_result_blob_path(
            self, container_name: str, blob_subpaths: str = 'actionHit'):
        # Example result_container_name="mturk-single-turn", result_blob_path="builder-data"
        self.result_blob_path = '/'.join([p.strip('/') for p in [
            container_name, self.starting_world_blob_path, blob_subpaths, self.game_id]
        ])

    def to_database_entry(self, starting_structures_container_name: str) -> Dict[str, Any]:
        if self.hit_id is None:
            _LOGGER.warning(f"Attempting to save turn without created hit for game {self.game_id}")
            return

        starting_world_path = self._build_starting_world_path(
            starting_structures_container_name, self.starting_world_blob_path,
            self.starting_world_blob_name, self.starting_step)

        new_entry = {
            "PartitionKey": self.game_id,
            "RowKey": self.hit_id,
            "HitType": self.turn_type,
            "IsHITQualified": self.is_qualified or "NA",
            "WorkerId": self.worker_id or "NA",
            "InitializedWorldStructureId": self.initialized_structure_id,
            "InitializedWorldPath": starting_world_path,
            "ActionDataPath": self.result_blob_path or "NA",
            "InputInstruction": self.input_instructions or "NA",
        }
        return new_entry


class IgluSingleTurnGameStorage(AzureGameStorage):
    """Abstraction of storage data structures for single turn games.

    This class is a context manager, use inside a with statement.
    >>> with IgluSingleTurnGameStorage("hitTableName", "connectionStr") as game_storage:
    ...     create_new_games(self, starting_structure_ids)
    """

    def get_last_game_index(self, turn_type: str = 'builder-normal') -> int:
        """Returns the maximum game index, stored in column PartitionKey of the hits table.

        Game id is game-<game number>, except some incorrect rows.

        Returns:
            The highest integer in the game ids of the hit table for entries created before
            the current date.
        """
        if self.table_client is None:
            raise ValueError("IgluSingleTurnGameStorage used outside a with statement!")

        query_filter = f"HitType eq '{turn_type}'"
        entities = list(self.table_client.query_entities(
            query_filter=query_filter, select=['PartitionKey', 'RowKey']))

        if len(entities) < 1:
            return 0

        game_indexes = []
        for row in entities:
            game_id = row['PartitionKey']
            # Extracting only the game index.
            game_indexes.append(self.get_index_from_game_id(game_id))

        return max(game_indexes)

    @staticmethod
    def get_index_from_game_id(game_id_or_game_index):
        if '-' in game_id_or_game_index:
            return int(game_id_or_game_index.split('-')[-1])
        try:
            return int(game_id_or_game_index)
        except ValueError:
            return 0

    @staticmethod
    def game_id_from_game_index(game_id_or_game_index):
        if not isinstance(game_id_or_game_index, int) and 'game-' in game_id_or_game_index:
            return game_id_or_game_index
        return f'game-{game_id_or_game_index}'

    def select_start_worlds_ids(self, game_count: int = 30) -> List[str]:
        """
        Searches @game_count new games selecting random start target structures.

        Start target structures are stored in a blob storage container.

        For each new game, an entry will be saved into the games table, marked as started but
        not finished. The attempt or turn id will be the following number to the maximum existing
        turn. If the game has already 5 turns created, the new turn will be 6, regardless of
        the state of previous turns.

        Raises:
            ValueError if the function is called outside a context manager or if @game_count
            is less than 1.

        Returns:
            (List[str]) A list with the selected blobs to be used as starting worlds.
        """
        if self.table_client is None:
            raise ValueError("IgluSingleTurnGameStorage used outside a with statement!")

        if game_count <= 0:
            raise ValueError("Not creating any Hits as games count is less than 1")

        container_client = self.create_container_client()
        blob_names = container_client.list_blobs(
            name_starts_with=self.starting_structures_blob_prefix)
        blob_list = []

        # Selecting the starting structures, or intermediate worlds, for workers to perform actions
        for blob in blob_names:
            # There are only two types of blobs, i) xml files with game state for each
            # step, and ii) png screenshots. Filter out the images and keep the xml files only.
            if ".png" not in blob.name:
                blob_list.append(blob.name)

        _LOGGER.debug(f"{len(blob_list)} candidate starting structures found.")
        # Selecting worlds at random to initialize
        random_starting_worlds = random.sample(blob_list, game_count)

        return random_starting_worlds

    def get_turns_from_open_game(
            self, game_id: str, turn_type: str, starting_world_path: str):

        # starting_world_paths looks like 'test-builder-data/1-c70/step-2'
        starting_world_blob_path = starting_world_path.split('/')[0]
        starting_world_blob_name = starting_world_path.split('/')[1]

        starting_step = starting_world_path.split('/')[2]

        if '-' in starting_world_blob_name:
            initialized_structure_id = starting_world_blob_name.split('-')[1]
        else:
            initialized_structure_id = starting_world_blob_name
        new_turn = SingleTurnDatasetTurn(
            game_id, turn_type,
            initialized_structure_id=initialized_structure_id,
            starting_world_blob_path=starting_world_blob_path,
            starting_world_blob_name=starting_world_blob_name,
            starting_step=starting_step)
        return new_turn

    def get_open_turns(self, turn_type: str, number_of_turns: int = 1) -> List[Turn]:
        """
        Creates new turns/games for randomly selected starting structures.

        The game ids will be creating using sequential numbers and the method
        `self.game_id_from_game_index`

        Args:
            number_of_turns (int): the number of turns to return

        Returns:
            list: a list with the new open Turn instances. Open turns do not have
            HITs associated.
        """
        next_game_index = self.get_last_game_index() + 1
        starting_world_ids = self.select_start_worlds_ids(game_count=number_of_turns)
        if len(starting_world_ids) != number_of_turns:
            _LOGGER.error("Error retrieving data from container")
            return 1

        open_turns = []
        for starting_world_id in starting_world_ids:
            next_game_id = self.game_id_from_game_index(next_game_index)
            open_turns.append(
                self.get_turns_from_open_game(next_game_id, turn_type, starting_world_id))
            next_game_index += 1
        return open_turns

    def retrieve_turn_entity(self, key: str, column_name: str = 'RowKey',
                             qualified_value: bool = False) -> Optional[Dict[str, Any]]:
        query_filter = f"{column_name} eq '{key}'"
        if qualified_value:
            query_filter += "and IsHITQualified eq true"
        try:
            entity = self.table_client.query_entities(
                query_filter=query_filter,
                results_per_page=1).next()
            return entity

        except (ResourceExistsError, StopIteration):
            _LOGGER.warning(f'No turn with {column_name} = {key} found on table')
