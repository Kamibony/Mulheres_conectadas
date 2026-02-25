import unittest
from unittest.mock import MagicMock, patch
import sys

# Mocking dependencies before importing main.py
mock_firebase_functions = MagicMock()

def mock_on_call_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

mock_firebase_functions.https_fn.on_call.side_effect = mock_on_call_decorator

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

# Now import the function to test
import os
# Set the environment variable before importing main to prevent ValueError
os.environ["APP_PROJECT_ID"] = "test-project"
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import main
from main import share_experience

class TestShareExperience(unittest.TestCase):
    @patch('main.TextEmbeddingModel')
    def test_share_experience_anonymous(self, mock_model_class):
        """Test share_experience with an anonymous user (req.auth is None)"""
        # Setup mock request
        mock_req = MagicMock()
        mock_req.data = {"text": "This is a long enough text for testing."}
        mock_req.auth = None

        # Setup mock Vertex AI model
        mock_model = MagicMock()
        mock_model_class.from_pretrained.return_value = mock_model
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.2, 0.3]
        mock_model.get_embeddings.return_value = [mock_embedding]

        # Setup mock Firestore
        mock_posts_ref = MagicMock()
        mock_db.collection.return_value = mock_posts_ref
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "new_post_id"
        mock_posts_ref.add.return_value = (None, mock_doc_ref)

        # Setup mock vector query
        mock_vector_query = MagicMock()
        mock_posts_ref.find_nearest.return_value = mock_vector_query
        mock_vector_query.stream.return_value = []

        # Call the function
        result = share_experience(mock_req)

        # Assertions
        self.assertTrue(result.get("success"), f"Expected success but got {result}")
        self.assertEqual(result.get("myPostId"), "new_post_id")

        # Check if authorId was "anonymous"
        self.assertTrue(mock_posts_ref.add.called)
        args, _ = mock_posts_ref.add.call_args
        added_post = args[0]
        self.assertEqual(added_post["authorId"], "anonymous")

    @patch('main.TextEmbeddingModel')
    def test_share_experience_authenticated(self, mock_model_class):
        """Test share_experience with an authenticated user"""
        # Setup mock request
        mock_req = MagicMock()
        mock_req.data = {"text": "This is a long enough text for testing authenticated."}
        mock_req.auth = MagicMock()
        mock_req.auth.uid = "user123"

        # Setup mock Vertex AI model
        mock_model = MagicMock()
        mock_model_class.from_pretrained.return_value = mock_model
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.2, 0.3]
        mock_model.get_embeddings.return_value = [mock_embedding]

        # Setup mock Firestore
        mock_posts_ref = MagicMock()
        mock_db.collection.return_value = mock_posts_ref
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "auth_post_id"
        mock_posts_ref.add.return_value = (None, mock_doc_ref)

        # Setup mock vector query
        mock_vector_query = MagicMock()
        mock_posts_ref.find_nearest.return_value = mock_vector_query
        mock_vector_query.stream.return_value = []

        # Call the function
        result = share_experience(mock_req)

        # Assertions
        self.assertTrue(result.get("success"))

        # Check if authorId was "user123"
        self.assertTrue(mock_posts_ref.add.called)
        args, _ = mock_posts_ref.add.call_args
        added_post = args[0]
        self.assertEqual(added_post["authorId"], "user123")

    def test_share_experience_text_too_short(self):
        """Test share_experience with text that is too short"""
        # Setup mock request
        mock_req = MagicMock()
        mock_req.data = {"text": "Short"}
        mock_req.auth = None

        # Call the function
        result = share_experience(mock_req)

        # Assertions
        self.assertIn("error", result)
        self.assertEqual(result["error"], "O texto é muito curto.")

    def test_share_experience_text_too_long(self):
        """Test share_experience with text that is too long"""
        # Setup mock request
        long_text = "a" * (main.MAX_TEXT_LENGTH + 1)
        mock_req = MagicMock()
        mock_req.data = {"text": long_text}
        mock_req.auth = None

        # Call the function
        result = share_experience(mock_req)

        # Assertions
        self.assertIn("error", result)
        self.assertEqual(result["error"], "O texto é muito longo.")

if __name__ == '__main__':
    unittest.main()
