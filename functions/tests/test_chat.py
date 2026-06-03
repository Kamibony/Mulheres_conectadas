import unittest
from unittest.mock import MagicMock, patch
import sys
import os

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
mock_firebase_functions.https_fn.FunctionsErrorCode.NOT_FOUND = "NOT_FOUND"

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

os.environ["APP_PROJECT_ID"] = "test-project"
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import main
from main import start_chat, request_reveal

class TestChatFunctions(unittest.TestCase):
    def test_start_chat_unauthenticated(self):
        mock_req = MagicMock()
        mock_req.auth = None

        with self.assertRaises(main.https_fn.HttpsError):
            start_chat(mock_req)

    def test_start_chat_success(self):
        mock_req = MagicMock()
        mock_req.auth.uid = "user_a"
        mock_req.data = {"target_post_id": "post_b"}

        mock_post_doc = MagicMock()
        mock_post_doc.exists = True
        mock_post_doc.to_dict.return_value = {"authorId": "user_b"}

        mock_post_ref = MagicMock()
        mock_post_ref.get.return_value = mock_post_doc

        mock_posts_collection = MagicMock()
        mock_posts_collection.document.return_value = mock_post_ref

        mock_chats_collection = MagicMock()

        # Mock finding existing chats (return empty list)
        mock_chats_where = MagicMock()
        mock_chats_collection.where.return_value = mock_chats_where
        mock_chats_where_limit = MagicMock()
        mock_chats_where.limit.return_value = mock_chats_where_limit
        mock_chats_where_limit.get.return_value = []

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "new_chat_123"
        mock_chats_collection.add.return_value = (None, mock_doc_ref)

        def collection_side_effect(name):
            if name == "posts": return mock_posts_collection
            if name == "chats": return mock_chats_collection
            return MagicMock()

        mock_db.collection.side_effect = collection_side_effect

        result = start_chat(mock_req)
        self.assertTrue(result["success"])
        self.assertEqual(result["chatId"], "new_chat_123")

if __name__ == '__main__':
    unittest.main()
