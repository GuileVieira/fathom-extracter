import pandas as pd
import re

def cleaning_data(conteudo_bruto: str, caminho_csv: str) -> str:
    """
    Processa um texto de transcrição em YAML e adiciona uma linha formatada ao CSV.
    
    Args:
        conteudo_bruto (str): O conteúdo da transcrição em formato de texto bruto.
        caminho_csv (str): Caminho do CSV onde a linha será adicionada.
    """
    pattern = r'- text: ([^\n]+)\s+- blockquote.*?- paragraph.*?: ([^\n]+)'
    matches = re.findall(pattern, conteudo_bruto, re.DOTALL)

    falas_formatadas = []
    for speaker, speech in matches:
        speaker_clean = speaker.strip()
        speech_clean = speech.strip().replace("\n", " ")
        falas_formatadas.append(f"{speaker_clean}: {speech_clean}")

    dialogo_formatado = " ".join(falas_formatadas)

    try:
        df = pd.read_csv(caminho_csv, sep=";")
    except FileNotFoundError:
        df = pd.DataFrame(columns=["dialogo"])

    df.loc[len(df)] = [dialogo_formatado]
    df.to_csv(caminho_csv, sep=";", index=False)

    print(f"Dialogo formatado adicionado ao CSV: {caminho_csv}")

    return dialogo_formatado
