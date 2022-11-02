"""Function to create HITs with a given layouts.
"""
from abc import ABC
from typing import Any, Dict, Optional
import boto3
import html
import os

from string import Template
import logger

_LOGGER = logger.get_logger(__name__)


class TemplateFiller(ABC):
    @staticmethod
    def fill_template(template: str, **kwargs):
        raise NotImplementedError(
            'Attempting to use abstract class. Create subclasses for different templates')


class BuilderTemplateFiller(TemplateFiller):

    def fill_template(self, template: str,
                      game_id: str, azure_sas: str, initialized_world_game_id: str,
                      step_screenshot_path: str, builder_data_path: str,
                      step_screenshot_view: str) -> str:
        template_kwargs = {
            'gameId': self.escape_arg(game_id),
            'sas': azure_sas,
            'initializedWorldGameId': self.escape_arg(initialized_world_game_id),
            'screenshotStep': self.escape_arg(step_screenshot_path),
            'builderDataPath': self.escape_arg(builder_data_path),
            'screenshotStepView': self.escape_arg(step_screenshot_view),
        }
        return template.substitute(**template_kwargs)

    @staticmethod
    def escape_arg(arg: str) -> str:
        return html.escape(str(arg))


class HITManager:

    # Register any new template to keep track of the files, versions and values
    # that each of them receive, istead of having to inspect each xml file.
    REGISTERED_TEMPLATES = {
        'builder_normal': {
            'v0.1': {
                'filename': 'builder_normal.xml',
                'filler_class': BuilderTemplateFiller(),
            }
        }
    }

    def __init__(self, templates_dirname: str, azure_connection_str: str, mturk_endpoint: str,
                 aws_access_key: str, aws_secret_key: str, **kwargs) -> None:
        self.azure_connection_str = azure_connection_str
        self.templates_dirname = templates_dirname
        self.open_hits = {}
        self.mturk_client = boto3.client(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            service_name='mturk',
            region_name='us-east-1',
            endpoint_url=mturk_endpoint,
        )

    def has_open_hits(self):
        return len(self.open_hits)

    def get_template_path(self, hit_type: str, version: str = 'v0.1') -> str:
        return os.path.join(
            self.templates_dirname,
            self.REGISTERED_TEMPLATES[hit_type][version]['filename'])

    def create_template_given_type(
            self, turn_type: str, version: str = 'v0.1',
            renderer_kwargs: Optional[Dict[str, Any]] = None) -> str:
        try:
            renderer = self.REGISTERED_TEMPLATES[turn_type][version]['filler_class']
        except KeyError:
            _LOGGER.error("Cannot find registered template for turn type "
                          f"{turn_type} version {version}")
        with open(self.get_template_path(turn_type, version), 'r') as template_file:
            template = Template(template_file.read())
        if renderer_kwargs is None:
            renderer_kwargs = {}
        return renderer.fill_template(template, **renderer_kwargs)

    def create_hit(
            self, rendered_template, hit_lifetime_seconds=3600,
            max_assignments=1, keywords: str = 'boto, qualification, iglu, minecraft,',
            auto_approval_delay_seconds: int = 3600, reward: str = "0.80",
            assignment_duration_in_seconds: int = 480,
            title: str = '', description: str = '',
            qualification_type_id: str = None,
            **kwargs) -> str:
        common_kwargs = dict(
            LifetimeInSeconds=hit_lifetime_seconds,  # 604800
            MaxAssignments=max_assignments,
            Keywords=keywords,
            AutoApprovalDelayInSeconds=auto_approval_delay_seconds,
        )

        hit = self.mturk_client.create_hit(
            **common_kwargs,
            Reward=reward,
            AssignmentDurationInSeconds=assignment_duration_in_seconds,
            Title=title,
            Description=description,
            Question=rendered_template,
            # QualificationRequirements=[{
            #     'QualificationTypeId': qualification_type_id,
            #     'Comparator': 'GreaterThan',
            #     'IntegerValues': [80]
            # },
            #     # ,{'QualificationTypeId': '00000000000000000071',
            #     # 'Comparator': 'In',
            #     # 'LocaleValues': [{ 'Country': "US" },{ 'Country': "CA" }]
            #     # }
            # ]
        )
        hit_id = hit['HIT']['HITId']
        print(f'HIT created with Id {hit_id}')
        self.open_hits[hit_id] = hit
        return hit_id

    def delete_hit(self, hit_id: str) -> None:
        self.mturk_client.delete_hit(HITId=hit_id)
