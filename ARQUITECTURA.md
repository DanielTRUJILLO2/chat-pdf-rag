# Arquitectura: qué hace cada archivo y carpeta

## Qué había en la carpeta `RETO CLASE`

| Elemento | Qué es | Relación con este proyecto |
|---|---|---|
| `Tutorial_Memoria_RAG.docx.pdf` | Tutorial de 30 páginas: memoria a corto, medio y largo plazo con RAG, ChromaDB y sentence-transformers | Es el material teórico del que parte el reto (RAG, ChromaDB, embeddings); no se indexa |
| `memoria-rag.zip` | Proyecto resultado del tutorial: un chat con memoria de conversación | Es la **base de estilo**: de allí se reutilizaron la idea de `almacen.py`, el modelo de embeddings y la llamada al LLM. Pero **no** responde preguntas sobre un PDF: guarda lo que el usuario dice, no un documento |
| `GUIA Laboratorio Mininet y Openflow (2).pdf` | Guía de laboratorio de redes (Mininet/OpenFlow), 1 página con 5 puntos | **Es el PDF que analiza el chatbot** (copiado a `chat-pdf-rag/pdfs/GUIA_Mininet_OpenFlow.pdf`). Contiene preguntas del laboratorio, no respuestas |
| `chat-pdf-rag/` | La aplicación nueva | Ver abajo |

> `memoria-rag.zip` incluye un archivo `.env` (que puede tener claves) y una carpeta `.venv` con miles de archivos.
> No lo comparta ni lo suba a un repositorio tal cual.

## Estructura de `chat-pdf-rag/`

```
chat-pdf-rag/
├── app/                       Código de la aplicación
│   ├── __init__.py            Marca la carpeta como paquete de Python (vacío)
│   ├── config.py              Parámetros y carga del .env
│   ├── almacen.py             Conexión con ChromaDB y modelo de embeddings
│   ├── ingesta.py             PDF → fragmentos → ChromaDB
│   ├── llm.py                 Llamada al LLM (con LangSmith)
│   ├── rag.py                 Recuperar + responder (corazón del RAG)
│   ├── chat.py                Chat de consola
│   ├── evaluar.py             Evaluación con RAGAS
│   └── preguntas_eval.json    Preguntas y respuestas de referencia para evaluar
├── pdfs/                      PDFs a consultar
│   └── GUIA_Mininet_OpenFlow.pdf
├── datos/chroma/              Base vectorial (se crea sola al ingerir)
├── resultados/                CSV de cada evaluación RAGAS (se crea sola)
├── iniciar.ps1                Menú para indexar, chatear y evaluar
├── .env.example               Plantilla de variables (claves); se copia a .env
├── .env                       Sus claves reales (usted lo crea; no se sube)
├── .gitignore                 Excluye .venv, .env, datos y resultados
├── pyproject.toml             Dependencias del proyecto (uv)
├── uv.lock                    Versiones exactas instaladas (generado por uv)
├── README.md                  Para qué sirve y cómo se usa
└── ARQUITECTURA.md            Este archivo
```

## Archivo por archivo

| Archivo | Qué hace | Funciones principales |
|---|---|---|
| `app/config.py` | Un único lugar para ajustar el sistema y cargar el `.env` | Constantes: `MODELO_LLM`, `MODELO_EMBEDDINGS`, `TAM_FRAGMENTO`, `SOLAPE`, `K_RESULTADOS`, `RUTA_CHROMA` |
| `app/almacen.py` | Abre ChromaDB en disco y define cómo se convierte el texto en vectores (modelo multilingüe, distancia coseno) | `crear_cliente`, `funcion_embeddings`, `obtener_coleccion` |
| `app/ingesta.py` | Lee el PDF página por página, normaliza espacios, lo parte en fragmentos (con solape, cortando en final de frase) y los guarda con metadatos `fuente` y `pagina`. Los IDs son un hash del contenido, así que re-ingerir no duplica | `leer_paginas`, `partir`, `ingerir` |
| `app/llm.py` | Único punto de contacto con el LLM. Envuelve el cliente de Anthropic con LangSmith | `llamar_llm` |
| `app/rag.py` | Busca los `K_RESULTADOS` fragmentos más parecidos a la pregunta y se los entrega al LLM con la orden de responder solo con ese contexto. Devuelve respuesta, fragmentos y páginas | `recuperar`, `responder` |
| `app/chat.py` | Bucle de consola; conserva los últimos 3 intercambios (sin el contexto, para no inflar tokens) | `main` |
| `app/evaluar.py` | Pasa las preguntas por el RAG, arma el dataset y lo califica con RAGAS; guarda un CSV | `construir_dataset`, `main` |
| `app/preguntas_eval.json` | 13 preguntas con respuesta de referencia redactada a partir del PDF de Mininet. Las dos últimas ("comando exacto para 5 hosts" y "capital de Francia") comprueban que el sistema reconozca lo que el documento no dice | — |

### Carpetas

- **`pdfs/`**: documentos de entrada. La ingesta acepta cualquier ruta, pero conviene dejarlos aquí.
- **`datos/chroma/`**: la base ChromaDB (`chroma.sqlite3` + índices). Borrarla equivale a "olvidar" el PDF; se regenera con la ingesta.
- **`resultados/`**: un CSV por evaluación, con las 4 métricas de cada pregunta, para comparar corridas.

## Flujo de datos

1. **Ingesta**: `ingesta.py` extrae el texto, lo parte y llama a `almacen.py` para guardarlo; Chroma calcula el embedding de cada fragmento.
2. **Pregunta**: `chat.py` → `rag.responder` → `rag.recuperar` consulta Chroma → arma el prompt → `llm.llamar_llm`.
3. **Evaluación**: `evaluar.py` repite el paso 2 con las preguntas del JSON y luego RAGAS califica.

## Cómo se incorporó LangSmith (precio)

LangSmith registra cada paso de la app. Se hizo con tres piezas pequeñas:

1. **Variables en `.env`**: `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY` y un destino: `LANGSMITH_AGENT_ID` (las trazas van a `agent-taller2-local`) o `LANGSMITH_PROJECT`, pero no ambos. Con eso el SDK activa el envío de trazas; sin ellas la app funciona igual.
2. **`wrap_anthropic` en `llm.py`**: envuelve el cliente de Anthropic. Cada `messages.create` se registra como una ejecución de tipo LLM con **tokens de entrada y salida**, que LangSmith multiplica por el precio del modelo para dar el **coste en dólares**.
3. **`@traceable` en `rag.py`**: `responder` genera la traza padre (`responder_pregunta`) y `recuperar` un paso de tipo *retriever* con los fragmentos hallados. Así el coste de la llamada al LLM queda dentro de la pregunta que lo originó, y se ve qué parte es recuperación y cuál es generación.

Dónde se ve: LangSmith → *Tracing* → proyecto `agent-taller2-local`: columnas de tokens, coste y latencia por pregunta, y totales del proyecto.
Como `evaluar.py` pasa por el mismo código, **cada evaluación también queda trazada**, y se puede comparar el coste entre, por ejemplo, `K_RESULTADOS=4` y `K_RESULTADOS=6`.

Nota: el precio por token lo define LangSmith según el modelo. Si no reconoce `claude-sonnet-5-5`, configure su tarifa en *Settings → Model pricing*.

## Cómo se incorporó RAGAS (precisión)

RAGAS califica un sistema RAG usando un LLM como juez. Se hizo en `evaluar.py`:

1. **Dataset** (`EvaluationDataset`): por cada pregunta se guarda `user_input` (pregunta), `response` (lo que contestó el chat), `retrieved_contexts` (fragmentos que recuperó Chroma) y `reference` (respuesta correcta del JSON).
2. **Juez y embeddings**: `ChatAnthropic` (mismo modelo) y el mismo modelo de embeddings del proyecto, envueltos con `LangchainLLMWrapper` / `LangchainEmbeddingsWrapper`.
3. **Métricas**: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`. Las dos primeras miden la **generación**; las dos últimas, la **recuperación**. Por eso sirven para saber *dónde* mejorar.
4. **Salida**: promedios en consola y CSV en `resultados/`.

Importante: el propio juez gasta tokens, y es lo más caro: en la primera corrida real, calificar con RAGAS costó ~211 000 tokens (~US$0,61), mientras que cada pregunta del chat cuesta ~US$0,003. Aparece en LangSmith como una traza `ragas evaluation`.

Dependencias: RAGAS 0.3.9 no es compatible con `langchain-community` 0.4; por eso `pyproject.toml` fija `ragas==0.3.9` y `langchain-community<0.4`. No actualice una sin probar la otra.

## Decisiones de diseño y límites

- **Fragmentos de 450 caracteres**: el modelo de embeddings solo lee ~128 tokens; con 900 caracteres la segunda mitad no se "veía" y la recuperación fallaba (se comprobó con el tutorial). El solape siempre arranca en límite de palabra.
- **5 fragmentos por pregunta**: la guía es de una sola página y queda en 8 fragmentos, así que cada pregunta ve más de la mitad del documento. Es buen caso para ver en RAGAS que `context_precision` es baja y `context_recall` alta.
- **El PDF no trae respuestas**: el sistema solo puede explicar qué pide cada punto. Es una limitación del documento, no del chat.
- **Resultados de la primera corrida real (PDF de Mininet, 13 preguntas)**: `faithfulness` 0,985; `answer_relevancy` 0,752; `context_precision` 0,731; `context_recall` 1,0. Lectura: el modelo casi no inventa y la recuperación siempre trae lo necesario, pero trae fragmentos de más (el PDF es de una página y se recuperan 5 de 8). `answer_relevancy` es 0 en la pregunta fuera del documento (capital de Francia), lo esperado porque la respuesta correcta es "no lo menciona".
- **RAGAS y `temperature`**: `claude-sonnet-5-5` rechaza el parámetro `temperature` que RAGAS envía; por eso `evaluar.py` usa `bypass_temperature=True`.
