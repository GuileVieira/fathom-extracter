import os
import requests
import json
import re

def resolver_refs_com_azure_llm(snapshot_text: str, elementos_desejados: list) -> dict:
    """
    Consulta a Azure OpenAI para obter os 'ref' corretos com base no snapshot e lista de elementos.

    Args:
        snapshot_text (str): Texto bruto (YAML) da estrutura da página.
        elementos_desejados (list): Lista com nomes dos elementos desejados (ex: ["Transcript"]).

    Returns:
        dict: Mapeamento de nome de elemento para ref, ex: { "Transcript": "s2e467" }
    """

    AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

    if not AZURE_API_KEY or not AZURE_ENDPOINT or not AZURE_DEPLOYMENT:
        raise EnvironmentError("Faltam variáveis no .env: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME")

    nome_elemento = elementos_desejados[0]

    prompt_base = f"""
Você é um agente que analisa snapshots de páginas da web representados em YAML. Seu trabalho é encontrar o `ref` (referência) de um elemento com base em seu nome visual.

## Snapshot da Página (YAML):
```yaml
{snapshot_text}
```

## Elemento desejado:
- {nome_elemento}

## Instruções:
- Retorne apenas um JSON no formato: {{ "{nome_elemento}": "ref_correspondente" }}
- NÃO inclua explicações, comentários ou outros textos além do JSON.
- NÃO envolva a resposta com marcações tipo ```json ou ```.
"""

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }

    url = f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"

    data = {
        "messages": [
            {"role": "system", "content": prompt_base},
            {"role": "user", "content": "Por favor, retorne o JSON solicitado."}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"].strip()

    # Remove marcações tipo ```json ... ```
    content = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", content)

    try:
        refs = json.loads(content)
        return refs
    except json.JSONDecodeError:
        raise ValueError(f"Erro ao interpretar resposta da LLM: {content}")
