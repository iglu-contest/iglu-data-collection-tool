from typing import Dict, List, Optional, Any
from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableServiceClient, TableClient, UpdateMode
from azure.storage.blob import ContainerClient


from turn import Turn
from common import logger

_LOGGER = logger.get_logger(__name__)
logger.set_logger_level('azure')


class AzureGameStorage:
    """Abstraction of data structures to save game data in Azure tables and containers.

    This class is a context manager, use inside a with statement.
    >>> with AzureGameStorage(hits_table_name, azure_connection_string) as game_storage:
    ...     create_new_games(self, starting_structure_ids)

    Data is saved in two parts:
    * An Azure table contain HIT data.
    * An Azure container saves the initial and target structures, and VoxelWorld data.
    """

    def __init__(self, hits_table_name: str, azure_connection_str: str,
                 starting_structures_container_name: str,
                 starting_structures_blob_prefix: str,
                 **kwargs) -> None:

        self.azure_connection_str = azure_connection_str

        self.hits_table_name = hits_table_name
        self.table_client = None

        self.starting_structures_container_name = starting_structures_container_name
        self.container_client = None

        self.starting_structures_blob_prefix = starting_structures_blob_prefix
        self.blob_service_client = None

    def __enter__(self):
        with TableServiceClient.from_connection_string(
                self.azure_connection_str) as table_service_client:
            _ = table_service_client.create_table_if_not_exists(
                table_name=self.hits_table_name)

        self.table_client = TableClient.from_connection_string(
            conn_str=self.azure_connection_str, table_name=self.hits_table_name)
        self.table_client.__enter__()
        _LOGGER.debug(f"Entering {self.__class__.__name__} context anc closing TableClient.")
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.table_client.__exit__(
            exception_type, exception_value, traceback)
        _LOGGER.debug(f"Leaving {self.__class__.__name__} context and closing TableClient.")
        self.table_client = None
        return None

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
        raise NotImplementedError

    def create_container_client(self):
        return ContainerClient.from_connection_string(
            self.azure_connection_str,
            self.starting_structures_container_name)

    def get_turns_from_open_game(
            self, game_id: str, turn_type: str, starting_world_path: str) -> Turn:
        raise NotImplementedError

    def get_open_turns(self, turn_type: str, number_of_turns: int = 1) -> List[Turn]:
        """
        Creates new turns/games for selected starting structures.

        Args:
            number_of_turns (int): the number of turns to return

        Returns:
            list: a list with the new open Turn instances. Open turns do not have
            HITs associated.
        """
        raise NotImplementedError

    def retrieve_turn_entity(
            self, key: str, column_name: str = 'RowKey') -> Optional[Dict[str, Any]]:
        query_filter = f"{column_name} eq '{key}'"
        try:
            entity = self.table_client.query_entities(
                query_filter=query_filter,
                results_per_page=1).next()
            return entity

        except (ResourceExistsError, StopIteration):
            _LOGGER.warning(f'No turn with {column_name} = {key} found on table')

    def save_new_turn(self, turn: Turn):
        if turn.hit_id is None:
            _LOGGER.warning(f"Attempting to save turn without created hit for game {turn.game_id}")
            return

        entity = turn.to_database_entry(self.starting_structures_container_name)

        try:
            self.table_client.create_entity(entity)
            _LOGGER.debug(f'Successfully inserted new turn {turn.hit_id} for game {turn.game_id}.')
        except ResourceExistsError:
            _LOGGER.error(f"Turn entry {turn.hit_id} for game {turn.game_id} already exists")

    def upsert_turn(self, turn: Turn):
        if turn.hit_id is None:
            _LOGGER.warning(
                f"Attempting to upsert turn without created hit for game {turn.game_id}")
            return
        entity = turn.to_database_entry(self.starting_structures_container_name)
        self.table_client.upsert_entity(mode=UpdateMode.MERGE, entity=entity)