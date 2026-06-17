import unittest
from unittest.mock import MagicMock, patch
import sys
import os

class TestRevealChat(unittest.TestCase):
    def setUp(self):
        super().setUp()
        for mod in ['main', 'firebase_functions', 'firebase_admin', 'google.cloud.firestore_v1.vector', 'google.cloud.firestore_v1.base_vector_query', 'vertexai', 'vertexai.language_models', 'dotenv']:
            if mod in sys.modules:
                del sys.modules[mod]

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
        self.mock_firebase_functions.https_fn.FunctionsErrorCode.UNAUTHENTICATED = "UNAUTHENTICATED"
        sys.modules['firebase_functions'] = self.mock_firebase_functions

        self.mock_firebase_admin = MagicMock()
        self.mock_firestore = MagicMock()
        self.mock_db = MagicMock()
        self.mock_firestore.client.return_value = self.mock_db
        self.mock_firebase_admin.firestore = self.mock_firestore
        sys.modules['firebase_admin'] = self.mock_firebase_admin
        sys.modules['google.cloud.firestore_v1.vector'] = MagicMock()
        sys.modules['google.cloud.firestore_v1.base_vector_query'] = MagicMock()
        sys.modules['vertexai'] = MagicMock()
        sys.modules['vertexai.language_models'] = MagicMock()
        sys.modules['dotenv'] = MagicMock()

        os.environ["APP_PROJECT_ID"] = "test-project"
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        import main
        self.main = main

        # Fix transaction wrapper for mock
        def mock_transactional(func):
            def wrapper(transaction, *args, **kwargs):
                return func(transaction, *args, **kwargs)
            return wrapper
        self.main.firestore.transactional = mock_transactional

    def test_request_reveal_invalid_chat_id_type(self):
        mock_req = MagicMock()
        mock_req.auth.uid = "user_a"
        mock_req.data = {"chatId": {"invalid": "type"}, "identity": "ig_usera"}

        with self.assertRaises(self.main.https_fn.HttpsError) as context:
            self.main.request_reveal(mock_req)

        self.assertEqual(context.exception.code, "INVALID_ARGUMENT")
        self.assertEqual(context.exception.message, "O chatId e a identity devem ser strings.")

    def test_request_reveal_invalid_identity_type(self):
        mock_req = MagicMock()
        mock_req.auth.uid = "user_a"
        mock_req.data = {"chatId": "chat_123", "identity": {"invalid": "type"}}

        with self.assertRaises(self.main.https_fn.HttpsError) as context:
            self.main.request_reveal(mock_req)

        self.assertEqual(context.exception.code, "INVALID_ARGUMENT")
        self.assertEqual(context.exception.message, "O chatId e a identity devem ser strings.")

    def test_request_reveal(self):
        mock_req = MagicMock()
        mock_req.auth.uid = "user_a"
        mock_req.data = {"chatId": "chat_123", "identity": "ig_usera"}

        mock_chat_doc = MagicMock()
        mock_chat_doc.exists = True
        mock_chat_doc.to_dict.return_value = {
            "status": "anonymous",
            "users": ["user_a", "user_b"]
        }

        mock_chat_ref = MagicMock()
        mock_chat_ref.get.return_value = mock_chat_doc

        mock_chats_collection = MagicMock()
        mock_chats_collection.document.return_value = mock_chat_ref

        # The global main variables are now private, mock them directly via test class setup
        # or handle them here. We assume they exist or can be patched.
        # Ensure _db exists on self.main (we may need to initialize it if this test class doesn't)
        if not hasattr(self.main, '_db') or self.main._db is None:
            self.main._db = MagicMock()

        self.main._db.collection.return_value = mock_chats_collection

        mock_transaction = MagicMock()
        self.main._db.transaction.return_value = mock_transaction

        result = self.main.request_reveal(mock_req)

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "reveal_pending_a")

        # Verify transaction.update was called
        mock_transaction.update.assert_called_with(mock_chat_ref, {"status": "reveal_pending_a"})

        # Verify identity saving
        mock_identity_ref = mock_chat_ref.collection.return_value.document.return_value
        mock_identity_ref.set.assert_called_with({"identity": "ig_usera"}, merge=True)

if __name__ == '__main__':
    unittest.main()
