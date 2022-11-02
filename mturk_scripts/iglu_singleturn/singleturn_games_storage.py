
from typing import List
import logger
import random

from azure.data.tables import TableServiceClient, TableClient
from azure.storage.blob import ContainerClient

_LOGGER = logger.get_logger(__name__)


# TODO the idea is that this class abstracts what needs to be "stored" to keep
# track of a turn. We are not using it much now, and it could definitely change.
class Turn:
    def __init__(self, game_id, starting_world_id, builder_data_path_in_blob,
                 initial_game_id_blob, screenshot_step_view, screenshot_step_in_blob) -> None:
        self.game_id = game_id
        self.turn_type = None
        self.builder_data_path_in_blob = builder_data_path_in_blob
        self.initial_game_id_blob = initial_game_id_blob
        self.open_hits = []
        self.starting_world_id = starting_world_id
        # TODO Do we need this?
        self.screenshot_step_view = screenshot_step_view
        self.screenshot_step_in_blob = screenshot_step_in_blob


class IgluSingleTurnGameStorage:
    """Abstraction of storage data structures for single turn games.

    This class is a context manager, use inside a with statement.
    >>> with IgluSingleTurnGameStorage("hitTableName", "connectionStr") as game_storage:
    ...     create_new_games(self, starting_structure_ids)
    """

    def __init__(self, hits_table_name: str, azure_connection_str: str,
                 starting_structures_container_name: str = 'mturk-vw',
                 starting_structures_blob_prefix: str = 'test-builder-data',
                 **kwargs) -> None:
        super().__init__()

        self.azure_connection_str = azure_connection_str

        self.hits_table_name = hits_table_name
        self.table_client = None

        self.starting_structures_container_name = starting_structures_container_name
        self.container_client = None

        self.starting_structures_blob_prefix = starting_structures_blob_prefix
        self.blob_service_client = None

        self.running_games = {}

        self.create_tables_if_not_exists()

        # Game ids are sequential numbers. We store the
        self.current_last_game_id = None

    def __enter__(self):
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

    def create_tables_if_not_exists(self) -> None:
        """Creates game and hits tables in Azure tables if they don't exist."""

        with TableServiceClient.from_connection_string(
                self.azure_connection_str) as table_service_client:
            table_service_client.create_table_if_not_exists(table_name=self.hits_table_name)

    def get_last_game_index(self) -> int:
        """Returns the maximum game index, stored in column PartitionKey of the hits table.

        Game id is game-<game number>, except some incorrect rows.

        Returns:
            The highest integer in the game ids of the hit table for entries created before
            the current date.
        """

        # TODO: question, why is it necessary to filter by date here?
        query_filter = "HitType eq 'builder-normal'"
        entities = list(self.table_client.query_entities(
            query_filter=query_filter,
            select=['PartitionKey', 'RowKey', 'Timestamp']))

        if len(entities) < 1:
            return 0

        game_indexes = []
        for row in entities:
            game_id = row['PartitionKey']
            # Extracting only the game index.
            game_indexes.append(int(game_id.split('-')[1]) if '-' in game_id else int(game_id))

        return max(game_indexes)

    def select_start_worlds_ids(self, game_count: int = 30) -> List[str]:
        """
        Creates @game_count new games selecting random start target structures.

        Start target structures are stored in a blob storage container.

        For each new game, an entry will be saved into the games table, marked as started but
        not finished. The attempt or turn id will be the following number to the maximum existing
        turn. If the game has already 5 turns created, the new turn will be 6, regardless of
        the state of previous turns.

        Raises:
            ValueError if the function is called outside a context manager or if @game_count
            is less than 1.
        """
        if self.table_client is None:
            raise ValueError("IgluSingleTurnGameStorage used outside a with statement!")

        if game_count <= 0:
            raise ValueError("Not creating any Hits as games count is less than 1")

        container_client = ContainerClient.from_connection_string(
            self.azure_connection_str,
            self.starting_structures_container_name)
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

    def get_open_turn(self, game_id, starting_world_id):
        starting_world_blob_path = starting_world_id.split('/')[0]
        initial_game_id_blob = starting_world_id.split('/')[1]

        screenshot_step_in_blob = starting_world_id.split('/')[2]
        screenshot_step_view = screenshot_step_in_blob + "_north"

        new_turn = Turn(
            game_id, starting_world_id, starting_world_blob_path,
            initial_game_id_blob, screenshot_step_view, screenshot_step_in_blob)
        return new_turn
