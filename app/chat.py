"""Chat de consola sobre el PDF indexado.  Uso: uv run python -m app.chat"""
import anthropic

from app.rag import responder


def main():
    print("Chat con su PDF. Escriba 'salir' para terminar.\n")
    historial: list[dict] = []
    while True:
        texto = input("Usted: ").strip()
        if texto.lower() in {"salir", "exit"}:
            break
        if not texto:
            continue
        try:
            r = responder(texto, historial)
        except anthropic.AuthenticationError:
            print("La clave ANTHROPIC_API_KEY del archivo .env no es válida. Corríjala y vuelva a abrir el chat.")
            break
        print(f"Asistente: {r['respuesta']}\n(páginas: {', '.join(map(str, r['paginas']))})\n")
        # El historial guarda solo pregunta y respuesta, sin el contexto, para no inflar los tokens
        historial += [{"role": "user", "content": texto},
                      {"role": "assistant", "content": r["respuesta"]}]
        historial = historial[-6:]


if __name__ == "__main__":
    main()
