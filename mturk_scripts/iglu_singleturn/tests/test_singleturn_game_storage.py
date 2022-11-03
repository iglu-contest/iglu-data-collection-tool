"""Test GameStorage functions with azure table clients mocked."""

import os
import unittest
from unittest import mock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from singleturn_games_storage import IgluSingleTurnGameStorage  # noqa: E402


@mock.patch("singleturn_games_storage.TableClient")
@mock.patch("singleturn_games_storage.TableServiceClient")
class TestIgluSingleTurnGameStorage(unittest.TestCase):

    HITS_TABLE_NAME: str = 'HitsTable'
    AZURE_CONNECTION_STR: str = 'some_hash_string'

    def mock_table_client_senvice_context_manager(
            self, table_client_service_class_mock: mock.MagicMock,
            table_client_service_mock: mock.MagicMock):
        """Mock method TableServiceClient().create_table_if_not_exists.

        For example, mock `table_service_client` instance in:
        >>> with TableServiceClient.from_connection_string("str") as table_service_client:
        ...     table_client = table_service_client.create_table_if_not_exists(...)
        where table_service_client is of type TableServiceClient and table_client is of type
        TableClient.

        Args:
            table_client_service_class_mock (mock.MagicMock): the mock generated by the patch to
                the statement inside the `with`. In the example above, is the patch of the
                class method `TableServiceClient`
            table_client_service_mock (mock.MagicMock): a new mock that will be used as
                return value for the __enter__ method of the context manager. In the example
                above, it mocks the variable `table_service_client`
        """
        table_client_mock = mock.MagicMock()
        context_manager_mock = mock.MagicMock()
        table_client_service_class_mock.from_connection_string.return_value = \
            context_manager_mock

        context_manager_mock.__enter__.return_value = table_client_service_mock
        table_client_service_mock.create_table_if_not_exists.return_value = table_client_mock

    def mock_table_client(self, table_client_service_class_mock, table_client_service_mock):
        """# The previous mock is assigned to the result of TableClient.from_connection_string,
        # which returns a TableClient instance.
        # When using
        #   `with IgluSingleTurnGameStorage(...) as game_storage`
        # the IgluSingleTurnGameStorage instance MUST create a new `table_client: TableClient`
        # and call its __enter__ and __exit__ methods when entering and leaving the with stament.
        # Because the TableClient instance is mocked with table_client_mock, the test
        # can ensure the __enter__ and __exit__ methods have been called.

        Returns:
            A mock.MagicMock representing the result of the
            `table_client_service_mock.create_table_if_not_exists` method.
            In the example above, is a mock of the variable `table_client`.
        """

    def test_create_tables(self, table_client_service_class_mock, _):
        """Tables are created when class is initialized."""
        table_client_service_mock = mock.MagicMock()
        _ = self.mock_table_client_senvice_context_manager(
            table_client_service_class_mock, table_client_service_mock)

        with IgluSingleTurnGameStorage(self.HITS_TABLE_NAME, self.AZURE_CONNECTION_STR) as _:
            table_client_service_class_mock.from_connection_string.assert_called_with(
                self.AZURE_CONNECTION_STR)
            table_client_service_mock.create_table_if_not_exists.assert_called_with(
                table_name=self.HITS_TABLE_NAME)

    def test_azure_table_context_management(
            self, _, table_client_class_mock):
        """The TableClient().__enter__ and TableClient().__exit__ methods are called.

        Args:
            _ (mock.MagicMock): ignored
            table_client_class_mock (mock.MagicMock): a mock for the class TableClient
        """
        table_client_mock = mock.MagicMock()
        table_client_class_mock.from_connection_string.return_value = table_client_mock

        with IgluSingleTurnGameStorage(
                self.HITS_TABLE_NAME,
                self.AZURE_CONNECTION_STR) as game_storage:
            table_client_class_mock.from_connection_string.assert_called()
            table_client_mock.__enter__.assert_called()
            table_client_mock.__exit__.assert_not_called()
            self.assertIsNotNone(game_storage.table_client)
        table_client_mock.__exit__.assert_called()
        self.assertIsNone(game_storage.table_client)

    def test_game_storage_can_raise_exception(self, *args):
        """Exceptions inside the with statement are correctly raised.

        This test fails if __exit__ method is not implemented correctly.
        """
        execption_str = "This should have been raised"

        def failing_function():
            with IgluSingleTurnGameStorage(
                    self.HITS_TABLE_NAME,
                    self.AZURE_CONNECTION_STR) as _:
                raise ValueError(execption_str)

        with self.assertRaises(ValueError) as raised_exception:
            failing_function()
        self.assertEqual(raised_exception.exception.args[0], execption_str)

    def test_game_storage_fails_if_outside_with(self, *args):
        """If IgluSingleTurnGameStorage is used without a context manager, raise exception."""

        def failing_function():
            storage = IgluSingleTurnGameStorage(self.HITS_TABLE_NAME, self.AZURE_CONNECTION_STR)
            storage.get_last_game_index()

        self.assertRaises(ValueError, failing_function)

        def failing_function():
            storage = IgluSingleTurnGameStorage(self.HITS_TABLE_NAME, self.AZURE_CONNECTION_STR)
            storage.select_start_worlds_ids(3)

        self.assertRaises(ValueError, failing_function)


if __name__ == '__main__':
    unittest.main()
