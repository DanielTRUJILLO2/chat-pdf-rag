from langsmith import traceable

from app.almacen import obtener_coleccion
from app.config import K_RESULTADOS
from app.llm import llamar_llm

SISTEMA = (
    "Usted responde preguntas sobre un documento PDF. Use SOLO el contexto entregado. "
    "Si la respuesta no está en el contexto, diga que el documento no lo menciona. "
    "Responda en español y de forma concisa."
)


@traceable(run_type="retriever", name="recuperar")
def recuperar(pregunta: str, k: int = K_RESULTADOS) -> list[dict]:
    coleccion = obtener_coleccion()
    if coleccion.count() == 0:
        raise RuntimeError("La base está vacía. Primero ejecute: python -m app.ingesta <archivo.pdf>")
    r = coleccion.query(query_texts=[pregunta], n_results=min(k, coleccion.count()))
    # LangSmith reconoce este formato (page_content + metadata) como documentos recuperados
    return [
        {"page_content": doc, "type": "Document", "metadata": meta}
        for doc, meta in zip(r["documents"][0], r["metadatas"][0])
    ]


@traceable(name="responder_pregunta")
def responder(pregunta: str, historial: list[dict] | None = None) -> dict:
    """RAG completo: recupera fragmentos del PDF y pide al LLM que conteste con ellos."""
    docs = recuperar(pregunta)
    contexto = "\n\n".join(f"[p. {d['metadata']['pagina']}] {d['page_content']}" for d in docs)
    mensajes = (historial or []) + [
        {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"}
    ]
    return {
        "respuesta": llamar_llm(SISTEMA, mensajes),
        "contextos": [d["page_content"] for d in docs],
        "paginas": sorted({d["metadata"]["pagina"] for d in docs}),
    }
