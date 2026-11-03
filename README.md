# Chat con su PDF (RAG + ChromaDB + RAGAS + LangSmith)

## ¿Para qué sirve?

Es un chat de consola donde usted hace preguntas y el asistente responde **solo con la información de un PDF**.
Si la respuesta no está en el documento, lo dice en lugar de inventarla.

Además permite **medir la solución**:

| Qué se mide | Herramienta | Resultado |
|---|---|---|
| **Precisión** de las respuestas | **RAGAS** | 4 métricas de 0 a 1 |
| **Precio** (tokens y dólares) | **LangSmith** | Coste por pregunta y por corrida |

El PDF que analiza es `pdfs/GUIA_Mininet_OpenFlow.pdf`: la guía de laboratorio de Mininet y OpenFlow (1 página, 5 puntos con sub-incisos: topologías, ping, enlaces, controlador externo y captura con Wireshark).

> La guía contiene las **preguntas del laboratorio, no sus respuestas**. El chat explica qué pide cada punto (topología, hosts, enlaces, pruebas), pero si le pide el comando de Mininet dirá que el documento no lo incluye.

## Cómo funciona

```
 INGESTA (una vez)                       CHAT (cada pregunta)
 PDF ──► texto ──► fragmentos            pregunta ──► embedding ──► ChromaDB
              │                                                        │
              ▼                                           5 fragmentos más parecidos
   embeddings ──► ChromaDB                                             │
                                          pregunta + fragmentos ──► LLM ──► respuesta (+ páginas)
```

## Requisitos

- Python 3.11 o superior y [uv](https://docs.astral.sh/uv/) (`uv --version`)
- Una clave de Anthropic (`ANTHROPIC_API_KEY`)
- Una clave de LangSmith (`LANGSMITH_API_KEY`, gratis en https://smith.langchain.com) para ver el coste
- ~1 GB libre: `sentence-transformers` instala PyTorch y descarga el modelo de embeddings (~470 MB) la primera vez

## Instalación

```powershell
cd chat-pdf-rag
uv sync                       # crea .venv e instala todo
copy .env.example .env        # luego edite .env y pegue sus claves
```

## Uso

**1. Indexar el PDF** (guarda los fragmentos en ChromaDB, carpeta `datos/chroma`):

```powershell
uv run python -m app.ingesta pdfs/GUIA_Mininet_OpenFlow.pdf
```

Puede repetirse sin problema: no duplica fragmentos. Para usar otro PDF, cámbiele la ruta.
Si cambia de documento y no quiere mezclarlos, borre antes la carpeta `datos`.

**2. Chatear:**

```powershell
uv run python -m app.chat
```

```
Usted: ¿Qué características tiene la topología del punto 3?
Asistente: Un switch, tres hosts y el controlador por omisión, con enlaces de 100 Mbps y 15 ms de retardo.
(páginas: 1)
```

Escriba `salir` para terminar.

**3. Medir la precisión (RAGAS):**

```powershell
uv run python -m app.evaluar
```

Hace las 13 preguntas de `app/preguntas_eval.json` al chat, las califica y muestra los promedios.
El detalle por pregunta queda en `resultados/ragas_<fecha>.csv`.

| Métrica | Qué responde | Si es baja… |
|---|---|---|
| `faithfulness` | ¿La respuesta se apoya solo en los fragmentos recuperados? | El LLM está inventando |
| `answer_relevancy` | ¿La respuesta contesta lo que se preguntó? | Respuestas desviadas o vagas |
| `context_precision` | ¿Los fragmentos útiles aparecen primero? | Hay mucho ruido en la recuperación |
| `context_recall` | ¿Los fragmentos traen todo lo necesario? | Hay que ajustar fragmentos o `K_RESULTADOS` |

**4. Ver el precio (LangSmith):**

Entre a https://smith.langchain.com → proyecto `agent-taller2-local` (el nombre sale de `LANGSMITH_AGENT_ID` en su `.env`; si usa `LANGSMITH_PROJECT=chat-pdf-rag` en su lugar, será ese). Cada pregunta aparece como una traza
`responder_pregunta` con sus pasos (`recuperar` y la llamada al LLM), tokens de entrada/salida,
**coste en dólares** y latencia. El total de una corrida de evaluación se ve sumando las trazas del proyecto.

> Para que LangSmith calcule dólares, el modelo debe tener precio configurado
> (Settings → Model pricing). Si `claude-sonnet-5-5` no aparece con precio, agréguelo con la tarifa vigente de Anthropic.
> Los tokens se registran siempre.

## Ajustes

Todo está en `app/config.py`: modelo, tamaño de fragmento (`TAM_FRAGMENTO`), solape y cantidad de fragmentos
recuperados (`K_RESULTADOS`). Cambie **un parámetro a la vez**, vuelva a ingerir (si tocó el tamaño de fragmento)
y repita `app.evaluar` para ver si las métricas suben o bajan, y cuánto cambia el coste en LangSmith.

## Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `Falta ANTHROPIC_API_KEY` | No creó `.env` a partir de `.env.example` |
| `La base está vacía` | Falta ejecutar la ingesta |
| `UnicodeEncodeError` en consola de Windows | Ejecute antes `$env:PYTHONUTF8 = "1"` |
| Error de dimensiones en ChromaDB | Cambió el modelo de embeddings: borre `datos/` y vuelva a ingerir |
| No aparecen trazas en LangSmith | Revise `LANGSMITH_TRACING=true` y `LANGSMITH_API_KEY`. No ponga a la vez `LANGSMITH_PROJECT` y `LANGSMITH_AGENT_ID`: LangSmith no traza y avisa "neither outranks the other" |
| La primera ejecución tarda | Descarga del modelo de embeddings; solo ocurre una vez |
