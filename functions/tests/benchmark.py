import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time
import logging

# Mocking dependencies
sys.modules['dotenv'] = MagicMock()
mock_firebase_functions = MagicMock()

def mock_on_call_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

mock_firebase_functions.https_fn.on_call.side_effect = mock_on_call_decorator
mock_firebase_functions.https_fn.FunctionsErrorCode.INVALID_ARGUMENT = "INVALID_ARGUMENT"
mock_firebase_functions.https_fn.HttpsError = Exception

mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_vertexai = MagicMock()
mock_vertexai_models = MagicMock()

mock_db = MagicMock()
mock_firestore.client.return_value = mock_db
mock_firebase_admin.firestore = mock_firestore

sys.modules['firebase_functions'] = mock_firebase_functions
sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['google.cloud.firestore_v1.vector'] = MagicMock()
sys.modules['google.cloud.firestore_v1.base_vector_query'] = MagicMock()
sys.modules['vertexai'] = mock_vertexai
sys.modules['vertexai.language_models'] = mock_vertexai_models

# Set environment variable
os.environ["APP_PROJECT_ID"] = "test-project"
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def mocked_from_pretrained(model_name):
    print("      [Mock] Loading model...")
    time.sleep(1.0) # Simulate 1 second load time
    return MagicMock()

def run_benchmark():
    # We want to measure the time including the module initialization
    print("--- Starting Benchmark (Optimized) ---")

    # We mock the class method BEFORE importing main
    with patch('vertexai.language_models.TextEmbeddingModel.from_pretrained', side_effect=mocked_from_pretrained):
        start_import = time.perf_counter()
        if 'main' in sys.modules:
            del sys.modules['main']
        import main
        from main import share_experience
        import_duration = time.perf_counter() - start_import
        print(f"Module import (cold start) duration: {import_duration:.4f}s")

        # Setup mock request
        mock_req = MagicMock()
        mock_req.data = {"text": "This is a long enough text for testing performance."}
        mock_req.auth = None

        # Mock Firestore behavior
        mock_posts_ref = MagicMock()
        main.db.collection.return_value = mock_posts_ref
        mock_posts_ref.add.return_value = (None, MagicMock(id="test_id"))
        mock_vector_query = MagicMock()
        mock_posts_ref.find_nearest.return_value = mock_vector_query
        mock_vector_query.stream.return_value = []

        # First call (should be fast because already initialized during import)
        start_time = time.perf_counter()
        share_experience(mock_req)
        first_call_duration = time.perf_counter() - start_time
        print(f"First function call duration: {first_call_duration:.4f}s")

        # Second call (should also be fast)
        start_time = time.perf_counter()
        share_experience(mock_req)
        second_call_duration = time.perf_counter() - start_time
        print(f"Second function call duration: {second_call_duration:.4f}s")

    print("--- Benchmark Finished ---")
    return import_duration, first_call_duration, second_call_duration

if __name__ == "__main__":
    run_benchmark()
