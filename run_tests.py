import sys
import os
from unittest.mock import MagicMock

# Mock what needs to be mocked before importing tests
sys.modules['dotenv'] = MagicMock()
os.environ['APP_PROJECT_ID'] = 'test-project'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'
sys.path.append(os.path.join(os.path.dirname(__file__), 'functions'))

import unittest
if __name__ == '__main__':
    tests = unittest.TestLoader().discover('functions/tests/')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    sys.exit(not result.wasSuccessful())
