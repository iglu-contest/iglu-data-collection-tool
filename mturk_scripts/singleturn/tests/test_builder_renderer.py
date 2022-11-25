import os
import sys
import unittest

# project root
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from singleturn.builder_template_renderer import BuilderTemplateRenderer

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