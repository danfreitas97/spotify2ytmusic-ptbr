#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Licenciado sob MIT
#  Origem: https://github.com/caseychu/spotify-backup

import codecs
import http.client
import http.server
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser


class SpotifyAPI:
    """Cliente simples para a API do Spotify usando token OAuth."""

    BASE_URL = "https://api.spotify.com/v1/"

    def __init__(self, auth):
        self._auth = auth

    def get(self, url, params={}, tries=3):
        """Busca um recurso na API do Spotify."""
        url = self._construct_url(url, params)
        for _ in range(tries):
            try:
                req = self._create_request(url)
                return self._read_response(req)
            except Exception as err:
                print(f"Erro ao buscar URL {url}: {err}")
                time.sleep(2)
        sys.exit("Falha ao obter dados da API do Spotify após várias tentativas.")

    def list(self, url, params={}):
        """Paginação: agrega e retorna todos os itens."""
        response = self.get(url, params)
        items = response["items"]

        while response["next"]:
            response = self.get(response["next"])
            items += response["items"]
        return items

    @staticmethod
    def authorize(client_id, scope):
        """Abre o navegador para autorização e retorna a instância autenticada."""
        redirect_uri = f"http://127.0.0.1:{SpotifyAPI._SERVER_PORT}/redirect"
        url = SpotifyAPI._construct_auth_url(client_id, scope, redirect_uri)
        print(
            f"Abra este link se o navegador não abrir automaticamente: {url}")
        webbrowser.open(url)

        server = SpotifyAPI._AuthorizationServer(
            "127.0.0.1", SpotifyAPI._SERVER_PORT)
        try:
            while True:
                server.handle_request()
        except SpotifyAPI._Authorization as auth:
            return SpotifyAPI(auth.access_token)

    @staticmethod
    def _construct_auth_url(client_id, scope, redirect_uri):
        return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
            {
                "response_type": "token",
                "client_id": client_id,
                "scope": scope,
                "redirect_uri": redirect_uri,
            }
        )

    def _construct_url(self, url, params):
        """Monta a URL completa da API."""
        if not url.startswith(self.BASE_URL):
            url = self.BASE_URL + url
        if params:
            url += ("&" if "?" in url else "?") + \
                urllib.parse.urlencode(params)
        return url

    def _create_request(self, url):
        """Cria uma requisição autenticada."""
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self._auth}")
        return req

    def _read_response(self, req):
        """Lê e decodifica a resposta JSON."""
        with urllib.request.urlopen(req) as res:
            reader = codecs.getreader("utf-8")
            return json.load(reader(res))

    _SERVER_PORT = 43019

    class _AuthorizationServer(http.server.HTTPServer):
        def __init__(self, host, port):
            super().__init__((host, port), SpotifyAPI._AuthorizationHandler)

        def handle_error(self, request, client_address):
            raise

    class _AuthorizationHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/redirect"):
                self._redirect_to_token()
            elif self.path.startswith("/token?"):
                self._handle_token()
            else:
                self.send_error(404)

        def _redirect_to_token(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b'<script>location.replace("token?" + location.hash.slice(1));</script>'
            )

        def _handle_token(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<script>close()</script>Obrigado! Voce ja pode fechar esta janela."
            )
            access_token = re.search(
                "access_token=([^&]*)", self.path).group(1)
            raise SpotifyAPI._Authorization(access_token)

        def log_message(self, format, *args):
            pass

    class _Authorization(Exception):
        def __init__(self, access_token):
            self.access_token = access_token


def fetch_user_data(spotify, dump):
    """Busca playlists e músicas curtidas conforme o parâmetro `dump`."""
    playlists = []
    liked_albums = []

    if "liked" in dump:
        print("Carregando álbuns e músicas curtidas…")
        liked_tracks = spotify.list("me/tracks", {"limit": 50})
        liked_albums = spotify.list("me/albums", {"limit": 50})
        playlists.append({"name": "Liked Songs", "tracks": liked_tracks})

    if "playlists" in dump:
        print("Carregando playlists…")
        playlist_data = spotify.list("me/playlists", {"limit": 50})
        for playlist in playlist_data:
            print(f"Carregando playlist: {playlist['name']}")
            playlist["tracks"] = spotify.list(
                playlist["tracks"]["href"], {"limit": 100}
            )
        playlists.extend(playlist_data)

    return playlists, liked_albums


def write_to_file(file, format, playlists, liked_albums):
    """Grava os dados coletados no arquivo especificado."""
    print(f"Gravando em {file}…")
    with open(file, "w", encoding="utf-8") as f:
        if format == "json":
            json.dump({"playlists": playlists, "albums": liked_albums}, f)
        else:
            for playlist in playlists:
                f.write(playlist["name"] + "\r\n")
                for track in playlist["tracks"]:
                    if track["track"]:
                        f.write(
                            "{name}\t{artists}\t{album}\t{uri}\t{release_date}\r\n".format(
                                uri=track["track"]["uri"],
                                name=track["track"]["name"],
                                artists=", ".join(
                                    [
                                        artist["name"]
                                        for artist in track["track"]["artists"]
                                    ]
                                ),
                                album=track["track"]["album"]["name"],
                                release_date=track["track"]["album"]["release_date"],
                            )
                        )
                f.write("\r\n")


def main(dump="playlists,liked", format="json", file="playlists.json", token=""):
    print("Iniciando backup…")
    spotify = (
        SpotifyAPI(token)
        if token
        else SpotifyAPI.authorize(
            client_id="5c098bcc800e45d49e476265bc9b6934",
            scope="playlist-read-private playlist-read-collaborative user-library-read",
        )
    )

    playlists, liked_albums = fetch_user_data(spotify, dump)
    write_to_file(file, format, playlists, liked_albums)
    print(f"Backup concluído! Dados salvos em {file}")


if __name__ == "__main__":
    main()
