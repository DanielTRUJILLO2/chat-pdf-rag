from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")

RUTA_CHROMA = str(RAIZ / "datos" / "chroma")
COLECCION = "documentos"

MODELO_LLM = "claude-sonnet-5-5"  # Cambie el modelo según su proveedor
MODELO_EMBEDDINGS = "paraphrase-multilingual-MiniLM-L12-v2"  # multilingüe: sirve para español

TAM_FRAGMENTO = 450     # caracteres por fragmento (el modelo de embeddings solo lee ~128 tokens)
SOLAPE = 80             # caracteres compartidos entre fragmentos contiguos
K_RESULTADOS = 5        # fragmentos que se recuperan por pregunta
