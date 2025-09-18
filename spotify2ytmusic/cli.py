#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from argparse import ArgumentParser
import pprint

from . import backend


def listar_albuns_curtidos():
    """
    Lista álbuns que foram marcados como 'curtidos'.
    """
    for song in backend.iterar_albuns_curtidos_spotify():
        print(f"{song.album} - {song.artist} - {song.title}")


def listar_playlists():
    """
    Lista as playlists no Spotify e no YTMusic.
    """
    yt = backend.obter_ytmusic()
    spotify_pls = backend.carregar_playlists_json()

    # Spotify
    print("== Spotify")
    for src_pl in spotify_pls["playlists"]:
        print(
            f"{src_pl.get('id')} - {src_pl['name']:50} ({len(src_pl['tracks'])} faixas)"
        )

    print()
    print("== YTMusic")
    for pl in yt.get_library_playlists(limit=5000):
        print(
            f"{pl['playlistId']} - {pl['title']:40} ({pl.get('count', '?')} faixas)")


def criar_playlist():
    """
    Cria uma playlist no YTMusic.
    """
    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "--privacy",
            default="PRIVATE",
            help="Privacidade da playlist criada (PRIVATE, PUBLIC, UNLISTED; padrão: PRIVATE).",
        )
        parser.add_argument("playlist_name", type=str,
                            help="Nome da playlist a ser criada.")
        return parser.parse_args()

    args = parse_arguments()
    backend.criar_playlist(args.playlist_name, privacy_status=args.privacy)


def buscar():
    """Busca uma faixa no YTMusic."""
    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument("track_name", type=str,
                            help="Nome da faixa a ser buscada.")
        parser.add_argument("--artist", type=str, help="Artista a procurar.")
        parser.add_argument("--album", type=str, help="Nome do álbum.")
        parser.add_argument(
            "--algo", type=int, default=0,
            help="Algoritmo de busca (0 = exato, 1 = estendido, 2 = aproximado).",
        )
        return parser.parse_args()

    args = parse_arguments()

    yt = backend.obter_ytmusic()
    details = backend.DetalhesPesquisa()
    ret = backend.buscar_musica(
        yt, args.track_name, args.artist, args.album, args.algo, details=details
    )

    print(f"Consulta: '{details.query}'")
    print("Faixa selecionada:")
    pprint.pprint(ret)
    print()
    print(f"Sugestões de busca: '{details.suggestions}'")
    if details.songs:
        print("Top 5 músicas retornadas:")
        for song in details.songs[:5]:
            pprint.pprint(song)


def carregar_albuns_curtidos():
    """
    Carrega ÁLBUNS curtidos do Spotify para o YTMusic.
    (O Spotify guarda álbuns curtidos fora da playlist 'Liked Songs'.)
    """
    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument("--track-sleep", type=float, default=0.1,
                            help="Tempo de espera entre cada faixa adicionada (padrão: 0.1).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Não adicionar faixas (somente simular).")
        parser.add_argument("--spotify-playlists-encoding", default="utf-8",
                            help="Codificação do arquivo `playlists.json`.")
        parser.add_argument("--algo", type=int, default=0,
                            help="Algoritmo de busca (0 = exato, 1 = estendido, 2 = aproximado).")
        return parser.parse_args()

    args = parse_arguments()

    backend.copiar_faixas(
        backend.iterar_albuns_curtidos_spotify(
            spotify_encoding=args.spotify_playlists_encoding
        ),
        None,
        args.dry_run,
        args.track_sleep,
        args.algo,
    )


def carregar_curtidas():
    """
    Carrega a playlist 'Liked Songs' do Spotify para o YTMusic.
    """
    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument("--track-sleep", type=float, default=0.1,
                            help="Tempo de espera entre cada faixa adicionada (padrão: 0.1).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Não adicionar faixas (somente simular).")
        parser.add_argument("--spotify-playlists-encoding", default="utf-8",
                            help="Codificação do arquivo `playlists.json`.")
        parser.add_argument("--algo", type=int, default=0,
                            help="Algoritmo de busca (0 = exato, 1 = estendido, 2 = aproximado).")
        parser.add_argument("--reverse-playlist", action="store_true",
                            help="Inverter a playlist ao carregar. Normalmente NÃO é necessário "
                                 "nas 'Liked Songs' porque a ordem já é oposta aos outros comandos.")
        return parser.parse_args()

    args = parse_arguments()

    backend.copiar_faixas(
        backend.iterar_playlist_spotify(
            None,
            spotify_encoding=args.spotify_playlists_encoding,
            reverse_playlist=args.reverse_playlist,
        ),
        None,
        args.dry_run,
        args.track_sleep,
        args.algo,
    )


def copiar_playlist():
    """
    Copia uma playlist do Spotify para uma playlist do YTMusic.
    """
    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument("--track-sleep", type=float, default=0.1,
                            help="Tempo de espera entre cada faixa adicionada (padrão: 0.1).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Não adicionar faixas (somente simular).")
        parser.add_argument("spotify_playlist_id", type=str,
                            help="ID da playlist do Spotify (origem).")
        parser.add_argument("ytmusic_playlist_id", type=str,
                            help="ID da playlist do YTMusic (destino). Se começar com '+', é tratado "
                                 "como NOME; se não existir, será criada (sem o '+').")
        parser.add_argument("--spotify-playlists-encoding", default="utf-8",
                            help="Codificação do arquivo `playlists.json`.")
        parser.add_argument("--algo", type=int, default=0,
                            help="Algoritmo de busca (0 = exato, 1 = estendido, 2 = aproximado).")
        parser.add_argument("--no-reverse-playlist", action="store_true",
                            help="NÃO inverter ao carregar. Playlists normais são invertidas por padrão "
                                 "para manter a mesma ordem do Spotify.")
        parser.add_argument("--privacy", default="PRIVATE",
                            help="Privacidade (PRIVATE, PUBLIC, UNLISTED; padrão: PRIVATE).")
        return parser.parse_args()

    args = parse_arguments()
    backend.copiar_playlist(
        spotify_playlist_id=args.spotify_playlist_id,
        ytmusic_playlist_id=args.ytmusic_playlist_id,
        track_sleep=args.track_sleep,
        dry_run=args.dry_run,
        spotify_playlists_encoding=args.spotify_playlists_encoding,
        reverse_playlist=not args.no_reverse_playlist,
        privacy_status=args.privacy,
    )


def copiar_todas_playlists():
    """
    Copia TODAS as playlists do Spotify (exceto 'Liked Songs') para o YTMusic.
    """
    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument("--track-sleep", type=float, default=0.1,
                            help="Tempo de espera entre cada faixa adicionada (padrão: 0.1).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Não adicionar faixas (somente simular).")
        parser.add_argument("--spotify-playlists-encoding", default="utf-8",
                            help="Codificação do arquivo `playlists.json`.")
        parser.add_argument("--algo", type=int, default=0,
                            help="Algoritmo de busca (0 = exato, 1 = estendido, 2 = aproximado).")
        parser.add_argument("--no-reverse-playlist", action="store_true",
                            help="NÃO inverter ao carregar. Playlists normais são invertidas por padrão.")
        parser.add_argument("--privacy", default="PRIVATE",
                            help="Privacidade (PRIVATE, PUBLIC, UNLISTED; padrão: PRIVATE).")
        return parser.parse_args()

    args = parse_arguments()
    backend.copiar_todas_playlists(
        track_sleep=args.track_sleep,
        dry_run=args.dry_run,
        spotify_playlists_encoding=args.spotify_playlists_encoding,
        yt_search_algo=args.algo,
        reverse_playlist=not args.no_reverse_playlist,
        privacy_status=args.privacy,
    )


def gui():
    """Executa a interface gráfica (GUI)."""
    from . import gui
    gui.main()


def oauth():
    """Executa o login 'ytmusicapi oauth'."""
    from ytmusicapi.setup import main
    sys.argv = ["ytmusicapi", "oauth"]
    sys.exit(main())
