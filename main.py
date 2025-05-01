import asyncio
from typing import Optional
from contextlib import AsyncExitStack
import time
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from extract_data import exec_extract
from clean_brute_transcription import cleaning_data

from resolver import resolver_refs_com_azure_llm
from anthropic import Anthropic
from dotenv import load_dotenv
import sys
import csv
import pandas as pd



load_dotenv() # Carrega variáveis de ambiente do .env

class MCPClient:
    def __init__(self):
        # Inicializa objetos de sessão e cliente
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        # Certifique-se de que a chave de API do Anthropic esteja configurada
        #anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        #if not anthropic_api_key:
             #raise ValueError("ANTHROPIC_API_KEY não configurada nas variáveis de ambiente.")
        #self.anthropic = Anthropic(api_key=anthropic_api_key)

    # Métodos irão aqui
    async def connect_to_server(self):
        """
        Conecta a um servidor MCP.

        Args:
            server_script_path: Caminho para o script do servidor (.py ou .js).
        """
        server_params = StdioServerParameters(
            command="npx",
            args=["@browsermcp/mcp"],
            env=None # Variáveis de ambiente opcionais para o servidor
        )

        # Utiliza AsyncExitStack para gerenciar o ciclo de vida do transporte e da sessão
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        # Inicializa a sessão MCP
        await self.session.initialize()

        # Lista as ferramentas disponíveis do servidor conectado
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConectado ao servidor com ferramentas:", [tool.name for tool in tools])

    async def process_query(self, query: any) -> any:
        """
        Processa uma consulta utilizando o Claude e as ferramentas disponíveis.
        """
        
        tool_result = await self.session.call_tool(query["name"], query["args"])
        # Primeira chamada à API do Claude com a consulta e as ferramentas
        """
        claude_response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022", # Especifique o modelo
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        final_text = []
        assistant_message_content = []

        # Processa a resposta do Claude
        for content in claude_response.content:
            if content.type == 'text':
                final_text.append(content.text)
                assistant_message_content.append(content)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input

                # Executa a chamada da ferramenta através do cliente MCP
                print(f"\n[Chamando ferramenta {tool_name} com args {tool_args}]")
                # Chama a ferramenta e obtém o resultado
                tool_result = await self.session.call_tool(tool_name, tool_args)


                assistant_message_content.append(content)
                messages.append({
                    "role": "assistant",
                    "content": assistant_message_content
                })

                # Adiciona o resultado da ferramenta às mensagens para a próxima chamada ao modelo
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": tool_result.content # Conteúdo do resultado da ferramenta
                        }
                    ]
                })

                

                # Obtém a próxima resposta do Claude com base no resultado da ferramenta
                claude_response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022", # Especifique o modelo
                    max_tokens=1000,
                    messages=messages,
                    tools=available_tools # Passa as ferramentas novamente
                )

                # Adiciona o texto da nova resposta do Claude
                if claude_response.content and claude_response.content[0].type == 'text':
                     final_text.append(claude_response.content[0].text)
             """
        return tool_result

    async def executar_fluxo_transcricao(self, url: str):
        # Ação 1: Navegar para a URL
        print("\n>> Navegando para URL...")
        response = await self.process_query({
            "name": "browser_navigate",
            "args": {"url": url}
        })

        # Ação 2: Espera (se necessário após o carregamento da página)
        print("\n>> Aguardando carregamento da página...")
        await self.process_query({
            "name": "browser_wait",
            "args": {"time": 5}
        })

        # Ação 3: Captura snapshot da página
        print("\n>> Capturando snapshot da página...")
        response = await self.process_query({
            "name": "browser_snapshot",
            "args": {}
        })
        print(response.content)

        # Ação 4: Clicar na aba Transcript
        ref = resolver_refs_com_azure_llm(response.content, ["Transcript"])
        print("\n>> Clicando em 'Transcript'...")
        response = await self.process_query({
            "name": "browser_click",
            "args": {"element": "Transcript", "ref": ref["Transcript"]}
            
           # "args": {"element": "Transcript", "ref": "s2e467"}
        })     
        print(response.content)
        
        print("\n>> Capturando snapshot da página...")
        response = await self.process_query({
            "name": "browser_snapshot",
            "args": {}
        })

        # Ação 5: Clicar em 'Copy Transcript'
        ref = resolver_refs_com_azure_llm(response.content, ["Copy Transcript"])
        print("\n>> Clicando em 'Copy Transcript'...")
        response = await self.process_query({
            "name": "browser_click",
            "args": {"element": "Transcript", "ref": ref["Copy Transcript"]}
            
        })
        print(response.content)
        
        # Ação 6: Captura snapshot da página
        print("\n>> Capturando snapshot da página...")
        response = await self.process_query({
            "name": "browser_snapshot",
            "args": {}
        })
        text = ""
        for item in response.content:
            if hasattr(item, "text"):
                text += item.text.strip() + "\n"
        print("\n>> Limpando dados...")
        dialogo_formatado = cleaning_data(text, "conversas.csv")
        exec_extract(dialogo_formatado)
        
     
    async def loop_commands(self):
        """Executa um loop de chat interativo."""
        print("\nCliente MCP Iniciado!")
        print("Digite suas consultas ou 'quit' para sair.")

        print("Conectando ao browser, aguarde 5 segundos...")
        time.sleep(5)

        df_links = pd.read_csv("links.csv", header=None)

        for idx, row in df_links.iterrows():
            url = row[0]
            id_execucao = idx

            try:
                await self.executar_fluxo_transcricao(url)
                # Persistir o ID da última execução com sucesso
                with open("ultimo_id.txt", "w") as f:
                    f.write(str(id_execucao))

            except Exception as e:
                print(f"\nErro com URL {url}: {str(e)}")

    async def cleanup(self):
        """Limpa os recursos."""
        await self.exit_stack.aclose()

async def main():
    """
    if len(sys.argv) < 2:
        print("Uso: python seu_cliente.py <caminho_para_script_do_servidor>")
        sys.exit(1)    
    """
   

    client = MCPClient()
    await client.cleanup()
    try:
        # Conecta ao servidor especificado na linha de comando
        await client.connect_to_server()
        # Inicia o loop de chat
        await client.loop_commands()
    finally:
        # Garante a limpeza dos recursos ao final
        await client.cleanup()

if __name__ == "__main__":
    import asyncio
    # Executa a função principal
    asyncio.run(main())
    #main()