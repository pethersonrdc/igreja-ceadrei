"""
Galeria de cultos — armazenamento local (SQLite + arquivos).
As fotos só são apagadas manualmente pelo usuário no painel.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from markupsafe import Markup, escape

import persistencia

_AVISO_HORA_RE = re.compile(
    r"(?<![\d])(\d{1,2}\s*[:hH]\s*\d{2})(?!\d)",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = persistencia.data_root()
UPLOAD_DIR = persistencia.upload_dir("galeria")
SEED_DIR = BASE_DIR / "static" / "images" / "galeria"
DB_PATH = persistencia.db_path("galeria.db")
AVISO_HOME_PATH = persistencia.db_path("aviso_home_midia.json")
SEED_FLAG_PATH = persistencia.db_path("galeria_seed_ok.json")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov"}
HOME_MEDIA_EXTENSIONS = ALLOWED_EXTENSIONS | VIDEO_EXTENSIONS
HOME_UPLOAD_DIR = persistencia.upload_dir("home")
POST_HOME_PATH = persistencia.db_path("post_home_midia.json")

# Versões extras para srcset (original permanece no banco / disco).
VARIANT_WIDTHS = (480, 960, 1600)


def _seed_flag_path() -> Path:
    return persistencia.db_path("galeria_seed_ok.json")


def galeria_ja_gerenciada() -> bool:
    """True se a mídia já publicou/apagou — não recriar seed automático."""
    return _seed_flag_path().exists()


def marcar_galeria_gerenciada(*, motivo: str = "") -> None:
    path = _seed_flag_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "motivo": (motivo or "").strip(),
        "em": agora().isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def disco_persistente_ativo() -> bool:
    return persistencia.usando_disco_persistente()


def formatar_aviso_html(texto: str) -> Markup:
    """Destaca horários (ex.: 21:00, 19h30) no aviso da home."""
    limpo = (texto or "").strip()
    if not limpo:
        return Markup("")
    escapado = str(escape(limpo))

    def _wrap(match: re.Match[str]) -> str:
        return f'<span class="aviso-hora">{match.group(1)}</span>'

    return Markup(_AVISO_HORA_RE.sub(_wrap, escapado))


def obter_aviso_home() -> dict:
    """Aviso de texto da mídia para a página inicial."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Preferência: disco persistente; fallback do aviso versionado no repo
    caminhos = [AVISO_HOME_PATH, BASE_DIR / "data" / "aviso_home_midia.json"]
    for path in caminhos:
        if not path.exists():
            continue
        try:
            dados = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        texto = (dados.get("texto") or "").strip()
        ativo = bool(dados.get("ativo")) and bool(texto)
        return {
            "texto": texto,
            "ativo": ativo,
            "texto_html": formatar_aviso_html(texto),
        }
    return {"texto": "", "ativo": False, "texto_html": Markup("")}


def salvar_aviso_home(texto: str, ativo: bool = True) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    limpo = (texto or "").strip()
    payload = {
        "texto": limpo,
        "ativo": bool(ativo) and bool(limpo),
        "atualizado_em": agora().isoformat(timespec="seconds"),
    }
    AVISO_HOME_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"texto": payload["texto"], "ativo": payload["ativo"]}


def _post_home_vazio() -> dict:
    return {
        "titulo": "",
        "texto": "",
        "link": "",
        "arquivo": "",
        "ativo": False,
        "atualizado_em": "",
        "tem_arquivo": False,
        "arquivo_eh_video": False,
        "tem_conteudo": False,
    }


def _enriquecer_post_home(dados: dict) -> dict:
    item = _post_home_vazio()
    item["titulo"] = (dados.get("titulo") or "").strip()
    item["texto"] = (dados.get("texto") or "").strip()
    item["link"] = (dados.get("link") or "").strip()
    item["arquivo"] = (dados.get("arquivo") or "").strip()
    item["ativo"] = bool(dados.get("ativo"))
    item["atualizado_em"] = (dados.get("atualizado_em") or "").strip()
    item["tem_arquivo"] = bool(item["arquivo"])
    item["arquivo_eh_video"] = Path(item["arquivo"]).suffix.lower() in VIDEO_EXTENSIONS
    item["tem_conteudo"] = bool(
        item["titulo"] or item["texto"] or item["arquivo"] or item["link"]
    )
    if item["ativo"] and not item["tem_conteudo"]:
        item["ativo"] = False
    return item


def obter_post_home() -> dict:
    """Post rico (título/texto/mídia) da mídia para a página inicial."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HOME_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    caminhos = [POST_HOME_PATH, BASE_DIR / "data" / "post_home_midia.json"]
    for path in caminhos:
        if not path.exists():
            continue
        try:
            dados = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        if isinstance(dados, dict):
            return _enriquecer_post_home(dados)
    return _post_home_vazio()


def obter_post_home_publico() -> dict | None:
    item = obter_post_home()
    if item.get("ativo") and item.get("tem_conteudo"):
        return item
    return None


def salvar_post_home(
    *,
    titulo: str,
    texto: str,
    link: str = "",
    arquivo: str | None = None,
    ativo: bool = True,
) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HOME_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    atual = obter_post_home()
    if arquivo is None:
        arquivo_final = atual.get("arquivo") or ""
    else:
        arquivo_final = arquivo.strip()
    payload = {
        "titulo": (titulo or "").strip(),
        "texto": (texto or "").strip(),
        "link": (link or "").strip(),
        "arquivo": arquivo_final,
        "ativo": bool(ativo),
        "atualizado_em": agora().isoformat(timespec="seconds"),
    }
    enriquecido = _enriquecer_post_home(payload)
    POST_HOME_PATH.write_text(
        json.dumps(
            {
                "titulo": enriquecido["titulo"],
                "texto": enriquecido["texto"],
                "link": enriquecido["link"],
                "arquivo": enriquecido["arquivo"],
                "ativo": enriquecido["ativo"],
                "atualizado_em": enriquecido["atualizado_em"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return enriquecido


def apagar_arquivo_post_home() -> bool:
    atual = obter_post_home()
    nome = (atual.get("arquivo") or "").strip()
    if not nome:
        return False
    caminho = HOME_UPLOAD_DIR / nome
    if caminho.exists():
        caminho.unlink()
    salvar_post_home(
        titulo=atual.get("titulo") or "",
        texto=atual.get("texto") or "",
        link=atual.get("link") or "",
        arquivo="",
        ativo=bool(atual.get("ativo")),
    )
    return True


def limpar_post_home() -> None:
    atual = obter_post_home()
    nome = (atual.get("arquivo") or "").strip()
    if nome:
        caminho = HOME_UPLOAD_DIR / nome
        if caminho.exists():
            caminho.unlink()
    POST_HOME_PATH.write_text(
        json.dumps(
            {
                "titulo": "",
                "texto": "",
                "link": "",
                "arquivo": "",
                "ativo": False,
                "atualizado_em": agora().isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def extensao_home_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in HOME_MEDIA_EXTENSIONS


def arquivo_home_eh_video(nome: str) -> bool:
    return Path(nome or "").suffix.lower() in VIDEO_EXTENSIONS


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    global UPLOAD_DIR, DATA_DIR, DB_PATH, AVISO_HOME_PATH, HOME_UPLOAD_DIR, POST_HOME_PATH
    DATA_DIR = persistencia.data_root()
    DB_PATH = persistencia.db_path("galeria.db")
    AVISO_HOME_PATH = persistencia.db_path("aviso_home_midia.json")
    POST_HOME_PATH = persistencia.db_path("post_home_midia.json")
    UPLOAD_DIR = persistencia.upload_dir("galeria")
    HOME_UPLOAD_DIR = persistencia.upload_dir("home")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    HOME_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                culto_titulo TEXT NOT NULL,
                culto_dia TEXT NOT NULL,
                titulo TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                expira_em TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS fotos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                arquivo TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            );
            """
        )
        # Bancos antigos podem ter expira_em NOT NULL sem default; garante coluna usável
        cols = {
            row["name"]: row
            for row in conn.execute("PRAGMA table_info(posts)").fetchall()
        }
        if "expira_em" not in cols:
            conn.execute(
                "ALTER TABLE posts ADD COLUMN expira_em TEXT NOT NULL DEFAULT ''"
            )
        conn.execute(
            "UPDATE posts SET expira_em = '' WHERE expira_em IS NULL"
        )


def agora() -> datetime:
    return datetime.now()


def listar_posts_ativos() -> list[dict]:
    """Lista todas as postagens (permanentes até o usuário apagar)."""
    init_db()
    with _connect() as conn:
        posts = conn.execute(
            """
            SELECT * FROM posts
            ORDER BY criado_em DESC
            """
        ).fetchall()

        resultado = []
        for post in posts:
            fotos = conn.execute(
                "SELECT id, arquivo FROM fotos WHERE post_id = ? ORDER BY id",
                (post["id"],),
            ).fetchall()
            item = dict(post)
            item["fotos"] = [dict(f) for f in fotos]
            resultado.append(item)
        return resultado


def obter_post(post_id: int) -> dict | None:
    init_db()
    with _connect() as conn:
        post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if not post:
            return None
        fotos = conn.execute(
            "SELECT id, arquivo FROM fotos WHERE post_id = ? ORDER BY id",
            (post_id,),
        ).fetchall()
        item = dict(post)
        item["fotos"] = [dict(f) for f in fotos]
        return item


def criar_post(culto_titulo: str, culto_dia: str, titulo: str, arquivos: list[str]) -> int:
    init_db()
    criado = agora()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO posts (culto_titulo, culto_dia, titulo, criado_em, expira_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                culto_titulo.strip(),
                culto_dia.strip(),
                titulo.strip(),
                criado.isoformat(timespec="seconds"),
                "",  # posts não expiram; campo legado no SQLite local
            ),
        )
        post_id = cur.lastrowid
        for arquivo in arquivos:
            conn.execute(
                "INSERT INTO fotos (post_id, arquivo) VALUES (?, ?)",
                (post_id, arquivo),
            )
    marcar_galeria_gerenciada(motivo=f"criou_post_{post_id}")
    return post_id


def apagar_post(post_id: int) -> bool:
    post = obter_post(post_id)
    if not post:
        return False
    for foto in post["fotos"]:
        apagar_arquivo_e_variantes(foto["arquivo"])
    with _connect() as conn:
        conn.execute("DELETE FROM fotos WHERE post_id = ?", (post_id,))
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    # Impede o seed automático de recolocar as fotos no próximo restart
    marcar_galeria_gerenciada(motivo=f"apagou_post_{post_id}")
    return True


def extensao_ok(nome: str) -> bool:
    return Path(nome).suffix.lower() in ALLOWED_EXTENSIONS


def nome_variante(arquivo: str, largura: int) -> str:
    """Nome do arquivo redimensionado ao lado do original (ex.: abc_960.jpg)."""
    path = Path(arquivo)
    return f"{path.stem}_{int(largura)}.jpg"


def listar_variantes(arquivo: str) -> list[str]:
    return [nome_variante(arquivo, w) for w in VARIANT_WIDTHS]


def apagar_arquivo_e_variantes(arquivo: str) -> None:
    nome = (arquivo or "").strip()
    if not nome:
        return
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    caminho = UPLOAD_DIR / nome
    if caminho.exists():
        caminho.unlink()
    for variante in listar_variantes(nome):
        caminho_v = UPLOAD_DIR / variante
        if caminho_v.exists():
            caminho_v.unlink()


def gerar_variantes(arquivo: str) -> list[str]:
    """
    Mantém o arquivo original e gera versões menores (JPG) para srcset.
    Retorna os nomes das variantes criadas (ou já existentes).
    """
    from PIL import Image, ImageOps

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    origem = UPLOAD_DIR / arquivo
    if not origem.exists():
        return []

    criados: list[str] = []
    try:
        with Image.open(origem) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode in ("RGBA", "P", "LA"):
                fundo = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P":
                    im = im.convert("RGBA")
                if im.mode in ("RGBA", "LA"):
                    fundo.paste(im, mask=im.split()[-1])
                else:
                    fundo.paste(im)
                im = fundo
            elif im.mode != "RGB":
                im = im.convert("RGB")

            largura_orig, _altura_orig = im.size
            for largura in VARIANT_WIDTHS:
                nome = nome_variante(arquivo, largura)
                destino = UPLOAD_DIR / nome
                if destino.exists():
                    criados.append(nome)
                    continue
                if largura_orig <= largura:
                    # Original já é menor/igual: copia como JPG naquele rótulo
                    # para o srcset ter candidatos estáveis.
                    im.save(destino, format="JPEG", quality=82, optimize=True)
                else:
                    copia = im.copy()
                    copia.thumbnail((largura, largura * 4), Image.Resampling.LANCZOS)
                    copia.save(destino, format="JPEG", quality=82, optimize=True)
                criados.append(nome)
    except OSError:
        return []
    return criados


def dimensao_imagem(arquivo: str) -> tuple[int, int]:
    """Largura/altura do original (fallback seguro para lightbox)."""
    from PIL import Image

    caminho = UPLOAD_DIR / arquivo
    if not caminho.exists():
        return (1600, 1200)
    try:
        with Image.open(caminho) as im:
            return im.size
    except OSError:
        return (1600, 1200)


def url_static_galeria(arquivo: str) -> str:
    """Caminho relativo /static/... (sem depender do request Flask)."""
    return f"/static/uploads/galeria/{arquivo}"


def srcset_galeria(arquivo: str) -> str:
    """
    srcset com variantes existentes + original (maior nitidez no desktop).
    Fotos antigas sem variantes caem só no original.
    """
    partes: list[str] = []
    for largura in VARIANT_WIDTHS:
        nome = nome_variante(arquivo, largura)
        if (UPLOAD_DIR / nome).exists():
            partes.append(f"{url_static_galeria(nome)} {largura}w")
    # Original: usa dimensão real quando possível
    w_orig, _ = dimensao_imagem(arquivo)
    partes.append(f"{url_static_galeria(arquivo)} {max(w_orig, VARIANT_WIDTHS[-1])}w")
    return ", ".join(partes)


def sizes_galeria() -> str:
    """Aproxima o grid da galeria (cards ~220px+)."""
    return "(max-width: 640px) 92vw, (max-width: 1024px) 45vw, 320px"


def garantir_variantes_existentes(limite: int | None = None) -> int:
    """
    Gera variantes faltantes para fotos já publicadas (upload antigo).
    Seguro: não altera o arquivo original nem o banco.
    """
    init_db()
    geradas = 0
    with _connect() as conn:
        rows = conn.execute("SELECT arquivo FROM fotos ORDER BY id").fetchall()
    for i, row in enumerate(rows):
        if limite is not None and i >= limite:
            break
        arquivo = (row["arquivo"] or "").strip()
        if not arquivo:
            continue
        if not (UPLOAD_DIR / arquivo).exists():
            continue
        faltando = [
            nome
            for nome in listar_variantes(arquivo)
            if not (UPLOAD_DIR / nome).exists()
        ]
        if not faltando:
            continue
        if gerar_variantes(arquivo):
            geradas += 1
    return geradas


def seed_fotos_iniciais() -> int | None:
    """
    Só na primeira subida (galeria vazia e sem flag).
    Depois que a mídia apaga ou publica, NÃO recria fotos sozinho.
    """
    import shutil

    init_db()
    if galeria_ja_gerenciada():
        return None
    if listar_posts_ativos():
        # Já há conteúdo (ou DB antigo): marca para não reseedar no futuro
        marcar_galeria_gerenciada(motivo="ja_tinha_posts")
        return None
    if not SEED_DIR.exists():
        return None

    arquivos_seed = sorted(
        p for p in SEED_DIR.iterdir() if p.is_file() and extensao_ok(p.name)
    )
    if not arquivos_seed:
        return None

    salvos: list[str] = []
    for origem in arquivos_seed:
        destino = UPLOAD_DIR / origem.name
        if not destino.exists():
            shutil.copy2(origem, destino)
        gerar_variantes(origem.name)
        salvos.append(origem.name)

    post_id = criar_post(
        culto_titulo="Culto da igreja",
        culto_dia="Recente",
        titulo="Fotos do culto",
        arquivos=salvos,
    )
    marcar_galeria_gerenciada(motivo="seed_inicial")
    return post_id
