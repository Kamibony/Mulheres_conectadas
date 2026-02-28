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

@https_fn.on_call(region="southamerica-east1", memory=1024)
def share_experience(req: https_fn.CallableRequest) -> any:
    """
    Prijme text od používateľky, vytvorí z neho vektor (embedding)
    a nájde sémanticky podobné príspevky v databáze.
    """
    # 1. Získanie dát z požiadavky
    data = req.data
    text = data.get("text")
    
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
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        embeddings = model.get_embeddings([text])
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