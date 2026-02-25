import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock dependencies
sys.modules['firebase_functions'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['google.cloud.firestore_v1.vector'] = MagicMock()
sys.modules['google.cloud.firestore_v1.base_vector_query'] = MagicMock()
sys.modules['vertexai'] = MagicMock()
sys.modules['vertexai.language_models'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

class TestVulnerability(unittest.TestCase):
    def setUp(self):
        # Remove main from sys.modules to force re-import
        if 'main' in sys.modules:
            del sys.modules['main']

    @patch.dict('os.environ', {}, clear=True)
    def test_main_raises_error_without_any_project_id(self):
        # Verify that importing main without APP_PROJECT_ID or GOOGLE_CLOUD_PROJECT raises ValueError
        with self.assertRaises(ValueError) as cm:
            import main

        # Check the error message
        self.assertIn("APP_PROJECT_ID environment variable not set", str(cm.exception))

    @patch.dict('os.environ', {'GOOGLE_CLOUD_PROJECT': 'fallback-project'}, clear=True)
    def test_main_uses_fallback_project_id(self):
        # Verify that importing main with GOOGLE_CLOUD_PROJECT works
        try:
            import main
        except ValueError:
            self.fail("Importing main raised ValueError unexpectedly with GOOGLE_CLOUD_PROJECT set!")

        # Verify that vertexai.init was called with the correct project id
        # Access the mock from sys.modules
        vertexai_mock = sys.modules['vertexai']
        vertexai_mock.init.assert_called_with(project='fallback-project', location='us-central1')

    @patch.dict('os.environ', {'APP_PROJECT_ID': 'primary-project'}, clear=True)
    def test_main_uses_primary_project_id(self):
        # Verify that importing main with APP_PROJECT_ID works
        try:
            import main
        except ValueError:
            self.fail("Importing main raised ValueError unexpectedly with APP_PROJECT_ID set!")

        # Verify that vertexai.init was called with the correct project id
        vertexai_mock = sys.modules['vertexai']
        vertexai_mock.init.assert_called_with(project='primary-project', location='us-central1')

if __name__ == '__main__':
    unittest.main()
