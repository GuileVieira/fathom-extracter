import json
import os
import requests
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

def enviar_para_llm_azure(dialogo_formatado: str, prompt_base: str, output_json_path: str) -> dict:
    """
    Envia um diálogo para a Azure OpenAI, interpreta a resposta como JSON,
    e salva somente o output parseado em um array JSON.

    Args:
        dialogo_formatado (str): Texto do diálogo formatado.
        prompt_base (str): Prompt de sistema para o modelo.
        output_json_path (str): Caminho do arquivo JSON de saída.

    Returns:
        dict: O JSON retornado e salvo.
    """
    if not AZURE_API_KEY or not AZURE_ENDPOINT or not AZURE_DEPLOYMENT:
        raise EnvironmentError("Faltam variáveis no .env: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME")

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }

    url = f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"

    data = {
        "messages": [
            {"role": "system", "content": prompt_base},
            {"role": "user", "content": dialogo_formatado}
        ],
        "temperature": 0.4,
        "max_tokens": 2000
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    raw_response = response.json()["choices"][0]["message"]["content"]

    # Tenta converter a resposta em JSON
    try:
        parsed_response = json.loads(raw_response)
    except json.JSONDecodeError:
        raise ValueError("A resposta da LLM não é um JSON válido")

    # Carrega ou inicia a lista de saída
    if os.path.exists(output_json_path):
        with open(output_json_path, "r", encoding="utf-8") as f:
            lista = json.load(f)
    else:
        lista = []

    lista.append(parsed_response)

    # Salva o arquivo atualizado
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)
    return parsed_response

def exec_extract(data):
    resposta = enviar_para_llm_azure(
        dialogo_formatado=data,
        prompt_base="""// Prompt Agente Extrator JSON Consistente - v12
    // Autor: Guilherme

    # VISÃO GERAL

    Você é um agente de inteligência artificial especializado na extração de dados estruturados a partir de transcrições de chamadas ou mensagens. Seu papel é analisar o conteúdo textual fornecido e retornar **exclusivamente um objeto JSON válido**, com informações organizadas conforme o formato definido abaixo.

    # FOCO DA ANÁLISE

    ⚠️ Toda a análise deve ser realizada **com base nas falas e interações da pessoa que não for vendedora**.  
    Não extraia insights com base nas falas dos vendedores, mesmo que eles revelem informações pessoais, façam sugestões ou forneçam contexto.  
    Considere o vendedor como **interlocutor secundário**. A prioridade analítica é sempre o **cliente, lead, parceiro ou outro participante que não pertença à equipe de vendas**.

    # OBJETIVO

    Dado um texto de conversa, identifique e preencha todos os campos do JSON abaixo, com base nas informações provenientes **exclusivamente do não-vendedor**.  
    Se determinado campo não for identificado, preencha com o valor vazio apropriado: string vazia `""`, lista vazia `[]`, ou objetos com campos internos vazios.

    # CLASSIFICAÇÃO DE VÍDEO DE VENDAS

    Considere uma reunião como **de vendas** (`"is_sales_meeting": true`) **somente se os dois critérios abaixo forem atendidos**:

    1. **Pelo menos um dos seguintes nomes aparecer como participante da conversa**:
        - `"Carolina Brandão"`
        - `"Douglas Machado"`
        - `"Josias Rocha"`
        - `"Kevin Juan"`
        - `"Morrâmulo Ítalo"`

    2. **O conteúdo da conversa estiver relacionado à tentativa de vender, apresentar, negociar ou fechar um produto, serviço, mentoria ou proposta comercial.**

    Se ambos os critérios forem atendidos:
    - Defina `"is_sales_meeting": true`
    - Atribua ao(s) participante(s) com nome(s) listado(s) o papel `"Vendedor"` no campo `participantes`

    Se **nenhum vendedor estiver presente**, ou **se a conversa não apresentar conteúdo claramente comercial ou de negociação**, defina:

    ```json
    "is_sales_meeting": false
    STATUS DA NEGOCIAÇÃO
    O campo status_negociacao.status deve conter uma das seguintes opções fixas:

    "fechado" – Quando ficou claro que o cliente fechou negócio.

    "perdido" – Quando houve rejeição ou cancelamento claro da proposta.

    "em andamento" – Quando o processo de venda ainda está em curso.

    "inconclusivo" – Quando não há dados suficientes para determinar o status.

    A observação deve justificar a classificação com base no que o não-vendedor expressou.

    FOCO DE ANÁLISE DE PERSONA
    O campo "persona_detalhada" deve conter uma lista de características, atitudes, experiências ou traços inferidos exclusivamente das falas do participante que não for o vendedor.

    Exemplo:

    json
    Copiar
    Editar
    "persona_detalhada": [
      "Já empreendeu desde os 18 anos",
      "Teve uma experiência emocionalmente difícil com falência",
      "Busca evitar repetir erros passados",
      "Utiliza esportes como forma de regular o emocional"
    ]
    ESTRUTURA JSON DE SAÍDA
    json
    Copiar
    Editar
    {
      "is_sales_meeting": true,
      "resumo_geral": "",
      "participantes": [
        { "nome": "", "papel": "" }
      ],
      "status_negociacao": {
        "status": "",
        "observacao": ""
      },
      "oportunidades_comerciais": [],
      "problemas_identificados": [],
      "objeções": [],
      "dores": [],
      "expectativas": [],
      "aspectos_emocionais_e_relacionais": {
        "desafios_pessoais": [],
        "clima_conversa": ""
      },
      "persona_detalhada": []
    }
    INSTRUÇÕES DE EXTRAÇÃO
    resumo_geral: Síntese do conteúdo da conversa do ponto de vista do não-vendedor.

    participantes: Lista com "nome" e "papel". Os nomes da lista de vendedores acima devem sempre receber o papel "Vendedor".

    status_negociacao: Classifique com base no discurso do não-vendedor.

    oportunidades_comerciais: Extraia apenas aquelas reconhecidas ou indicadas pelo não-vendedor.

    problemas_identificados: Obstáculos citados pelo não-vendedor.

    objeções: Barreiras levantadas por quem não é da equipe de vendas.

    dores: Necessidades e dificuldades relatadas pelo não-vendedor.

    expectativas: Resultados desejados mencionados por ele.

    aspectos_emocionais_e_relacionais: Clima da conversa segundo suas falas; desafios pessoais mencionados.

    persona_detalhada: Perfil, histórico e comportamentos inferidos exclusivamente do não-vendedor.

    FORMATO E REGRAS
    Todos os campos devem estar presentes.

    Campos sem informação devem conter valores vazios apropriados.

    A chave "is_sales_meeting" é obrigatória e deve ser booleana (true ou false).

    A resposta deve ser apenas o JSON válido, sem comentários, explicações, prefixos ou marcações Markdown como ```json.

    FORMATO DE RESPOSTA
    Retorne apenas o objeto JSON puro.
    Sem explicações, sem texto adicional. Somente o JSON final.""",
      output_json_path="resultados_analise.json"
    )

    print(resposta)
