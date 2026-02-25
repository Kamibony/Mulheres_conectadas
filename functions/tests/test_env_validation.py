import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies
sys.modules['firebase_functions'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['google.cloud.firestore_v1.vector'] = MagicMock()
sys.modules['google.cloud.firestore_v1.base_vector_query'] = MagicMock()
sys.modules['vertexai'] = MagicMock()
sys.modules['vertexai.language_models'] = MagicMock()

class TestVulnerability(unittest.TestCase):
    def setUp(self):
        # Remove main from sys.modules to force re-import
        if 'main' in sys.modules:
            del sys.modules['main']

    @patch.dict('os.environ', {}, clear=True)
    def test_main_raises_error_without_gcp_project(self):
        # Verify that importing main without GCP_PROJECT raises ValueError
        with self.assertRaises(ValueError) as cm:
            import main

        # Check the error message
        self.assertIn("GCP_PROJECT environment variable not set", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
