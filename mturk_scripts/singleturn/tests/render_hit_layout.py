"""Script to create local HTML files that can be used to test the voxelworld experience."""
import dotenv
import os
import sys

# Project root
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from singleturn.singleturn_games_storage import IgluSingleTurnGameStorage  # noqa: E402
from singleturn.builder_template_renderer import BuilderTemplateRenderer  # noqa: E402
from utils import read_config  # noqa: E402

dotenv.load_dotenv(
    os.path.join(os.path.dirname(__file__), '..', '.env'))


class HTMLBuilderTemplateRenderer(BuilderTemplateRenderer):

    def render_template(self, **template_kwargs) -> str:
        rendered_template = super().render_template(**template_kwargs)

        # Get only the HTML content of the template
        template_start_index = rendered_template.index('<html>')
        template_end_index = rendered_template.index('</html>') + len('</html>')
        return rendered_template[template_start_index:template_end_index]


def main():

    config = read_config('sandbox', config_filepath='../env_configs.json')

    config['azure_connection_str'] = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    config['azure_sas'] = os.getenv('AZURE_STORAGE_SAS')

    with IgluSingleTurnGameStorage(**config) as game_storage:
        hit_type = 'html_template'
        last_game_index = game_storage.get_last_game_index() + 1

        # Handpicked example that has a starting grid
        open_turn = game_storage.get_turns_from_open_game(
            game_id=game_storage.game_id_from_game_index(last_game_index),
            turn_type=hit_type, starting_world_path='test-builder-data/10-c164/step-4'
        )

        renderer = BuilderTemplateRenderer('test_data/no_write_builder_normal.xml')

        template = renderer.render_template_from_turn(config['azure_sas'], open_turn)

        with open('test_data/test_html_hit.html', 'w') as test_html_hit_file:
            test_html_hit_file.write(template)


if __name__ == '__main__':
    main()
