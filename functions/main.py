import os
from firebase_functions import https_fn
from firebase_admin import initialize_app, firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Inicializácia Firebase a Firestore
initialize_app()
db = firestore.client()

# Konštanty pre validáciu a vyhľadávanie
MIN_TEXT_LENGTH = 10

# Inicializácia Vertex AI (použije ID projektu z prostredia Firebase)
# Tu musíš zadať lokáciu, ideálne rovnakú, akú si vybral pri tvorbe Firestore
project_id = os.environ.get("GCP_PROJECT") 
vertexai.init(project=project_id, location="us-central1") # Zmeň na "southamerica-east1", ak si databázu dal do Brazílie

@https_fn.on_call()
def share_experience(req: https_fn.CallableRequest) -> any:
    """
    Prijme text od používateľky, vytvorí z neho vektor (embedding)
    a nájde sémanticky podobné príspevky v databáze.
    """
    # 1. Získanie dát z požiadavky
    data = req.data
    text = data.get("text")
    
    if not text or len(text) < MIN_TEXT_LENGTH:
        return {"error": "O texto é muito curto."} # Text je príliš krátky
        
    # Anonymné ID (ak je používateľka prihlásená anonymne)
    user_id = req.auth.uid if req.auth else "anonymous"

    try:
        # 2. Vytvorenie vektora (Embedding) cez Vertex AI
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        embeddings = model.get_embeddings([text])
        vector_values = embeddings[0].values
        
        # 3. Uloženie nového príspevku do Firestore
        posts_ref = db.collection("posts")
        new_post = {
            "text": text,
            "embedding": Vector(vector_values), # Uloženie ako vektorový typ
            "authorId": user_id,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        _, doc_ref = posts_ref.add(new_post)
        
        # 4. Sémantické vyhľadávanie (Vector Search)
        # Hľadáme príspevky s najpodobnejším významom
        vector_query = posts_ref.find_nearest(
            vector_field="embedding",
            query_vector=Vector(vector_values),
            distance_measure=DistanceMeasure.COSINE,
            limit=6
        )
        
        docs = vector_query.stream()
        
        matches = []
        for doc in docs:
            # Preskočíme príspevok, ktorý sme práve uložili
            if doc.id != doc_ref.id:
                doc_data = doc.to_dict()
                matches.append({
                    "id": doc.id,
                    "text": doc_data.get("text")
                })

            if len(matches) >= 5:
                break
                
        # 5. Vrátenie výsledkov na frontend
        return {
            "success": True,
            "myPostId": doc_ref.id,
            "resonances": matches
        }

    except Exception as e:
        print(f"Chyba: {str(e)}")
        return {"error": "Vyskytla sa chyba pri spracovaní."}