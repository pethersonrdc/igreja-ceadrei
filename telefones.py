"""Comparação de telefone e nome para cadastro único."""

from __future__ import annotations

import re
import unicodedata


def so_digitos(telefone: str) -> str:
    return re.sub(r"\D+", "", telefone or "")


def normalizar_telefone(telefone: str) -> str:
    """Só dígitos, sem +55, no máximo DDD + número (11)."""
    d = so_digitos(telefone)
    if d.startswith("55") and len(d) >= 12:
        d = d[2:]
    if d.startswith("0") and len(d) >= 11:
        d = d[1:]
    if len(d) > 11:
        d = d[-11:]
    return d


def telefones_iguais(a: str, b: str) -> bool:
    """Compara telefone mesmo com máscara, DDD ou código do país."""
    na = normalizar_telefone(a)
    nb = normalizar_telefone(b)
    if len(na) < 8 or len(nb) < 8:
        return False
    if na == nb:
        return True
    menor, maior = (na, nb) if len(na) <= len(nb) else (nb, na)
    return (len(maior) - len(menor) <= 4) and maior.endswith(menor)


def nome_chave(nome: str) -> str:
    texto = unicodedata.normalize("NFD", (nome or "").strip().lower())
    sem_acento = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sem_acento).strip()
