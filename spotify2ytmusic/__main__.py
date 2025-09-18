#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from . import cli
import sys
import inspect


def listar_comandos(module) -> list[str]:
    """
    Retorna apenas funções definidas diretamente no módulo `cli`
    (ignora importadas/privadas).
    """
    return sorted(
        name
        for name, obj in inspect.getmembers(module)
        if inspect.isfunction(obj)
        and getattr(obj, "__module__", "") == module.__name__
        and not name.startswith("_")
    )


def imprimir_ajuda(comandos: list[str]) -> None:
    print("uso: spotify2ytmusic [COMANDO] <ARGUMENTOS>")
    print("Comandos disponíveis:", ", ".join(comandos))
    print("Exemplo: spotify2ytmusic listar_playlists")


def main() -> None:
    comandos = listar_comandos(cli)

    # Sem args ou com ajuda explícita
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        imprimir_ajuda(comandos)
        sys.exit(0 if len(sys.argv) >= 2 else 1)

    cmd = sys.argv[1]

    if cmd not in comandos:
        print(f"ERRO: Comando desconhecido '{cmd}'. Consulte:")
        print("       https://github.com/linsomniac/spotify_to_ytmusic")
        print("Comandos disponíveis:", ", ".join(comandos))
        sys.exit(1)

    # Executa o subcomando preservando os argumentos seguintes
    fn = getattr(cli, cmd)
    sys.argv = sys.argv[1:]
    try:
        fn()
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
        sys.exit(130)


if __name__ == "__main__":
    main()
