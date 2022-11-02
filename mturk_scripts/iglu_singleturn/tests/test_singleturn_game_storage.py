"""_summary_"""

import os
import unittest
from unittest import mock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from singleturn_games_storage import IgluSingleTurnGameStorage  # noqa: E402


@mock.patch("singleturn_games_storage.TableClient")
@mock.patch("singleturn_games_storage.TableServiceClient.from_connection_string")
class TestIgluSingleTurnGameStorage(unittest.TestCase):

    HITS_TABLE_NAME: str = 'HitsTable'
    AZURE_CONNECTION_STR: str = 'some_hash_string'

    def mock_context_manager(self, with_statement_body_mock):
        """Mock objects created using a with statement.

        For example, mock `table_service_client` instance in:
        >>> with TableServiceClient.from_connection_string("str") as table_service_client

        Args:
            with_statement (mock.MagicMock): the mock generated by the patch to
            the statement inside the `with`. In the example above, is the patch of the
            class method `TableServiceClient.from_connection_string`

        Returns:
            a mock.MagicMock representing the result of the `with` statement managed
            inside the context. In the example above, is a mock of the instance
            `table_service_client`, which is the result of calling
            `TableServiceClient.from_connection_string("str")`.
        """
        with_statement_result_mock = mock.MagicMock()
        # Create mock for the TableServiceClient instance generated by the with statement
        context_manager_mock = mock.MagicMock()
        with_statement_body_mock.return_value = context_manager_mock
        context_manager_mock.__enter__.return_value = with_statement_result_mock
        return with_statement_result_mock

    def test_create_tables(self, from_connection_str_mock, _):
        """Tables are created when class is initialized."""

        table_service_client_mock = self.mock_context_manager(from_connection_str_mock)
        _ = IgluSingleTurnGameStorage(
            self.HITS_TABLE_NAME,
            self.AZURE_CONNECTION_STR
        )
        from_connection_str_mock.assert_called_with(
            self.AZURE_CONNECTION_STR)
        table_service_client_mock.create_table_if_not_exists.assert_called_with(
            table_name=self.HITS_TABLE_NAME)

    def test_azure_table_context_management(self, _, table_client_class_mock):
        """The TableClient.__enter__ and TableClient.__exit__ methods are called.

        Args:
            _ (mock.MagicMock): ignored
            table_client_class_mock (mock.MagicMock): a mock for the class TableClient
        """
        table_client_mock = mock.MagicMock()
        # The previous mock is assigned to the result of TableClient.from_connection_string,
        # which returns a TableClient instance.
        # When using
        #   `with IgluSingleTurnGameStorage(...) as game_storage`
        # the IgluSingleTurnGameStorage instance MUST create a new `table_client: TableClient`
        # and call its __enter__ and __exit__ methods when entering and leaving the with stament.
        # Because the TableClient instance is mocked with table_client_mock, the test
        # can ensure the __enter__ and __exit__ methods have been called.
        table_client_class_mock.from_connection_string.return_value = \
            table_client_mock
        with IgluSingleTurnGameStorage(
                self.HITS_TABLE_NAME,
                self.AZURE_CONNECTION_STR) as game_storage:
            table_client_class_mock.from_connection_string.assert_called_with(
                conn_str=self.AZURE_CONNECTION_STR, table_name=self.HITS_TABLE_NAME
            )
            table_client_mock.__enter__.assert_called()
            table_client_mock.__exit__.assert_not_called()
            self.assertIsNotNone(game_storage.table_client)
        table_client_mock.__exit__.assert_called()

    def test_game_storage_raises_exception(self, *args):
        """Exceptions inside the with statement are correctly raised.

        This test fails if __exit__ method is not implemented correctly.
        """
        execption_str = "This should have been raised"

        def failing_function():
            with IgluSingleTurnGameStorage(
                    self.HITS_TABLE_NAME,
                    self.AZURE_CONNECTION_STR) as _:
                raise ValueError(execption_str)

        self.assertRaises(ValueError, failing_function)


if __name__ == '__main__':
    unittest.main()
