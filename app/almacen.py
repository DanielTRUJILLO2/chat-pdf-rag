import chromadb
from chromadb.utils import embedding_functions

from app.config import COLECCION, MODELO_EMBEDDINGS, RUTA_CHROMA


def crear_cliente(ruta: str = RUTA_CHROMA) -> chromadb.ClientAPI:
    """Crea (o abre) una base vectorial persistente en disco."""
    return chromadb.PersistentClient(path=ruta)


def funcion_embeddings():
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODELO_EMBEDDINGS)


def obtener_coleccion(cliente=None, nombre: str = COLECCION):
    """Devuelve la colección de fragmentos, con distancia coseno."""
    cliente = cliente or crear_cliente()
    return cliente.get_or_create_collection(
        name=nombre,
        embedding_function=funcion_embeddings(),
        metadata={"hnsw:space": "cosine"},
    )
