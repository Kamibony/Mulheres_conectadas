import time
import os
import sys
from unittest.mock import MagicMock, patch

# Mocking dependencies before importing main.py
sys.modules['dotenv'] = MagicMock()
mock_firebase_functions = MagicMock()

def mock_on_call_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

mock_firebase_functions.https_fn.on_call.side_effect = mock_on_call_decorator

class MockHttpsError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

mock_firebase_functions.https_fn.HttpsError = MockHttpsError
mock_firebase_functions.https_fn.FunctionsErrorCode.INVALID_ARGUMENT = "INVALID_ARGUMENT"

mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_vertexai = MagicMock()
mock_vertexai_models = MagicMock()

# Configure firestore mock
mock_db = MagicMock()
mock_firestore.client.return_value = mock_db
mock_firebase_admin.firestore = mock_firestore

sys.modules['firebase_functions'] = mock_firebase_functions
sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['google.cloud.firestore_v1.vector'] = MagicMock()
sys.modules['google.cloud.firestore_v1.base_vector_query'] = MagicMock()
sys.modules['vertexai'] = mock_vertexai
sys.modules['vertexai.language_models'] = mock_vertexai_models

os.environ["APP_PROJECT_ID"] = "benchmark-project"
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import main
from main import share_experience

def mock_from_pretrained(model_name):
    # Simulate a 1-second delay for loading the model
    time.sleep(1.0)
    mock_model = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1, 0.2, 0.3]
    mock_model.get_embeddings.return_value = [mock_embedding]
    return mock_model

@patch('main.TextEmbeddingModel.from_pretrained', side_effect=mock_from_pretrained)
def run_benchmark(mock_pretrained):
    print("Running benchmark...")

    mock_req = MagicMock()
    mock_req.data = {"text": "This is a valid text for testing benchmark"}
    mock_req.auth = MagicMock()
    mock_req.auth.uid = "test-user"

    mock_posts_ref = MagicMock()
    mock_db.collection.return_value = mock_posts_ref
    mock_doc_ref = MagicMock()
    mock_doc_ref.id = "benchmark_post_id"
    mock_posts_ref.add.return_value = (None, mock_doc_ref)

    mock_vector_query = MagicMock()
    mock_posts_ref.find_nearest.return_value = mock_vector_query
    mock_vector_query.stream.return_value = []

    times = []
    # Call multiple times to see the difference
    for i in range(3):
        start_time = time.time()
        share_experience(mock_req)
        end_time = time.time()
        duration = end_time - start_time
        times.append(duration)
        print(f"Call {i+1} took: {duration:.4f} seconds")

    print(f"Total time for 3 calls: {sum(times):.4f} seconds")

if __name__ == "__main__":
    run_benchmark()
