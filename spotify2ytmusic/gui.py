#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import threading
import json
import tkinter as tk
from tkinter import ttk

from . import cli
from . import backend
from . import spotify_backup
from typing import Callable


def create_label(parent: tk.Frame, text: str, **kwargs) -> tk.Label:
    """Cria um Label estilizado."""
    return tk.Label(
        parent,
        text=text,
        font=("Helvetica", 14),
        background="#161515",
        foreground="white",
        **kwargs,
    )


def create_button(parent: tk.Frame, text: str, **kwargs) -> tk.Button:
    """Cria um Button estilizado."""
    return tk.Button(
        parent,
        text=text,
        font=("Helvetica", 14),
        background="#383838",
        foreground="white",
        border=1,
        **kwargs,
    )


class Window:
    """Janela principal com abas e logs."""

    def __init__(self) -> None:
        """Inicializa a janela, abas e logs."""
        self.root = tk.Tk()
        self.root.title("Spotify → YT Music")
        self.root.geometry("1280x720")
        self.root.config(background="#161515")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook.Tab", background="#121212",
                        foreground="white")
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#161515")],
            foreground=[("selected", "#ffffff")],
        )
        style.configure("TFrame", background="#161515")
        style.configure("TNotebook", background="#121212")

        # Redireciona stdout para a GUI
        sys.stdout.write = self.redirector

        self.root.after(1, lambda: self.yt_login(auto=True))
        self.root.after(1, lambda: self.load_write_settings(0))

        # Divisor vertical: abas em cima, logs embaixo
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Container das abas
        self.tab_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.tab_frame, weight=2)

        self.tabControl = ttk.Notebook(self.tab_frame)
        self.tabControl.pack(fill=tk.BOTH, expand=1)

        # Abas
        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)
        self.tab3 = ttk.Frame(self.tabControl)
        self.tab4 = ttk.Frame(self.tabControl)
        self.tab5 = ttk.Frame(self.tabControl)
        self.tab6 = ttk.Frame(self.tabControl)
        self.tab7 = ttk.Frame(self.tabControl)

        self.tabControl.add(self.tab1, text="Login no YT Music")
        self.tabControl.add(self.tab2, text="Backup do Spotify")
        self.tabControl.add(self.tab3, text="Carregar músicas curtidas")
        self.tabControl.add(self.tab4, text="Listar playlists")
        self.tabControl.add(self.tab5, text="Copiar todas as playlists")
        self.tabControl.add(self.tab6, text="Copiar playlist específica")
        self.tabControl.add(self.tab7, text="Configurações")

        # Área de logs
        self.log_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.log_frame, weight=1)

        self.logs = tk.Text(self.log_frame, font=("Helvetica", 14))
        self.logs.pack(fill=tk.BOTH, expand=1)
        self.logs.config(background="#161515", foreground="white")

        # Tab 1 - Login
        create_label(
            self.tab1,
            text="Bem-vindo! Para começar, faça login no YT Music.",
        ).pack(anchor=tk.CENTER, expand=True)
        create_button(self.tab1, text="Login", command=self.yt_login).pack(
            anchor=tk.CENTER, expand=True
        )

        # Tab 2 - Backup
        create_label(
            self.tab2, text="Primeiro, faça o backup das suas playlists do Spotify."
        ).pack(anchor=tk.CENTER, expand=True)
        create_button(
            self.tab2,
            text="Backup",
            command=lambda: self.call_func(
                func=spotify_backup.main, args=(), next_tab=self.tab3
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # Tab 3 - Liked Songs
        create_label(self.tab3, text="Agora, carregue suas músicas curtidas.").pack(
            anchor=tk.CENTER, expand=True
        )
        create_button(
            self.tab3,
            text="Carregar",
            command=lambda: self.call_func(
                func=backend.copiar_faixas,
                args=(
                    backend.iterar_playlist_spotify(),
                    None,
                    False,
                    0.1,
                    self.var_algo.get(),
                ),
                next_tab=self.tab4,
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # Tab 4 - Listar playlists
        create_label(
            self.tab4, text="Liste suas playlists e seus IDs."
        ).pack(anchor=tk.CENTER, expand=True)
        create_button(
            self.tab4,
            text="Listar",
            command=lambda: self.call_func(
                func=cli.listar_playlists, args=(), next_tab=self.tab5
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # Tab 5 - Copiar tudo
        create_label(
            self.tab5,
            text="Copie todas as playlists do Spotify para o YT Music.\n"
                 "Observação: pode demorar (as faixas são adicionadas uma a uma).",
        ).pack(anchor=tk.CENTER, expand=True)
        create_button(
            self.tab5,
            text="Copiar tudo",
            command=lambda: self.call_func(
                func=backend.copiar_todas_playlists,
                args=(0.1, False, "utf-8", self.var_algo.get()),
                next_tab=self.tab6,
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # Tab 6 - Copiar específica
        create_label(
            self.tab6,
            text="Copie uma playlist específica do Spotify para o YT Music.",
        ).pack(anchor=tk.CENTER, expand=True)
        create_label(self.tab6, text="ID da playlist do Spotify:").pack(
            anchor=tk.CENTER, expand=True
        )
        self.spotify_playlist_id = tk.Entry(self.tab6)
        self.spotify_playlist_id.pack(anchor=tk.CENTER, expand=True)
        create_label(self.tab6, text="ID/Nome da playlist do YT Music:").pack(
            anchor=tk.CENTER, expand=True
        )
        self.yt_playlist_id = tk.Entry(self.tab6)
        self.yt_playlist_id.pack(anchor=tk.CENTER, expand=True)
        create_button(
            self.tab6,
            text="Copiar",
            command=lambda: self.call_func(
                func=backend.copiar_playlist,
                args=(
                    self.spotify_playlist_id.get(),
                    self.yt_playlist_id.get(),
                    "utf-8",
                    False,
                    0.1,
                    self.var_algo.get(),
                ),
                next_tab=self.tab6,
            ),
        ).pack(anchor=tk.CENTER, expand=True)

        # Tab 7 - Configurações
        self.var_scroll = tk.BooleanVar()

        auto_scroll = tk.Checkbutton(
            self.tab7,
            text="Rolagem automática",
            variable=self.var_scroll,
            command=lambda: self.load_write_settings(1),
            background="#161515",
            foreground="#ffffff",
            selectcolor="#565658",
            border=1,
        )
        auto_scroll.pack(anchor=tk.CENTER, expand=True)
        auto_scroll.select()

        self.var_algo = tk.IntVar()
        self.var_algo.set(0)

        self.algo_label = create_label(self.tab7, text=f"Algoritmo: ")
        self.algo_label.pack(anchor=tk.CENTER, expand=True)

        menu_algo = tk.OptionMenu(
            self.tab7,
            self.var_algo,
            0,
            *[1, 2],
            command=lambda x: self.load_write_settings(1),
        )
        menu_algo.pack(anchor=tk.CENTER, expand=True)
        menu_algo.config(background="#1D1C1C", foreground="#ffffff", border=1)

    def redirector(self, input_str="") -> None:
        """Insere `input_str` nos logs e mantém rolagem se habilitada."""
        self.logs.config(state=tk.NORMAL)
        self.logs.insert(tk.END, input_str)
        self.logs.config(state=tk.DISABLED)
        if self.var_scroll.get():
            self.logs.see(tk.END)

    def call_func(self, func: Callable, args: tuple, next_tab: ttk.Frame) -> None:
        """Chama `func` em outra thread e alterna para `next_tab` ao terminar."""
        th = threading.Thread(target=func, args=args)
        th.start()
        while th.is_alive():
            self.root.update()
        self.tabControl.select(next_tab)
        print()

    def yt_login(self, auto: bool = False) -> None:
        """
        Faz login no YT Music. Se `oauth.json` não existir, abre um console
        para executar 'ytmusicapi oauth'.
        """

        def run_in_thread():
            if os.path.exists("oauth.json"):
                print("Arquivo detectado, login automático")
            elif auto:
                print("Nenhum arquivo detectado. Login manual necessário.")
                return
            else:
                print("Arquivo não detectado, login necessário.")

                # Abre um novo console para rodar o comando
                if os.name == "nt":  # Windows
                    try:
                        process = subprocess.Popen(
                            ["ytmusicapi", "oauth"],
                            creationflags=subprocess.CREATE_NEW_CONSOLE,
                        )
                    except FileNotFoundError as e:
                        print(
                            "ERRO: Não foi possível executar 'ytmusicapi oauth'. "
                            "O pacote ytmusicapi está instalado? Tente 'pip install ytmusicapi'. "
                            f"Exceção: {e}"
                        )
                        sys.exit(1)
                    process.communicate()
                else:  # Unix/Linux/Mac
                    try:
                        subprocess.call(
                            "python3 -m ytmusicapi oauth",
                            shell=True,
                            stdout=subprocess.PIPE,
                        )
                    except Exception as e:
                        print(f"Ocorreu um erro: {e}")

            self.tabControl.select(self.tab2)
            print()

        th = threading.Thread(target=run_in_thread)
        th.start()

    def load_write_settings(self, action: int) -> None:
        """
        Lê (action=0) ou grava (action=1) as configurações em 'settings.json'.
        """
        texts = {0: "Correspondência exata",
                 1: "Aproximado (fuzzy)", 2: "Aproximado (com vídeo)"}

        exist = True
        if action == 0:
            with open("settings.json", "a+"):
                pass
            with open("settings.json", "r+") as f:
                value = f.read()
                if value == "":
                    exist = False
            if exist:
                with open("settings.json", "r+") as f:
                    settings = json.load(f)
                    self.var_scroll.set(settings["auto_scroll"])
                    self.var_algo.set(settings["algo_number"])
        else:
            with open("settings.json", "w+") as f:
                settings = {
                    "auto_scroll": self.var_scroll.get(),
                    "algo_number": self.var_algo.get(),
                }
                json.dump(settings, f)

        self.algo_label.config(text=f"Algoritmo: {texts[self.var_algo.get()]}")
        self.root.update()


def main() -> None:
    ui = Window()
    ui.root.mainloop()


if __name__ == "__main__":
    main()
