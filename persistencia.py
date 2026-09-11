"""
Disco persistente para SQLite e uploads (Render).

Defina DATA_DIR=/var/data no serviço e monte um Persistent Disk nesse caminho.
Sem DATA_DIR, usa data/ e static/uploads/ do repositório (desenvolvimento local).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_DATA = BASE_DIR / "data"
STATIC_UPLOADS = BASE_DIR / "static" / "uploads"

UPLOAD_SUBDIRS = (
    "galeria",
    "louvor",
    "porta_altar",
    "mocidade",
    "pastores",
    "batismo",
    "casais",
    "arraial",
    "lideres",
    "leoas",
    "leaodejuda",
    "maranata",
    "soldadinhos",
    "home",
    "aniversario",
    "historia",
)


def usando_disco_persistente() -> bool:
    return bool((os.environ.get("DATA_DIR") or "").strip())


def data_root() -> Path:
    bruto = (os.environ.get("DATA_DIR") or "").strip()
    root = Path(bruto) if bruto else REPO_DATA
    root.mkdir(parents=True, exist_ok=True)
    return root


def db_path(filename: str) -> Path:
    return data_root() / filename


def upload_dir(subdir: str) -> Path:
    """
    Pasta de arquivos enviados.
    Com DATA_DIR: grava no disco persistente e espelha em static/uploads/<subdir>
    via symlink, para url_for('static', ...) continuar funcionando.
    """
    nome = (subdir or "").strip().strip("/").replace("\\", "/")
    if not nome:
        raise ValueError("subdir de upload vazio")

    if usando_disco_persistente():
        destino = data_root() / "uploads" / nome
        destino.mkdir(parents=True, exist_ok=True)
        link = STATIC_UPLOADS / nome
        _garantir_link_upload(link, destino)
        return destino

    pasta = STATIC_UPLOADS / nome
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _garantir_link_upload(link: Path, destino: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    destino.mkdir(parents=True, exist_ok=True)

    try:
        # Link quebrado (ex.: apontava para /tmp/... de teste) → remove e recria
        if link.is_symlink() and not link.exists():
            link.unlink()
        if link.is_symlink():
            if link.resolve() == destino.resolve():
                return
            link.unlink()
        elif link.exists():
            if link.is_dir():
                for item in link.iterdir():
                    alvo = destino / item.name
                    if item.name == ".gitkeep":
                        continue
                    if not alvo.exists():
                        shutil.move(str(item), str(alvo))
                shutil.rmtree(link)
            else:
                link.unlink()
        link.symlink_to(destino, target_is_directory=True)
    except OSError:
        # Sem symlink: mantém cópia em static/uploads para o Nginx servir.
        _espelhar_pasta(destino, STATIC_UPLOADS / destino.name)


def _espelhar_pasta(origem: Path, destino_static: Path) -> None:
    destino_static.mkdir(parents=True, exist_ok=True)
    if not origem.exists():
        return
    for item in origem.iterdir():
        if not item.is_file() or item.name == ".gitkeep":
            continue
        alvo = destino_static / item.name
        if not alvo.exists() or item.stat().st_mtime > alvo.stat().st_mtime:
            shutil.copy2(item, alvo)


def espelhar_arquivo_upload(subdir: str, nome_arquivo: str) -> Path | None:
    """
    Garante que um arquivo novo em DATA_DIR também exista em static/uploads/
    (necessário quando o symlink falha ou aponta para caminho inválido).
    """
    nome = (subdir or "").strip().strip("/")
    arquivo = (nome_arquivo or "").strip()
    if not nome or not arquivo:
        return None

    origem_dir = upload_dir(nome)
    origem = origem_dir / arquivo
    if not origem.is_file():
        return None

    link = STATIC_UPLOADS / nome
    # Se o link está ok, o arquivo já é visível via static/
    try:
        if link.is_symlink() and link.resolve() == origem_dir.resolve():
            return origem
    except OSError:
        pass

    destino_dir = STATIC_UPLOADS / nome
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / arquivo
    try:
        if link.is_symlink() and not link.exists():
            link.unlink()
    except OSError:
        pass

    # Se static/uploads/<subdir> ainda é symlink quebrado para outro sítio,
    # remove e usa pasta real para a cópia.
    try:
        if link.is_symlink():
            try:
                ok = link.resolve() == origem_dir.resolve()
            except OSError:
                ok = False
            if not ok:
                link.unlink()
                destino_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    shutil.copy2(origem, destino)
    return destino


def preparar() -> Path:
    """Garante DATA_DIR e pastas de upload no boot do app."""
    root = data_root()
    (root / "uploads").mkdir(parents=True, exist_ok=True)
    for sub in UPLOAD_SUBDIRS:
        upload_dir(sub)
        # Repara espelho static após deploy/git reset
        destino = root / "uploads" / sub if usando_disco_persistente() else STATIC_UPLOADS / sub
        if usando_disco_persistente():
            _garantir_link_upload(STATIC_UPLOADS / sub, destino)
            # Cópia de segurança se o link continuar inválido
            try:
                link = STATIC_UPLOADS / sub
                if not link.exists() or (link.is_dir() and not link.is_symlink()):
                    _espelhar_pasta(destino, STATIC_UPLOADS / sub)
            except OSError:
                _espelhar_pasta(destino, STATIC_UPLOADS / sub)
    return root