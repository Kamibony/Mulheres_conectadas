import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

from firebase_functions import https_fn
from firebase_admin import initialize_app, firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
import vertexai
from vertexai.language_models import TextEmbeddingModel
import logging

# Konfigurácia logovania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konštanty pre validáciu a vyhľadávanie
MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 1000

# Privátne globálne premenné pre lazy inicializáciu (Warm Start optimalizácia)
_db = None
_embedding_model = None

def get_db():
    global _db
    if _db is None:
        try:
            initialize_app()
        except ValueError:
            # app already initialized
            pass
        except Exception:
            logger.exception("Firebase/Firestore initialization failed")

        try:
            _db = firestore.client()
        except Exception:
            logger.exception("Firestore client initialization failed")
    return _db

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        project_id = os.environ.get("APP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("APP_PROJECT_ID environment variable not set.")

        try:
            vertexai.init(project=project_id, location="southamerica-east1")
            _embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        except Exception:
            logger.exception("Failed to initialize Vertex AI model globally")
    return _embedding_model

@https_fn.on_call(region="southamerica-east1", memory=1024)
def share_experience(req: https_fn.CallableRequest) -> Any:
    """
    Prijme text od používateľky, vytvorí z neho vektor (embedding)
    a nájde sémanticky podobné príspevky v databáze.
    """
    db = get_db()
    embedding_model = get_embedding_model()
    if not req.auth:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="Usuária não autenticada."
        )

    # 1. Získanie dát z požiadavky
    data = req.data
    text = data.get("text")
    
    if not isinstance(text, str):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="O texto fornecido deve ser uma string."
        )

    if not text or len(text) < MIN_TEXT_LENGTH:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="O texto é muito curto."
        )

    if len(text) > MAX_TEXT_LENGTH:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="O texto é muito longo."
        )
        
    user_id = req.auth.uid

    try:
        # 2. Vytvorenie vektora (Embedding) cez Vertex AI
        # Využíva globálne inicializovaný model pre lepší výkon
        embeddings = embedding_model.get_embeddings([text])
        vector_values = embeddings[0].values
        
        posts_ref = db.collection("posts")

        # 3. Sémantické vyhľadávanie (Vector Search)
        # Hľadáme príspevky s najpodobnejším významom PRED uložením nového príspevku
        vector_query = posts_ref.find_nearest(
            vector_field="embedding",
            query_vector=Vector(vector_values),
            distance_measure=DistanceMeasure.COSINE,
            limit=5
        )
        
        docs = vector_query.stream()
        
        matches = []
        for doc in docs:
            doc_data = doc.to_dict()
            matches.append({
                "id": doc.id,
                "text": doc_data.get("text")
            })
                
        # 4. Uloženie nového príspevku do Firestore
        new_post = {
            "text": text,
            "embedding": Vector(vector_values), # Uloženie ako vektorový typ
            "authorId": user_id,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        _, doc_ref = posts_ref.add(new_post)

        # 5. Vrátenie výsledkov na frontend
        return {
            "success": True,
            "myPostId": doc_ref.id,
            "resonances": matches
        }

    except Exception as e:
        print(f"Chyba: {str(e)}")
        return {"error": "Vyskytla sa chyba pri spracovaní."}

@https_fn.on_call(region="southamerica-east1", memory=256)
def start_chat(req: https_fn.CallableRequest) -> Any:
    """
    Začne chat s autorkou príspevku.
    """
    db = get_db()
    data = req.data
    target_post_id = data.get("target_post_id")

    if not req.auth or not req.auth.uid:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="Usuária não autenticada."
        )

    if not target_post_id:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="O target_post_id é obrigatório."
        )

    if not isinstance(target_post_id, str):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="O target_post_id deve ser uma string."
        )

    try:
        # Get target post to find target author
        post_ref = db.collection("posts").document(target_post_id)
        post_doc = post_ref.get()

        if not post_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message="Post não encontrado."
            )

        target_author_id = post_doc.to_dict().get("authorId")
        if not target_author_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INTERNAL,
                message="Erro interno: autor do post não encontrado."
            )

        # Prevent self-chat
        if req.auth.uid == target_author_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Você não pode iniciar um chat consigo mesma."
            )

        # Check if chat already exists
        chats_ref = db.collection("chats")
        existing_chats = chats_ref.where("users", "in", [[req.auth.uid, target_author_id], [target_author_id, req.auth.uid]]).limit(1).get()

        if existing_chats:
            return {
                "success": True,
                "chatId": existing_chats[0].id
            }

        # Create chat document if it doesn't exist
        new_chat = {
            "status": "anonymous",
            "users": [req.auth.uid, target_author_id],
            "timestamp": firestore.SERVER_TIMESTAMP
        }

        _, doc_ref = chats_ref.add(new_chat)

        return {
            "success": True,
            "chatId": doc_ref.id
        }

    except Exception as e:
        if isinstance(e, https_fn.HttpsError):
            raise e
        print(f"Chyba: {str(e)}")
        return {"error": "Vyskytla sa chyba pri spracovaní."}



def _update_chat_status_tx(transaction, chat_ref, req_auth_uid):
    snapshot = chat_ref.get(transaction=transaction)
    if not snapshot.exists:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message="Chat não encontrado."
        )

    chat_data = snapshot.to_dict()
    users = chat_data.get("users", [])
    current_status = chat_data.get("status", "anonymous")

    if req_auth_uid not in users:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            message="Acesso negado."
        )

    if current_status == "revealed":
        return "revealed"

    uid_index = users.index(req_auth_uid)
    user_label = "a" if uid_index == 0 else "b"
    other_label = "b" if uid_index == 0 else "a"

    pending_status = f"reveal_pending_{user_label}"
    other_pending_status = f"reveal_pending_{other_label}"

    new_status = current_status
    if current_status == "anonymous":
        new_status = pending_status
    elif current_status == other_pending_status:
        new_status = "revealed"
    elif current_status == pending_status:
        pass # Already requested

    if new_status != current_status:
        transaction.update(chat_ref, {"status": new_status})

    return new_status

@https_fn.on_call(region="southamerica-east1", memory=256)
def request_reveal(req: https_fn.CallableRequest) -> Any:

    """
    Požiada o odhalenie identity.
    """
    db = get_db()
    data = req.data
    chat_id = data.get("chatId")
    identity = data.get("identity")

    if not req.auth or not req.auth.uid:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="Usuária não autenticada."
        )

    if not chat_id or not identity:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="O chatId e a identity são obrigatórios."
        )

    if not isinstance(chat_id, str) or not isinstance(identity, str):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="O chatId e a identity devem ser strings."
        )


    try:
        chat_ref = db.collection("chats").document(chat_id)

        transactional_update = firestore.transactional(_update_chat_status_tx)
        new_status = transactional_update(db.transaction(), chat_ref, req.auth.uid)

        # Save identity
        identity_ref = db.collection("chats").document(chat_id).collection("identities").document(req.auth.uid)
        identity_ref.set({"identity": identity}, merge=True)

        return {
            "success": True,
            "status": new_status
        }

    except Exception as e:
        if isinstance(e, https_fn.HttpsError):
            raise e
        print(f"Chyba: {str(e)}")
        return {"error": "Vyskytla sa chyba pri spracovaní."}
