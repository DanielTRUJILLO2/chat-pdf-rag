"""Lee un PDF, lo parte en fragmentos y los guarda en ChromaDB.

Uso: uv run python -m app.ingesta pdfs/Tutorial_Memoria_RAG.pdf
"""
import hashlib
import re
import sys
from pathlib import Path

from pypdf import PdfReader

from app.almacen import obtener_coleccion
from app.config import SOLAPE, TAM_FRAGMENTO


def leer_paginas(ruta: str) -> list[tuple[int, str]]:
    """Devuelve (número de página, texto limpio) de cada página con contenido."""
    paginas = []
    for i, pagina in enumerate(PdfReader(ruta).pages, start=1):
        # El PDF trae saltos de línea y espacios dobles entre palabras: se normalizan
        texto = re.sub(r"\s+", " ", pagina.extract_text() or "").strip()
        if texto:
            paginas.append((i, texto))
    return paginas


def partir(texto: str, tam: int = TAM_FRAGMENTO, solape: int = SOLAPE) -> list[str]:
    """Parte el texto en fragmentos de ~tam caracteres, cortando al final de una frase si es posible."""
    fragmentos, inicio = [], 0
    while inicio < len(texto):
        fin = min(inicio + tam, len(texto))
        if fin < len(texto):
            corte = texto.rfind(". ", inicio + tam // 2, fin)
            if corte != -1:
                fin = corte + 1
        fragmentos.append(texto[inicio:fin].strip())
        if fin >= len(texto):
            break
        inicio = max(fin - solape, inicio + 1)
        # El solape no debe empezar a mitad de palabra
        espacio = texto.find(" ", inicio, fin)
        if espacio != -1:
            inicio = espacio + 1
    return [f for f in fragmentos if f]


def ingerir(ruta: str) -> int:
    """Indexa el PDF. Es idempotente: volver a ingerirlo no duplica fragmentos."""
    fuente = Path(ruta).name
    ids, docs, metas = [], [], []
    for pagina, texto in leer_paginas(ruta):
        for n, fragmento in enumerate(partir(texto)):
            ids.append(hashlib.sha1(f"{fuente}|{pagina}|{n}|{fragmento}".encode()).hexdigest())
            docs.append(fragmento)
            metas.append({"fuente": fuente, "pagina": pagina})
    obtener_coleccion().upsert(ids=ids, documents=docs, metadatas=metas)
    return len(ids)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python -m app.ingesta ruta/al/archivo.pdf")
    print(f"{ingerir(sys.argv[1])} fragmentos guardados en ChromaDB.")
