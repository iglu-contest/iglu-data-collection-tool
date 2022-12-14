"""
Create, query and delete hits using sandbox mturk client.
"""

import datetime
import dotenv
import os
import sys

# Project root
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# Load dotenv before project imports
dotenv.load_dotenv(
    os.path.join(os.path.dirname(__file__), '..', '.env'))


from hit_manager import HITManager, TemplateRenderer  # noqa: E402
from common import utils, logger  # noqa: E402

_LOGGER = logger.get_logger(__name__)


def main():
    endpoint = 'sandbox'
    config = utils.read_config(endpoint, '../env_configs.json')
    max_hits = 5
    hit_type = 'simple_template'

    renderer = TemplateRenderer('test_data/test_html_hit.html')

    hit_manager = HITManager(
        mturk_endpoint=config['mturk_endpoint'],
        aws_access_key=os.environ.get('AWS_ACCESS_KEY_ID', ''),
        aws_secret_key=os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
    )

    # Create hits
    created_hits = []
    for i in range(max_hits):
        template = renderer.render_template()
        hit_id = hit_manager.create_hit(
            template, hit_type=hit_type, hit_lifetime_seconds=60,
            max_assignments=3, auto_approval_delay_seconds=60, reward="0.80",
            assignment_duration_in_seconds=60, title=f'Hit number {i}')
        created_hits.append(hit_id)

    # Look for different type
    all_hits = hit_manager.get_open_hit_ids("not" + hit_type)
    _LOGGER.info(f"Hits of incorrect type returned {len(all_hits)}")

    all_hits = hit_manager.get_open_hit_ids(hit_type)
    _LOGGER.info(f"Hits of correct type returned {len(all_hits)}")

    # Clean up created hits
    for hit in all_hits:
        hit_manager.mturk_client.update_expiration_for_hit(
            HITId=hit,
            ExpireAt=datetime.datetime(2015, 1, 1)
        )
        hit_manager.mturk_client.delete_hit(HITId=hit)
        _LOGGER.info(f"Hit {hit} deleted")


if __name__ == '__main__':
    main()
