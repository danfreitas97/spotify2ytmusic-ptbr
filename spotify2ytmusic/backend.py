#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
import time
import re

from ytmusicapi import YTMusic
from typing import Optional, Union, Iterator, Dict, List
from collections import namedtuple
from dataclasses import dataclass, field


SongInfo = namedtuple("SongInfo", ["title", "artist", "album"])


def obter_ytmusic() -> YTMusic:
    """
    Obtém uma instância autenticada do YTMusic usando 'oauth.json'.
    """
    if not os.path.exists("oauth.json"):
        print("ERRO: O arquivo 'oauth.json' não existe no diretório atual.")
        print("      Você já fez login no YTMusic? Rode 'ytmusicapi oauth'.")
        sys.exit(1)

    try:
        return YTMusic("oauth.json")
    except json.decoder.JSONDecodeError as e:
        print(f"ERRO: Problema ao decodificar JSON ao iniciar YTMusic: {e}")
        print("      Geralmente indica problema no 'oauth.json'.")
        print("      Faça login novamente: 'ytmusicapi oauth'.")
        sys.exit(1)


def _ytmusic_criar_playlist(
    yt: YTMusic, title: str, description: str, privacy_status: str = "PRIVATE"
) -> str:
    """Wrapper de criação de playlist com retentativa exponencial."""
    def _create(
        yt: YTMusic, title: str, description: str, privacy_status: str
    ) -> Union[str, dict]:
        exception_sleep = 5
        for _ in range(10):
            try:
                pid = yt.create_playlist(
                    title=title, description=description, privacy_status=privacy_status
                )
                return pid
            except Exception as e:
                print(
                    f"ERRO: (Tentando novamente create_playlist: {title}) {e} em {exception_sleep} s"
                )
                time.sleep(exception_sleep)
                exception_sleep *= 2
        return {"s2yt error": f'ERRO: Não foi possível criar a playlist "{title}"'}

    pid = _create(yt, title, description, privacy_status)
    if isinstance(pid, dict):
        print(f"ERRO: Falha ao criar playlist (nome: {title}): {pid}")
        sys.exit(1)

    time.sleep(1)  # evita erro de "missing playlist ID"
    return pid


def carregar_playlists_json(filename: str = "playlists.json", encoding: str = "utf-8"):
    """Lê o arquivo `playlists.json` exportado do Spotify."""
    return json.load(open(filename, "r", encoding=encoding))


def criar_playlist(pl_name: str, privacy_status: str = "PRIVATE") -> None:
    """Cria uma playlist no YTMusic."""
    yt = obter_ytmusic()
    pid = _ytmusic_criar_playlist(
        yt, title=pl_name, description=pl_name, privacy_status=privacy_status
    )
    print(f"ID da playlist: {pid}")


def iterar_albuns_curtidos_spotify(
    spotify_playlist_file: str = "playlists.json",
    spotify_encoding: str = "utf-8",
) -> Iterator[SongInfo]:
    """Itera faixas de álbuns curtidos no Spotify."""
    spotify_pls = carregar_playlists_json(
        spotify_playlist_file, spotify_encoding)
    if "albums" not in spotify_pls:
        return None
    for album in [x["album"] for x in spotify_pls["albums"]]:
        for track in album["tracks"]["items"]:
            yield SongInfo(track["name"], track["artists"][0]["name"], album["name"])


def iterar_playlist_spotify(
    src_pl_id: Optional[str] = None,
    spotify_playlist_file: str = "playlists.json",
    spotify_encoding: str = "utf-8",
    reverse_playlist: bool = True,
) -> Iterator[SongInfo]:
    """Itera faixas de uma playlist específica (ou 'Liked Songs' se None)."""
    spotify_pls = carregar_playlists_json(
        spotify_playlist_file, spotify_encoding)

    def _buscar_playlist(spotify_pls: Dict, src_pl_id: Union[str, None]) -> Dict:
        for src_pl in spotify_pls["playlists"]:
            if src_pl_id is None and str(src_pl.get("name")) == "Liked Songs":
                return src_pl
            if src_pl_id is not None and str(src_pl.get("id")) == src_pl_id:
                return src_pl
        raise ValueError(
            f"Não foi possível encontrar a playlist do Spotify {src_pl_id}")

    src_pl = _buscar_playlist(spotify_pls, src_pl_id)
    src_pl_name = src_pl["name"]

    print(f"== Playlist Spotify: {src_pl_name}")

    pl_tracks = src_pl["tracks"]
    if reverse_playlist:
        pl_tracks = reversed(pl_tracks)

    for src_track in pl_tracks:
        if src_track["track"] is None:
            print("AVISO: Faixa do Spotify malformada. Pulando.")
            continue
        try:
            src_album_name = src_track["track"]["album"]["name"]
            src_track_artist = src_track["track"]["artists"][0]["name"]
        except TypeError as e:
            print(f"ERRO: Faixa do Spotify malformada. Track: {src_track!r}")
            raise e
        src_track_name = src_track["track"]["name"]
        yield SongInfo(src_track_name, src_track_artist, src_album_name)


def obter_id_playlist_por_nome(yt: YTMusic, title: str) -> Optional[str]:
    """Obtém o ID de uma playlist no YTMusic pelo nome."""
    try:
        playlists = yt.get_library_playlists(limit=5000)
    except KeyError as e:
        print("=" * 60)
        print(
            f"Tentativa de localizar playlist '{title}' falhou com KeyError: {e}")
        print("Bug do ytmusicapi. Atualize: `pip install --upgrade ytmusicapi`")
        print("=" * 60)
        raise

    for pl in playlists:
        if pl["title"] == title:
            return pl["playlistId"]
    return None


@dataclass
class DetalhesPesquisa:
    query: Optional[str] = field(default=None)
    songs: Optional[List[Dict]] = field(default=None)
    suggestions: Optional[List[str]] = field(default=None)


def buscar_musica(
    yt: YTMusic,
    track_name: str,
    artist_name: str,
    album_name,
    yt_search_algo: int,
    details: Optional[DetalhesPesquisa] = None,
) -> dict:
    """Localiza uma música no YTMusic (algoritmos 0/1/2)."""
    albums = yt.search(query=f"{album_name} by {artist_name}", filter="albums")
    for album in albums[:3]:
        try:
            for track in yt.get_album(album["browseId"])["tracks"]:
                if track["title"] == track_name:
                    return track
        except Exception as e:
            print(f"Não foi possível consultar o álbum ({e}), continuando…")

    query = f"{track_name} by {artist_name}"
    if details:
        details.query = query
        details.suggestions = yt.get_search_suggestions(query=query)
    songs = yt.search(query=query, filter="songs")

    match yt_search_algo:
        case 0:
            if details:
                details.songs = songs
            return songs[0]
        case 1:
            for song in songs:
                if (
                    song["title"] == track_name
                    and song["artists"][0]["name"] == artist_name
                    and song["album"]["name"] == album_name
                ):
                    return song
            raise ValueError(
                f"Não encontrei {track_name} de {artist_name} em {album_name}")
        case 2:
            for song in songs:
                title_wo_brackets = re.sub(r"[\[(].*?[])]", "", song["title"])
                if (
                    (
                        title_wo_brackets == track_name
                        and song["album"]["name"] == album_name
                    )
                    or (title_wo_brackets == track_name)
                    or (title_wo_brackets in track_name)
                    or (track_name in title_wo_brackets)
                ) and (
                    song["artists"][0]["name"] == artist_name
                    or artist_name in song["artists"][0]["name"]
                ):
                    return song
            else:
                track_name_l = track_name.lower()
                first_song_title = songs[0]["title"].lower()
                if (
                    track_name_l not in first_song_title
                    or songs[0]["artists"][0]["name"] != artist_name
                ):
                    print("Não encontrei em 'songs', pesquisando em 'videos'…")
                    new_songs = yt.search(
                        query=f"{track_name} by {artist_name}", filter="videos"
                    )
                    for new_song in new_songs:
                        new_song_title = new_song["title"].lower()
                        if (
                            track_name_l in new_song_title
                            and artist_name in new_song_title
                        ) or (track_name_l in new_song_title):
                            print("Vídeo correspondente encontrado.")
                            return new_song
                    else:
                        raise ValueError(
                            f"Não encontrei {track_name} de {artist_name} em {album_name}"
                        )
                else:
                    return songs[0]


def copiar_faixas(
    src_tracks: Iterator[SongInfo],
    dst_pl_id: Optional[str] = None,
    dry_run: bool = False,
    track_sleep: float = 0.1,
    yt_search_algo: int = 0,
    *,
    yt: Optional[YTMusic] = None,
):
    """Copia faixas (curtir ou adicionar à playlist destino)."""
    if yt is None:
        yt = obter_ytmusic()

    if dst_pl_id is not None:
        try:
            yt_pl = yt.get_playlist(playlistId=dst_pl_id)
        except Exception as e:
            print(
                f"ERRO: Não foi possível encontrar a playlist do YTMusic {dst_pl_id}: {e}")
            print("      Verifique o ID (ex.: 'PL_xxxxxxxxxxxxxxxxx').")
            sys.exit(1)
        print(f"== Playlist Youtube: {yt_pl['title']}")

    tracks_added_set = set()
    duplicate_count = 0
    error_count = 0

    for src_track in src_tracks:
        print(
            f"Spotify:   {src_track.title} - {src_track.artist} - {src_track.album}")

        try:
            dst_track = buscar_musica(
                yt, src_track.title, src_track.artist, src_track.album, yt_search_algo
            )
        except Exception as e:
            print(f"ERRO: Não foi possível localizar a faixa no YTMusic: {e}")
            error_count += 1
            continue

        yt_artist_name = "<Desconhecido>"
        if "artists" in dst_track and len(dst_track["artists"]) > 0:
            yt_artist_name = dst_track["artists"][0]["name"]
        print(
            f"  Youtube: {dst_track['title']} - {yt_artist_name} - {dst_track['album'] if 'album' in dst_track else '<Desconhecido>'}"
        )

        if dst_track["videoId"] in tracks_added_set:
            print("(DUPLICADO: esta faixa já foi adicionada)")
            duplicate_count += 1
        tracks_added_set.add(dst_track["videoId"])

        if not dry_run:
            exception_sleep = 5
            for _ in range(10):
                try:
                    if dst_pl_id is not None:
                        yt.add_playlist_items(
                            playlistId=dst_pl_id,
                            videoIds=[dst_track["videoId"]],
                            duplicates=False,
                        )
                    else:
                        yt.rate_song(dst_track["videoId"], "LIKE")
                    break
                except Exception as e:
                    print(
                        f"ERRO: (Tentando novamente add_playlist_items: {dst_pl_id} {dst_track['videoId']}) {e} em {exception_sleep} s"
                    )
                    time.sleep(exception_sleep)
                    exception_sleep *= 2

        if track_sleep:
            time.sleep(track_sleep)

    print()
    print(
        f"Adicionadas {len(tracks_added_set)} faixas, {duplicate_count} duplicadas, {error_count} erros."
    )


def copiar_playlist(
    spotify_playlist_id: str,
    ytmusic_playlist_id: str,
    spotify_playlists_encoding: str = "utf-8",
    dry_run: bool = False,
    track_sleep: float = 0.1,
    yt_search_algo: int = 0,
    reverse_playlist: bool = True,
    privacy_status: str = "PRIVATE",
):
    """Copia uma playlist do Spotify para uma do YTMusic."""
    print("Usando algoritmo de busca nº:", yt_search_algo)
    yt = obter_ytmusic()
    pl_name: str = ""

    if ytmusic_playlist_id.startswith("+"):
        pl_name = ytmusic_playlist_id[1:]
        ytmusic_playlist_id = obter_id_playlist_por_nome(yt, pl_name)
        print(f"Buscando playlist '{pl_name}': id={ytmusic_playlist_id}")

    if ytmusic_playlist_id is None:
        if pl_name == "":
            print(
                "Nenhum nome/ID da playlist de destino informado; criando nome a partir do Spotify…")
            spotify_pls: dict = carregar_playlists_json()
            for pl in spotify_pls["playlists"]:
                if len(pl.keys()) > 3 and pl["id"] == spotify_playlist_id:
                    pl_name = pl["name"]

        ytmusic_playlist_id = _ytmusic_criar_playlist(
            yt, title=pl_name, description=pl_name, privacy_status=privacy_status
        )
        if isinstance(ytmusic_playlist_id, dict):
            print(f"ERRO: Falha ao criar playlist: {ytmusic_playlist_id}")
            sys.exit(1)
        print(
            f"NOTA: Playlist criada '{pl_name}' com ID: {ytmusic_playlist_id}")

    copiar_faixas(
        iterar_playlist_spotify(
            spotify_playlist_id,
            spotify_encoding=spotify_playlists_encoding,
            reverse_playlist=reverse_playlist,
        ),
        ytmusic_playlist_id,
        dry_run,
        track_sleep,
        yt_search_algo,
        yt=yt,
    )


def copiar_todas_playlists(
    track_sleep: float = 0.1,
    dry_run: bool = False,
    spotify_playlists_encoding: str = "utf-8",
    yt_search_algo: int = 0,
    reverse_playlist: bool = True,
    privacy_status: str = "PRIVATE",
):
    """Copia todas as playlists do Spotify (exceto 'Músicas Curtidas') para o YTMusic."""
    spotify_pls = carregar_playlists_json()
    yt = obter_ytmusic()

    for src_pl in spotify_pls["playlists"]:
        if str(src_pl.get("name")) == "Liked Songs":
            continue

        pl_name = src_pl["name"] or f"Spotify Playlist sem nome {src_pl['id']}"

        dst_pl_id = obter_id_playlist_por_nome(yt, pl_name)
        print(f"Buscando playlist '{pl_name}': id={dst_pl_id}")
        if dst_pl_id is None:
            dst_pl_id = _ytmusic_criar_playlist(
                yt, title=pl_name, description=pl_name, privacy_status=privacy_status
            )
            if isinstance(dst_pl_id, dict):
                print(f"ERRO: Falha ao criar playlist: {dst_pl_id}")
                sys.exit(1)
            print(f"NOTA: Playlist criada '{pl_name}' com ID: {dst_pl_id}")

        copiar_faixas(
            iterar_playlist_spotify(
                src_pl["id"],
                spotify_encoding=spotify_playlists_encoding,
                reverse_playlist=reverse_playlist,
            ),
            dst_pl_id,
            dry_run,
            track_sleep,
            yt_search_algo,
        )
        print("\nPlaylist concluída!\n")

    print("Tudo pronto!")
