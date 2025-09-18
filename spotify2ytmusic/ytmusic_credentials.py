# -*- coding: utf-8 -*-

import ytmusicapi
import os


def setup_ytmusic_with_raw_headers(
    input_file="raw_headers.txt", credentials_file="oauth.json"
):
    """
    Lê cabeçalhos brutos (raw) do arquivo e configura o YTMusic via ytmusicapi.setup.

    Parâmetros:
        input_file (str): Caminho do arquivo com os cabeçalhos.
        credentials_file (str): Caminho do arquivo de credenciais a salvar.

    Retorna:
        str: String de cabeçalhos de configuração retornada por ytmusicapi.setup.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Arquivo de entrada {input_file} não existe.")

    with open(input_file, "r") as file:
        headers_raw = file.read()

    config_headers = ytmusicapi.setup(
        filepath=credentials_file, headers_raw=headers_raw
    )
    print(f"Credenciais salvas em {credentials_file}")
    return config_headers


if __name__ == "__main__":
    try:
        raw_headers_file = "raw_headers.txt"
        credentials_file = "oauth.json"

        print(f"Configurando YTMusic usando cabeçalhos de {raw_headers_file}…")
        setup_ytmusic_with_raw_headers(
            input_file=raw_headers_file, credentials_file=credentials_file
        )

        print("Configuração do YTMusic concluída com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
