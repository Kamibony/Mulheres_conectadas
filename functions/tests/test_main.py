import unittest
from unittest.mock import MagicMock, patch
import sys

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
mock_firebase_functions.https_fn.FunctionsErrorCode.UNAUTHENTICATED = "UNAUTHENTICATED"

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

class TestShareExperience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import main
        cls.main = main

    def setUp(self):
        # Reset the global model before each test
        self.main._text_embedding_model = None

    @patch('main.TextEmbeddingModel')
    def test_share_experience_anonymous(self, mock_model_class):
        mock_req = MagicMock()
        mock_req.data = {"text": "This is a long enough text for testing."}
        mock_req.auth = None

        # Call the function and expect HttpsError
        with self.assertRaises(main.https_fn.HttpsError) as context:
            share_experience(mock_req)

        # Assertions
        self.assertEqual(context.exception.code, "UNAUTHENTICATED")
        self.assertEqual(context.exception.message, "Usuária não autenticada.")


    def test_share_experience_authenticated(self):
        """Test share_experience with an authenticated user"""
        # Setup mock request
        mock_req = MagicMock()
        mock_req.data = {"text": "This is a long enough text for testing authenticated."}
        mock_req.auth = MagicMock()
        mock_req.auth.uid = "user123"

        # Setup mock Vertex AI model
        mock_model = main.embedding_model
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.2, 0.3]
        mock_model.get_embeddings.return_value = [mock_embedding]

        mock_posts_ref = MagicMock()
        self.main.db.collection.return_value = mock_posts_ref

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "auth_post_id"
        mock_posts_ref.add.return_value = (None, mock_doc_ref)

        mock_vector_query = MagicMock()
        mock_posts_ref.find_nearest.return_value = mock_vector_query
        mock_vector_query.stream.return_value = []

        result = self.main.share_experience(mock_req)

        self.assertTrue(result.get("success"), f"Expected success but got {result}")
        self.assertTrue(mock_posts_ref.add.called)
        args, _ = mock_posts_ref.add.call_args
        added_post = args[0]
        self.assertEqual(added_post["authorId"], "user123")

    def test_share_experience_text_invalid_type(self):
        """Test share_experience with text that is not a string"""
        # Setup mock request
        mock_req = MagicMock()
        mock_req.data = {"text": "Short"}
        mock_req.auth = MagicMock()

        # Call the function and expect HttpsError
        with self.assertRaises(self.main.https_fn.HttpsError) as context:
            self.main.share_experience(mock_req)

        # Assertions
        self.assertEqual(context.exception.code, "INVALID_ARGUMENT")
        self.assertEqual(context.exception.message, "O texto fornecido deve ser uma string.")

    def test_share_experience_text_too_short(self):
        mock_req = MagicMock()
        mock_req.data = {"text": "Short"}
        mock_req.auth = None

        with self.assertRaises(self.main.https_fn.HttpsError) as context:
            self.main.share_experience(mock_req)

        self.assertEqual(context.exception.code, "INVALID_ARGUMENT")
        self.assertEqual(context.exception.message, "O texto é muito curto.")

    def test_share_experience_text_too_long(self):
        long_text = "a" * (self.main.MAX_TEXT_LENGTH + 1)
        mock_req = MagicMock()
        mock_req.data = {"text": long_text}
        mock_req.auth = MagicMock()

        with self.assertRaises(self.main.https_fn.HttpsError) as context:
            self.main.share_experience(mock_req)

        self.assertEqual(context.exception.code, "INVALID_ARGUMENT")
        self.assertEqual(context.exception.message, "O texto é muito longo.")

class TestRequestReveal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need to import main after mocking
        import main
        cls.main = main

    def test_request_reveal_identity_invalid_type(self):
        mock_req = MagicMock()
        mock_req.data = {"chatId": "chat123", "identity": {"not": "a string"}}
        mock_req.auth = MagicMock()
        mock_req.auth.uid = "user123"

        with self.assertRaises(self.main.https_fn.HttpsError) as context:
            self.main.request_reveal(mock_req)

        self.assertEqual(context.exception.code, "INVALID_ARGUMENT")
        self.assertEqual(context.exception.message, "A identity deve ser uma string.")

    def test_request_reveal_identity_too_long(self):
        mock_req = MagicMock()
        mock_req.data = {"chatId": "chat123", "identity": "a" * 101}
        mock_req.auth = MagicMock()
        mock_req.auth.uid = "user123"

        with self.assertRaises(self.main.https_fn.HttpsError) as context:
            self.main.request_reveal(mock_req)

        self.assertEqual(context.exception.code, "INVALID_ARGUMENT")
        self.assertEqual(context.exception.message, "A identity é muito longa.")

if __name__ == '__main__':
    unittest.main()
