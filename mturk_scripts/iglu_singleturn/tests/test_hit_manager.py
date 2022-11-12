"""_summary_"""

import datetime
import json
import os
import sys
import unittest

from typing import Optional
from unittest import mock

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from hit_manager import HITManager, BuilderTemplateRenderer  # noqa: E402


class MturkClientFake(mock.MagicMock):
    NEXT_HIT_ID = 0

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hits = {}

    def list_hits(self, *args, **kwargs):
        return {
            'NextToken': '',
            'NumResults': len(self.hits),
            'HITs': [hit for hit in self.hits.values()]
        }

    def create_hit(
            self, hit_type='', max_assignments=1, hit_lifetime_seconds=60,
            assignment_duration_in_seconds=60, *args, **kwargs):
        """Creates new hit with default states (assignable, not reviewed, etc.)"""
        new_hit_id = self.NEXT_HIT_ID
        self.NEXT_HIT_ID += 1
        self.create_mock_hit(
            new_hit_id, hit_type, assignments_available=max_assignments,
            hit_lifetime_seconds=hit_lifetime_seconds,
            assignment_duration_in_seconds=assignment_duration_in_seconds)
        return new_hit_id

    def create_mock_hit(
            self, hit_id, hit_type: str = '', status: str = 'Assignable',
            creation_time: Optional[datetime.datetime] = None,
            hit_review_status: str = 'NotReviewed',
            hit_lifetime_seconds: int = 60, assignment_duration_in_seconds: int = 60,
            assignments_pending: int = 0, assignments_available: int = 0,
            assignments_completed: int = 0):
        creation_time = datetime.datetime.now() if creation_time is None else creation_time
        # Create only used fields, real HITs are more complex
        self.hits[hit_id] = {
            'HITId': hit_id,
            'CreationTime': creation_time,
            # Possible status are 'Assignable'|'Unassignable'|'Reviewable'|'Reviewing'|'Disposed',
            'HITStatus': status,
            'MaxAssignments': assignments_pending + assignments_available + assignments_completed,
            'Expiration': creation_time + datetime.timedelta(seconds=hit_lifetime_seconds),
            'AssignmentDurationInSeconds': assignment_duration_in_seconds,
            # Possible review status 'NotReviewed'|'MarkedForReview'|'ReviewedAppropriate'|
            # 'ReviewedInappropriate'
            'HITReviewStatus': hit_review_status,
            'NumberOfAssignmentsPending': assignments_pending,
            'NumberOfAssignmentsAvailable': assignments_available,
            'NumberOfAssignmentsCompleted': assignments_completed,
            'RequesterAnnotation': json.dumps({'hit_type': hit_type}),
        }


@mock.patch('hit_manager.boto3.client')
class HitManagerTest(unittest.TestCase):

    AWS_SECRET_KEY = 'secret_key'
    AWS_ACCESS_KEY = 'access_key'
    HIT_TYPE = 'builder_normal'

    def test_get_open_hits(self, boto3_client_mock: mock.MagicMock):
        """Get hits that are not expired with and that have not been reviewed."""
        fake_mturk_client = MturkClientFake()
        boto3_client_mock.return_value = fake_mturk_client

        hit_manager = HITManager(
            mturk_endpoint="sandbox",
            aws_access_key=self.AWS_ACCESS_KEY,
            aws_secret_key=self.AWS_SECRET_KEY,
            max_hits=5,
        )
        last_hit_id = 1

        expected_hit_ids = []
        non_expected_hit_ids = []
        for i in range(4):
            # new_hit
            fake_mturk_client.create_mock_hit(
                last_hit_id, hit_type=self.HIT_TYPE, status="Assignable",
                hit_review_status="NotReviewed", assignments_pending=1,
                hit_lifetime_seconds=60,
            )
            expected_hit_ids.append(last_hit_id)
            last_hit_id += 1

            # new_hit from different type
            fake_mturk_client.create_mock_hit(
                last_hit_id, hit_type="not_" + self.HIT_TYPE, status="Assignable",
                hit_review_status="NotReviewed", assignments_pending=1,
                hit_lifetime_seconds=60,
            )
            non_expected_hit_ids.append(last_hit_id)
            last_hit_id += 1

            # hit to review
            fake_mturk_client.create_mock_hit(
                last_hit_id, hit_type=self.HIT_TYPE, status="Reviewable",
                hit_review_status="MarkedForReview", assignments_completed=1,
                hit_lifetime_seconds=60,
            )
            expected_hit_ids.append(last_hit_id)
            last_hit_id += 1

            # expired_hit_id
            fake_mturk_client.create_mock_hit(
                last_hit_id, hit_type=self.HIT_TYPE, status="Assignable",
                creation_time=datetime.datetime.now() - datetime.timedelta(hours=1),
                hit_lifetime_seconds=60,
                hit_review_status="NotReviewed", assignments_pending=1,
            )
            non_expected_hit_ids.append(last_hit_id)
            last_hit_id += 1

            # non expired but reviewed hit
            fake_mturk_client.create_mock_hit(
                last_hit_id, hit_type=self.HIT_TYPE, status="Unassignable",
                hit_lifetime_seconds=60,
                hit_review_status="ReviewedAppropriate", assignments_completed=1,
            )
            non_expected_hit_ids.append(last_hit_id)
            last_hit_id += 1

        hit_ids = hit_manager.get_open_hit_ids(self.HIT_TYPE)
        self.assertEqual(set(hit_ids), set(expected_hit_ids))


class BuilderTemplateRendererTests(unittest.TestCase):

    def test_render_builder_template(self):
        """Builder normal template is correctly rendered.

        If this tests fails, it is likely there is a discrepancy between function
        builder_normal_template_kwargs and the template itself."""

        renderer = BuilderTemplateRenderer(
            template_filepath="test_data/no_write_builder_normal.xml",
        )

        template_kwargs = {
            'game_id': 'game_id',
            'azure_sas': 'azure_sas',
            'starting_world_blob_path': 'test-builder-data',
            'starting_world_blob_name': '37-c161',
            'starting_step': 'step-2',
            'screenshot_step_view': 'step-2_north',
        }

        rendered_template = renderer.render_template(**template_kwargs)

        # All variables have been replaced
        self.assertNotIn('$', rendered_template)

        for parameter_value in template_kwargs.values():
            self.assertIn(parameter_value, rendered_template)


if __name__ == '__main__':
    unittest.main()
