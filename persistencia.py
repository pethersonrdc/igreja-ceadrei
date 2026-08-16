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
        # Ambiente sem permissão de symlink: usa a pasta persistente direto.
        # Templates que apontam para static/uploads precisam do link;
        # nesse caso copiamos arquivos para static também.
        pasta_static = STATIC_UPLOADS / destino.name
        pasta_static.mkdir(parents=True, exist_ok=True)
        for item in destino.iterdir():
            alvo = pasta_static / item.name
            if item.is_file() and not alvo.exists():
                shutil.copy2(item, alvo)


def preparar() -> Path:
    """Garante DATA_DIR e pastas de upload no boot do app."""
    root = data_root()
    (root / "uploads").mkdir(parents=True, exist_ok=True)
    for sub in UPLOAD_SUBDIRS:
        upload_dir(sub)
    return root
