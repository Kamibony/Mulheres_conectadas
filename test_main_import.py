import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Need to mock some things before importing main
sys.modules['dotenv'] = MagicMock()
os.environ['APP_PROJECT_ID'] = 'test-project'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'
sys.path.append(os.path.join(os.path.dirname(__file__), 'functions'))

import main

class TestImports(unittest.TestCase):
    def test_import(self):
        self.assertIsNotNone(main)

if __name__ == '__main__':
    unittest.main()
