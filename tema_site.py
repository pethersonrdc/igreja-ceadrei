"""
Tema visual do site (cores, fontes, fundo) — editável pelo Portal CEASDREI.
Salvo em DATA_DIR/tema_site.json (disco persistente no VPS).
"""

from __future__ import annotations

import json
from pathlib import Path

import persistencia

TEMA_DEFAULT = {
    "cor_texto": "#122033",
    "cor_fundo": "#f7f4ef",
    "cor_destaque": "#b8893a",
    "cor_secundaria": "#1a3a52",
    "fonte_titulo": "Cormorant Garamond",
    "fonte_texto": "Outfit",
    "estilo_fundo": "padrao",
}

FONTES_TITULO = [
    "Cormorant Garamond",
    "Playfair Display",
    "Libre Baskerville",
    "Merriweather",
    "Lora",
]

FONTES_TEXTO = [
    "Outfit",
    "Source Sans 3",
    "Lato",
    "Nunito Sans",
    "Rubik",
]

ESTILOS_FUNDO = {
    "padrao": "Gradiente claro com dourado suave (atual)",
    "suave": "Fundo creme limpo, sem radiais fortes",
    "escuro": "Atmosfera mais escura (marinho)",
    "claro": "Quase branco, alto contraste",
}


def _path() -> Path:
    return persistencia.db_path("tema_site.json")


def carregar() -> dict:
    path = _path()
    if not path.exists():
        return dict(TEMA_DEFAULT)
    try:
        dados = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(TEMA_DEFAULT)
    out = dict(TEMA_DEFAULT)
    out.update({k: v for k, v in dados.items() if k in TEMA_DEFAULT})
    return out


def salvar(dados: dict) -> dict:
    tema = dict(TEMA_DEFAULT)
    for chave in TEMA_DEFAULT:
        valor = dados.get(chave)
        if isinstance(valor, str):
            valor = valor.strip()
        if valor:
            tema[chave] = valor
    if tema["fonte_titulo"] not in FONTES_TITULO:
        tema["fonte_titulo"] = TEMA_DEFAULT["fonte_titulo"]
    if tema["fonte_texto"] not in FONTES_TEXTO:
        tema["fonte_texto"] = TEMA_DEFAULT["fonte_texto"]
    if tema["estilo_fundo"] not in ESTILOS_FUNDO:
        tema["estilo_fundo"] = TEMA_DEFAULT["estilo_fundo"]
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return tema


def google_fonts_href(tema: dict | None = None) -> str:
    tema = tema or carregar()
    tit = tema["fonte_titulo"].replace(" ", "+")
    txt = tema["fonte_texto"].replace(" ", "+")
    familia_tit = f"family={tit}:ital,wght@0,600;0,700;1,600"
    familia_txt = f"family={txt}:wght@400;600"
    return (
        "https://fonts.googleapis.com/css2?"
        f"{familia_tit}&{familia_txt}&display=swap"
    )


def css_vars(tema: dict | None = None) -> str:
    """CSS inline para :root a partir do tema salvo."""
    tema = tema or carregar()
    ink = tema["cor_texto"]
    paper = tema["cor_fundo"]
    gold = tema["cor_destaque"]
    sea = tema["cor_secundaria"]
    font_display = tema["fonte_titulo"]
    font_body = tema["fonte_texto"]
    estilo = tema["estilo_fundo"]

    if estilo == "suave":
        bg = f"linear-gradient(180deg, {paper} 0%, {paper} 100%)"
    elif estilo == "escuro":
        bg = (
            f"radial-gradient(1000px 500px at 10% -10%, rgba(184,137,58,0.18), transparent 55%),"
            f"linear-gradient(180deg, {sea} 0%, #0d2436 100%)"
        )
    elif estilo == "claro":
        bg = "linear-gradient(180deg, #ffffff 0%, #f4f4f4 100%)"
    else:
        bg = (
            f"radial-gradient(1200px 600px at 10% -10%, {gold}22, transparent 55%),"
            f"radial-gradient(900px 500px at 100% 0%, {sea}1a, transparent 50%),"
            f"linear-gradient(180deg, #fbf8f3 0%, {paper} 40%, #efe8dc 100%)"
        )

    if estilo == "escuro":
        ink_use = "#f3efe8"
        ink_soft = "#c9c2b6"
    else:
        ink_use = ink
        ink_soft = ink

    return (
        ":root{"
        f"--ink:{ink_use};"
        f"--ink-soft:{ink_soft};"
        f"--paper:{paper};"
        f"--gold:{gold};"
        f"--gold-deep:{gold};"
        f"--sea:{sea};"
        f"--sea-deep:{sea};"
        f"--font-display:\"{font_display}\",Georgia,serif;"
        f"--font-body:\"{font_body}\",\"Segoe UI\",sans-serif;"
        f"--portal-bg:{bg};"
        "}"
        "body{background:var(--portal-bg);}"
    )
