from typing import Any, Dict


class Turn:
    """Class that acts as buffer between the database tables and the mturk scripts.

    Contains all the data necessary to keep track of a turn, and maps its attributes
    into the database schema.
    """
    def __init__(
            self, game_id: str, turn_type: str,
            initialized_structure_id: str) -> None:
        """Create a new turn instance that has no hit assigned yet.

        Args:
            game_id (str): The identifier of the game and turn. Will be used to retrieve the
                turns from database.
            turn_type (str): A string to describe the turn. Will be used to retrieve the
                turns from database.
            initialized_structure_id (str): Id of the target structure for the original game from
                where this turn was created.
        """
        # In singleturn, the game_id also identifies the turn.
        self.game_id = game_id
        self.turn_type = turn_type

        self.initialized_structure_id = initialized_structure_id

        # Values set after hit has been completed
        self.hit_id = None
        self.worker_id = None
        self.is_qualified = None
        self.result_blob_path = None
        self.input_instructions = None

    def set_hit_id(self, hit_id):
        self.hit_id = hit_id

    @classmethod
    def from_database_entry(cls, row: Dict[str, Any]):
        raise NotImplementedError

    def to_database_entry(self, starting_structures_container_name: str) -> Dict[str, Any]:
        raise NotImplementedError
