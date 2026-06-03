import unittest
from unittest.mock import MagicMock, patch
import sys
import os

class TestShareExperience(unittest.TestCase):
    def setUp(self):
        super().setUp()

        # Clean up modules
        for mod in ['main', 'firebase_functions', 'firebase_admin', 'google.cloud.firestore_v1.vector', 'google.cloud.firestore_v1.base_vector_query', 'vertexai', 'vertexai.language_models', 'dotenv']:
            if mod in sys.modules:
                del sys.modules[mod]

        # Mocks
        self.mock_dotenv = MagicMock()
        sys.modules['dotenv'] = self.mock_dotenv

        self.mock_firebase_functions = MagicMock()
        def mock_on_call_decorator(*args, **kwargs):
            def wrapper(func):
                return func
            return wrapper
        self.mock_firebase_functions.https_fn.on_call.side_effect = mock_on_call_decorator

        class MockHttpsError(Exception):
            def __init__(self, code, message):
                self.code = code
                self.message = message
        self.mock_firebase_functions.https_fn.HttpsError = MockHttpsError
        self.mock_firebase_functions.https_fn.FunctionsErrorCode.INVALID_ARGUMENT = "INVALID_ARGUMENT"
        sys.modules['firebase_functions'] = self.mock_firebase_functions

        self.mock_firebase_admin = MagicMock()
        self.mock_firestore = MagicMock()
        self.mock_db = MagicMock()
        self.mock_firestore.client.return_value = self.mock_db
        self.mock_firebase_admin.firestore = self.mock_firestore
        sys.modules['firebase_admin'] = self.mock_firebase_admin

        sys.modules['google.cloud.firestore_v1.vector'] = MagicMock()
        sys.modules['google.cloud.firestore_v1.base_vector_query'] = MagicMock()

        self.mock_vertexai = MagicMock()
        sys.modules['vertexai'] = self.mock_vertexai

        self.mock_vertexai_models = MagicMock()
        sys.modules['vertexai.language_models'] = self.mock_vertexai_models

        # Import main
        os.environ["APP_PROJECT_ID"] = "test-project"
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        import main
        self.main = main

    @patch('main.TextEmbeddingModel')
    def test_share_experience_anonymous(self, mock_model_class):
        mock_req = MagicMock()
        mock_req.data = {"text": "This is a long enough text for testing."}
        mock_req.auth = None

        mock_model = MagicMock()
        mock_model_class.from_pretrained.return_value = mock_model
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.2, 0.3]
        mock_model.get_embeddings.return_value = [mock_embedding]

        mock_posts_ref = MagicMock()
        # Mock db in the imported module!
        self.main.db.collection.return_value = mock_posts_ref

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "new_post_id"
        mock_posts_ref.add.return_value = (None, mock_doc_ref)

        mock_vector_query = MagicMock()
        mock_posts_ref.find_nearest.return_value = mock_vector_query
        mock_vector_query.stream.return_value = []

        result = self.main.share_experience(mock_req)

        self.assertTrue(result.get("success"), f"Expected success but got {result}")
        self.assertEqual(result.get("myPostId"), "new_post_id")
        self.assertTrue(mock_posts_ref.add.called)
        args, _ = mock_posts_ref.add.call_args
        added_post = args[0]
        self.assertEqual(added_post["authorId"], "anonymous")

    @patch('main.TextEmbeddingModel')
    def test_share_experience_authenticated(self, mock_model_class):
        mock_req = MagicMock()
        mock_req.data = {"text": "This is a long enough text for testing authenticated."}
        mock_req.auth = MagicMock()
        mock_req.auth.uid = "user123"

        mock_model = MagicMock()
        mock_model_class.from_pretrained.return_value = mock_model
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
        mock_req.data = {"text": {"not": "a string"}}
        mock_req.auth = None

        # Call the function and expect HttpsError
        with self.assertRaises(main.https_fn.HttpsError) as context:
            share_experience(mock_req)

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
        mock_req.auth = None

        with self.assertRaises(self.main.https_fn.HttpsError) as context:
            self.main.share_experience(mock_req)

        self.assertEqual(context.exception.code, "INVALID_ARGUMENT")
        self.assertEqual(context.exception.message, "O texto é muito longo.")

if __name__ == '__main__':
    unittest.main()
