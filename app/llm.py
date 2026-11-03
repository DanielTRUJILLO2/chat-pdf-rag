import os

import anthropic
from langsmith.wrappers import wrap_anthropic

from app.config import MODELO_LLM


def _cliente():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Falta ANTHROPIC_API_KEY en el archivo .env")
    # wrap_anthropic envía a LangSmith cada llamada con sus tokens (de ahí sale el coste)
    # cuando LANGSMITH_TRACING=true; si no, se comporta como el cliente normal.
    return wrap_anthropic(anthropic.Anthropic())


def llamar_llm(sistema: str, mensajes: list[dict], max_tokens: int = 1024) -> str:
    respuesta = _cliente().messages.create(
        model=MODELO_LLM, max_tokens=max_tokens, system=sistema, messages=mensajes
    )
    return "".join(b.text for b in respuesta.content if hasattr(b, "text"))
