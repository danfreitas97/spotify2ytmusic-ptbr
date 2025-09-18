# Spotify para Youtube Music - Conversor de Playlists PT-BR

---

---

## Visão Geral

Este é um conjunto de scripts para copiar músicas "curtidas" e playlists do Spotify para o YouTube Music. Funciona tanto por **linha de comando** quanto com a **interface gráfica (GUI)**.

---

---

## Preparação / Pré-requisitos

Você precisará ter o **Python** e o **Git** instalados. Obviamente.

---

---

## Instruções de Instalação e Configuração

#

---

## 1\. Clonar o Repositório e Instalar Dependências

Crie e ative um ambiente virtual Python para isolar as dependências.

```bash
git clone https://github.com/danfreitas97/spotify2ytmusic-ptbr.git
cd spotify2ytmusic-ptbr

```

No Windows, os comandos para ativar o ambiente virtual são:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Linux ou Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

#

---

## 2\. Autenticação no YouTube Music

Para usar a API do YouTube Music, é necessário gerar credenciais válidas.

Você pode tentar o método automático primeiro:

```bash
python -m spotify2ytmusic oauth

```

Isso abrirá a linha de comando da API do YT Music para você fazer o login. Um arquivo `oauth.json` será criado na pasta do projeto.

**Se o método automático não funcionar, siga estes passos:**

1.  Abra o **YouTube Music** no Firefox e confirme que você está logado.
2.  Abra a ferramenta de inspeção do navegador (`F12` ou clique com o botão direito e selecione _Inspecionar_).
3.  Vá para a aba **Network (Rede)** e filtre por `/browse`.
4.  Clique em uma das requisições listadas e encontre a seção **Request Headers**.
5.  Ative a visualização RAW clicando no botão correspondente.
6.  Copie todos os cabeçalhos.
7.  Crie um arquivo chamado `raw_headers.txt` na pasta raiz do projeto e cole o conteúdo copiado nele.

Depois, execute o script de credenciais:

- No Windows: `python spotify2ytmusic/ytmusic_credentials.py`
- No Linux ou Mac: `python3 spotify2ytmusic/ytmusic_credentials.py`

Após rodar este script, um arquivo de autenticação será criado. A GUI irá detectá-lo automaticamente e fazer o login, pulando a aba "Login to YT Music" e exibindo a mensagem "File detected, auto login".

---

---

## Como Usar

#

---

## Interface Gráfica (GUI)

Para abrir a GUI, use o comando:
`python -m spotify2ytmusic gui`

Com a GUI você pode:

- Fazer backup das playlists do Spotify, salvando-as em um arquivo `playlists.json`.
- Importar músicas curtidas do Spotify para o YouTube Music.
- Listar playlists disponíveis.
- Copiar todas as playlists de uma vez.
- Copiar uma playlist específica.

#

---

## Linha de Comando

Use `python -m spotify2ytmusic` seguido do comando. Por exemplo, `python -m spotify2ytmusic listar_playlists`.

##

---

## Comandos Úteis

- **Fazer backup do Spotify:**
  `python spotify_backup.py playlists.json --dump=liked,playlists --format=json`

- **Importar músicas curtidas:**
  `python -m spotify2ytmusic carregar_curtidas`

- **Importar álbuns curtidos:**
  `python -m spotify2ytmusic carregar_albuns_curtidos`

- **Listar playlists:**
  `python -m spotify2ytmusic listar_playlists`

- **Copiar todas as playlists:**
  `python -m spotify2ytmusic copiar_todas_playlists`

- **Copiar uma playlist específica:**
  `python -m spotify2ytmusic copiar_playlist <SPOTIFY_PLAYLIST_ID> <YTMUSIC_PLAYLIST_ID>`

- **Criar uma playlist no YouTube Music:**
  `python -m spotify2ytmusic criar_playlist "<NOME_DA_PLAYLIST>"`

- **Copiar para uma nova playlist que será criada automaticamente:**
  Adicione um `+` antes do nome da playlist no YouTube Music.
  `python -m spotify2ytmusic copiar_playlist <SPOTIFY_PLAYLIST_ID> +<NOME_PLAYLIST_YTM>`

- **Buscar faixas para depuração:**
  `python -m spotify2ytmusic buscar --artist <ARTISTA> --album <ALBUM> <NOME_FAIXA>`

---

---

## Algoritmo de Correspondência

O programa tenta encontrar a faixa no YouTube Music de forma precisa.

1.  Primeiro, ele busca no álbum do artista.
2.  Se não encontrar, busca pelo nome da música junto com o artista.
3.  Dependendo da opção escolhida (`--algo` ou no menu da GUI), a busca pode ser:
    - **0**: Correspondência exata.
    - **1**: Correspondência aproximada.
    - **2**: Correspondência aproximada, permitindo vídeos.

Se a busca falhar, pode ser gerado um `ValueError`.

---

---

## Observações e Solução de Problemas

- Se a cópia falhar após 20-40 minutos, mantenha o YouTube Music aberto em segundo plano para evitar que a sessão expire.
- Se ocorrer um erro “HTTP 400: Bad Request”, tente rodar o comando com `--track-sleep=3` para reduzir a taxa de requisições e adicionar um atraso de 3 segundos entre as faixas.
- A ferramenta é compatível com Linux, Windows e macOS. Não funciona em celulares.
