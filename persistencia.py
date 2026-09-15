"""
Disco persistente para SQLite e uploads (Render / Hostinger).

Defina DATA_DIR=/var/data no serviço e monte um Persistent Disk nesse caminho.
Sem DATA_DIR, usa data/ e static/uploads/ do repositório (desenvolvimento local).

Importante: com DATA_DIR NÃO usamos symlink para servir arquivos.
O Nginx (alias /static/) falha com symlink quebrado ou sem permissão de
seguir link — por isso o espelho em static/uploads/ é sempre pasta real + cópia.
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


def _pasta_persistente(subdir: str) -> Path:
    nome = (subdir or "").strip().strip("/").replace("\\", "/")
    if not nome:
        raise ValueError("subdir de upload vazio")
    pasta = data_root() / "uploads" / nome
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _remover_symlink_se_houver(caminho: Path) -> None:
    try:
        if caminho.is_symlink():
            caminho.unlink()
    except OSError:
        pass


def _espelhar_pasta(origem: Path, destino_static: Path) -> None:
    destino_static.mkdir(parents=True, exist_ok=True)
    if not origem.exists():
        return
    for item in origem.iterdir():
        if not item.is_file() or item.name == ".gitkeep":
            continue
        alvo = destino_static / item.name
        try:
            if not alvo.exists() or item.stat().st_mtime > alvo.stat().st_mtime:
                shutil.copy2(item, alvo)
        except OSError:
            continue


def garantir_espelho_real(subdir: str) -> Path:
    """
    Garante pasta REAL em static/uploads/<subdir> (nunca symlink)
    e copia os arquivos do DATA_DIR para o Nginx servir.
    Retorna a pasta de gravação (DATA_DIR quando ativo).
    """
    nome = (subdir or "").strip().strip("/").replace("\\", "/")
    if not nome:
        raise ValueError("subdir de upload vazio")

    if not usando_disco_persistente():
        pasta = STATIC_UPLOADS / nome
        pasta.mkdir(parents=True, exist_ok=True)
        return pasta

    origem = _pasta_persistente(nome)
    destino = STATIC_UPLOADS / nome
    _remover_symlink_se_houver(destino)
    if destino.exists() and not destino.is_dir():
        try:
            destino.unlink()
        except OSError:
            pass
    destino.mkdir(parents=True, exist_ok=True)
    _espelhar_pasta(origem, destino)
    return origem


def upload_dir(subdir: str) -> Path:
    """
    Pasta de gravação dos uploads.
    Com DATA_DIR: grava no disco persistente e espelha cópia real em static/uploads/.
    """
    return garantir_espelho_real(subdir)


def espelhar_arquivo_upload(subdir: str, nome_arquivo: str) -> Path | None:
    """
    Copia um arquivo do disco persistente para static/uploads/ (pasta real).
    Sempre copia — não confia em symlink (Nginx no Hostinger não serve bem).
    """
    nome = (subdir or "").strip().strip("/")
    arquivo = (nome_arquivo or "").strip()
    if not nome or not arquivo:
        return None

    # Garante pasta real (remove symlink quebrado se existir)
    origem_dir = garantir_espelho_real(nome)
    origem = origem_dir / arquivo
    if not origem.is_file():
        return None

    destino_dir = STATIC_UPLOADS / nome
    _remover_symlink_se_houver(destino_dir)
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / arquivo
    try:
        shutil.copy2(origem, destino)
    except OSError:
        return None
    return destino


def preparar() -> Path:
    """Garante DATA_DIR e espelho real de todas as pastas de upload no boot."""
    root = data_root()
    (root / "uploads").mkdir(parents=True, exist_ok=True)
    STATIC_UPLOADS.mkdir(parents=True, exist_ok=True)
    for sub in UPLOAD_SUBDIRS:
        garantir_espelho_real(sub)
    return root
