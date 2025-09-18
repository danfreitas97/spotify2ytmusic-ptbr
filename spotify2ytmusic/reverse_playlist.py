#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
from argparse import ArgumentParser


def reverse_playlist(input_file="playlists.json", verbose=True, replace=False) -> int:
    if os.path.exists(input_file) and not replace:
        if verbose:
            print("Arquivo de saída já existe e --replace não foi usado. Saindo…")
        return 1

    print("Fazendo backup do arquivo…")
    shutil.copyfile(input_file, input_file.split(".")[0] + "_backup.json")

    if verbose:
        print("Carregando JSON…")
    with open(input_file, "r") as file:
        data = json.load(file)

    data2 = data.copy()

    if verbose:
        print("Invertendo as playlists…")
    for i in range(len(data2["playlists"])):
        data2["playlists"][i]["tracks"] = data2["playlists"][i]["tracks"][::-1]

    if verbose:
        print("Gravando no arquivo (pode demorar)…")
    with open(input_file, "w") as file:
        json.dump(data2, file)

    if verbose:
        print("Concluído!")
        print(f"Arquivo gravado em {input_file}")

    return 0


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("input_file", type=str,
                        help="Caminho do arquivo de entrada.")
    parser.add_argument(
        "-v", "--verbose", action="store_false", help="Desabilitar modo verboso."
    )
    parser.add_argument(
        "-r",
        "--replace",
        action="store_true",
        help="Sobrescrever o arquivo de saída se já existir.",
    )

    args = parser.parse_args()

    reverse_playlist(args.input_file, args.verbose, args.replace)
