import time
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import importlib

# Mocking dependencies
sys.modules['dotenv'] = MagicMock()
mock_firebase_functions = MagicMock()

def mock_on_call_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

mock_firebase_functions.https_fn.on_call.side_effect = mock_on_call_decorator
mock_firebase_functions.https_fn.HttpsError = Exception
mock_firebase_functions.https_fn.FunctionsErrorCode = MagicMock()

mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_vertexai = MagicMock()
mock_vertexai_models = MagicMock()

sys.modules['firebase_functions'] = mock_firebase_functions
sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['google.cloud.firestore_v1.vector'] = MagicMock()
sys.modules['google.cloud.firestore_v1.base_vector_query'] = MagicMock()
sys.modules['vertexai'] = mock_vertexai
sys.modules['vertexai.language_models'] = mock_vertexai_models

os.environ["APP_PROJECT_ID"] = "test-project"
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def run_benchmark():
    # Mocking the model to simulate heavy initialization
    def side_effect_from_pretrained(*args, **kwargs):
        print("Initializing model...")
        time.sleep(0.5) # Simulate 500ms initialization
        return MagicMock()

    print("Running improved benchmark...")

    # We want to catch the initialization that happens at module import
    with patch('vertexai.language_models.TextEmbeddingModel.from_pretrained', side_effect=side_effect_from_pretrained) as mock_init:
        # Import/Reload main to trigger global initialization
        if 'main' in sys.modules:
            del sys.modules['main']
        import main
        from main import share_experience

        mock_req = MagicMock()
        mock_req.data = {"text": "This is a long enough text for testing."}
        mock_req.auth = None
        main.db = MagicMock()

        iterations = 5

        start_time = time.time()
        for i in range(iterations):
            share_experience(mock_req)
        end_time = time.time()

        total_time = end_time - start_time
        print(f"Total time for {iterations} iterations: {total_time:.4f}s")
        print(f"Average time per iteration (excluding global init): {total_time/iterations:.4f}s")
        print(f"Model initialization called {mock_init.call_count} times")

if __name__ == "__main__":
    run_benchmark()
