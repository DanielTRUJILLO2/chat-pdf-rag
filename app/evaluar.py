"""Evalúa el chat con RAGAS (precisión de las respuestas).  Uso: uv run python -m app.evaluar

Cada pregunta pasa por el RAG real; así LangSmith registra tokens y coste de la corrida,
y RAGAS puntúa las respuestas y los fragmentos recuperados.
"""
import json
import time
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

from app.config import MODELO_EMBEDDINGS, MODELO_LLM, RAIZ
from app.rag import responder

PREGUNTAS = Path(__file__).with_name("preguntas_eval.json")


def construir_dataset() -> EvaluationDataset:
    filas = []
    for item in json.loads(PREGUNTAS.read_text(encoding="utf-8")):
        r = responder(item["pregunta"])
        filas.append({
            "user_input": item["pregunta"],
            "retrieved_contexts": r["contextos"],
            "response": r["respuesta"],
            "reference": item["referencia"],
        })
        print(f"  OK {item['pregunta']}")
    return EvaluationDataset.from_list(filas)


def main():
    print("1/2 Generando respuestas con el RAG...")
    dataset = construir_dataset()

    print("2/2 Calificando con RAGAS (el LLM actúa como juez)...")
    # bypass_temperature: este modelo rechaza el parámetro temperature que RAGAS envía por defecto
    juez = LangchainLLMWrapper(ChatAnthropic(model=MODELO_LLM, max_tokens=4096), bypass_temperature=True)
    embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=MODELO_EMBEDDINGS))
    resultado = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=juez,
        embeddings=embeddings,
    )

    tabla = resultado.to_pandas()
    carpeta = RAIZ / "resultados"
    carpeta.mkdir(exist_ok=True)
    archivo = carpeta / f"ragas_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    tabla.to_csv(archivo, index=False, encoding="utf-8-sig")

    print("\n=== Promedios RAGAS (0 a 1, más alto es mejor) ===")
    for metrica in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
        print(f"{metrica:20s} {tabla[metrica].mean():.3f}")
    print(f"\nDetalle por pregunta: {archivo}")
    print("El coste (tokens y dólares) de esta corrida está en LangSmith, en el proyecto LANGSMITH_PROJECT.")


if __name__ == "__main__":
    main()
