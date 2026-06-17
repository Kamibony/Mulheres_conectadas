import os
from dotenv import load_dotenv

load_dotenv()

from firebase_functions import https_fn, options
from firebase_admin import initialize_app, firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Inicializácia Firebase a Firestore
try:
    initialize_app()
    db = firestore.client()
except Exception as e:
    print(f"Warning: Firebase/Firestore initialization failed: {e}")
    db = None

# Konštanty pre validáciu a vyhľadávanie
MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 1000

# Inicializácia Vertex AI (použije ID projektu z prostredia Firebase)
# Tu musíš zadať lokáciu, ideálne rovnakú, akú si vybral pri tvorbe Firestore
project_id = os.environ.get("APP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
if not project_id:
    raise ValueError("APP_PROJECT_ID environment variable not set.")
vertexai.init(project=project_id, location="us-central1") # Zmeň na "southamerica-east1", ak si databázu dal do Brazílie

_text_embedding_model = None

@https_fn.on_call(region="southamerica-east1", memory=1024)
def share_experience(req: https_fn.CallableRequest) -> any:
    """
    Prijme text od používateľky, vytvorí z neho vektor (embedding)
    a nájde sémanticky podobné príspevky v databáze.
    """
    global _text_embedding_model
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
        
    # Anonymné ID (ak je používateľka prihlásená anonymne)
    user_id = req.auth.uid if req.auth else "anonymous"

    try:
        # 2. Vytvorenie vektora (Embedding) cez Vertex AI
        if _text_embedding_model is None:
            _text_embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

        embeddings = _text_embedding_model.get_embeddings([text])
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
def start_chat(req: https_fn.CallableRequest) -> any:
    """
    Začne chat s autorkou príspevku.
    """
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


@https_fn.on_call(region="southamerica-east1", memory=256)
def request_reveal(req: https_fn.CallableRequest) -> any:
    """
    Požiada o odhalenie identity.
    """
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

    if not isinstance(identity, str):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="A identity deve ser uma string."
        )

    if len(identity) > 100:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="A identity é muito longa."
        )

    try:
        chat_ref = db.collection("chats").document(chat_id)

        @firestore.transactional
        def update_chat_status(transaction, chat_ref):
            snapshot = chat_ref.get(transaction=transaction)
            if not snapshot.exists:
                raise https_fn.HttpsError(
                    code=https_fn.FunctionsErrorCode.NOT_FOUND,
                    message="Chat não encontrado."
                )

            chat_data = snapshot.to_dict()
            users = chat_data.get("users", [])
            current_status = chat_data.get("status", "anonymous")

            if req.auth.uid not in users:
                raise https_fn.HttpsError(
                    code=https_fn.FunctionsErrorCode.PERMISSION_DENIED,
                    message="Acesso negado."
                )

            if current_status == "revealed":
                return "revealed"

            uid_index = users.index(req.auth.uid)
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

        new_status = update_chat_status(db.transaction(), chat_ref)

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
