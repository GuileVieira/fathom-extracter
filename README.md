# Projeto de Extração e Análise de Transcrições

Este projeto consiste em um conjunto de scripts Python para automatizar a extração, limpeza e análise de transcrições de conversas, especialmente aquelas originadas de reuniões online.

## Scripts

- `clean_brute_transcription.py`: Este script contém a função `cleaning_data` que recebe um texto bruto de transcrição (em formato YAML) e um caminho para um arquivo CSV. Ele extrai as falas dos participantes, formata-as e as adiciona como uma nova linha no arquivo CSV especificado.

- `extract_data.py`: Este script contém as funções `enviar_para_llm_azure` e `exec_extract`. A função `enviar_para_llm_azure` envia um diálogo formatado para a API Azure OpenAI, interpreta a resposta como JSON e salva o resultado em um arquivo JSON. A função `exec_extract` utiliza a função `enviar_para_llm_azure` para analisar o diálogo e extrair informações relevantes.

- `main.py`: Este é o script principal que orquestra todo o fluxo de trabalho. Ele utiliza a biblioteca `mcp` para interagir com a extensão BrowserMCP, automatizando a navegação em páginas web, a extração de transcrições e o processamento dos dados.

- `resolver.py`: Este script contém a função `resolver_refs_com_azure_llm` que consulta a API Azure OpenAI para resolver as referências (refs) de elementos em um snapshot da página web, com base em seus nomes visuais.

## Extensão BrowserMCP

Este projeto depende da extensão do Chrome chamada **BrowserMCP** para automatizar a interação com o navegador. Certifique-se de instalar a extensão a partir do seguinte link:

[BrowserMCP - Automate Your Browser](https://chromewebstore.google.com/detail/browser-mcp-automate-your/bjfgambnhccakkhmkepdoekmckoijdlc)

A extensão BrowserMCP permite que o script `main.py` navegue em páginas web, clique em elementos e extraia informações de forma automatizada.

## Variáveis de Ambiente

Os scripts `extract_data.py` e `resolver.py` dependem das seguintes variáveis de ambiente, que devem ser definidas em um arquivo `.env`:

- `AZURE_OPENAI_API_KEY`: A chave da API Azure OpenAI.
- `AZURE_OPENAI_ENDPOINT`: O endpoint da API Azure OpenAI.
- `AZURE_OPENAI_DEPLOYMENT_NAME`: O nome do deployment da API Azure OpenAI.
  `AZURE_OPENAI_API_VERSION`: A versão da API Azure OpenAI.

Um arquivo `.env.example` é fornecido como exemplo.

## Instalação

1.  Clone este repositório.
2.  Instale as dependências usando `pip install -r requirements.txt`.
3.  Instale a extensão BrowserMCP no Chrome a partir do link fornecido acima.
4.  Configure as variáveis de ambiente no arquivo `.env`.

## Execução

Para executar o script principal, utilize o seguinte comando:

```bash
python main.py
```

Certifique-se de que a extensão BrowserMCP esteja instalada e configurada corretamente antes de executar o script.
