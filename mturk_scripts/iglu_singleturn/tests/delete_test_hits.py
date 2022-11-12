"""
Script to remove all hits with turn type "test_hit", stored in field RequesterAnnotation.
"""
import argparse
import datetime
import dotenv
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

# Load dotenv before project imports
dotenv.load_dotenv(
    os.path.join(os.path.dirname(__file__), '..', '.env'))

import logger  # noqa: E402

from hit_manager import HITManager  # noqa: E402
from utils import read_config  # noqa: E402

_LOGGER = logger.get_logger(__name__)


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
       '--hit_type', help='Type of hit to delete.', default='test-hit',
    )
    return parser.parse_args()


def main():
    args = read_args()
    config = read_config("sandbox")

    config['aws_access_key'] = os.getenv("AWS_ACCESS_KEY_ID_LIT")
    config['aws_secret_key'] = os.getenv("AWS_SECRET_ACCESS_KEY_LIT")

    hit_manager = HITManager(
        mturk_endpoint=config['mturk_endpoint'],
        aws_access_key=os.environ.get('AWS_ACCESS_KEY_ID', ''),
        aws_secret_key=os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
    )

    all_hits = hit_manager.get_open_hit_ids(args.hit_type)
    _LOGGER.info(f"Hits of correct type returned {len(all_hits)}")

    # Clean up created hits
    for hit in all_hits:
        hit_manager.mturk_client.update_expiration_for_hit(
            HITId=hit,
            ExpireAt=datetime.datetime(2015, 1, 1)
        )
        try:
            hit_manager.mturk_client.delete_hit(HITId=hit)
            _LOGGER.info(f'Hit {hit} deleted.')
        except Exception:
            _LOGGER.info(f'Hit {hit} not deleted.')


if __name__ == '__main__':
    main()
