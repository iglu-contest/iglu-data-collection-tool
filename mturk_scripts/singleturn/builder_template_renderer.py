import html
import os
import sys
from string import Template
from typing import Any, Dict

# Project root
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from hit_manager import TemplateRenderer


class BuilderTemplateRenderer(TemplateRenderer):

    def __init__(self, template_filepath: str = 'templates') -> None:
        self.template_filepath = template_filepath

    def render_template_from_turn(self, azure_sas, open_turn) -> Dict[str, Any]:
        """Extracts from a Turn instance the parameters to render a normal_builder template.
        """
        return self.render_template(
            game_id=open_turn.game_id,
            azure_sas=azure_sas,
            starting_world_blob_name=open_turn.starting_world_blob_name,
            starting_world_blob_path=open_turn.starting_world_blob_path,
            starting_step=open_turn.starting_step,
            screenshot_step_view=open_turn.screenshot_step_view,
        )

    def render_template(self, game_id: str, azure_sas: str,
                        starting_world_blob_path: str, starting_world_blob_name: str,
                        starting_step: str, screenshot_step_view: str) -> str:
        with open(self.template_filepath, 'r') as template_file:
            template = Template(template_file.read())

        template_kwargs = {
            'gameId': self.escape_arg(game_id),  # 317
            'sas': azure_sas,
            'builderDataPath': self.escape_arg(starting_world_blob_path),  # 'test-builder-data'
            'initializedWorldGameId': self.escape_arg(starting_world_blob_name),  # '37-c161'
            'screenshotStep': self.escape_arg(starting_step),    # 'step-2'
            'screenshotStepView': self.escape_arg(screenshot_step_view),  # 'step-2_north'
        }
        return template.substitute(**template_kwargs)

    @staticmethod
    def escape_arg(arg: str) -> str:
        return html.escape(str(arg))
