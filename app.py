"""
Igreja CEADREI — servidor Flask com páginas HTML, API JSON e galeria admin.
"""

from __future__ import annotations

import os
import uuid
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import gallery

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ceadrei-dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB por upload

# Senha do painel da mídia (troque em produção via variável de ambiente)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ceasdrei")
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)


def load_json(name: str) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        return {}
    return __import__("json").loads(path.read_text(encoding="utf-8"))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_ok"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_admin():
    return {"admin_logado": bool(session.get("admin_ok"))}

@app.before_request
def _limpeza_galeria():
    # Limpa fotos expiradas em rotas públicas relevantes e no admin
    if request.endpoint in {"home", "galeria_publica", "admin_galeria", "api_galeria"}:
        gallery.limpar_expirados()


@app.route("/")
def home():
    igreja = load_json("igreja.json")
    cultos = load_json("cultos.json").get("cultos", [])[:3]
    posts = gallery.listar_posts_ativos()
    destaque = posts[0] if posts else None
    return render_template(
        "index.html",
        igreja=igreja,
        cultos=cultos,
        galeria_destaque=destaque,
    )


@app.route("/sobre")
def sobre():
    igreja = load_json("igreja.json")
    return render_template("sobre.html", igreja=igreja)


@app.route("/cultos")
def cultos_page():
    igreja = load_json("igreja.json")
    cultos = load_json("cultos.json").get("cultos", [])
    return render_template("cultos.html", igreja=igreja, cultos=cultos)


@app.route("/eventos")
def eventos_page():
    igreja = load_json("igreja.json")
    eventos = load_json("eventos.json").get("eventos", [])
    return render_template("eventos.html", igreja=igreja, eventos=eventos)


@app.route("/contato")
def contato():
    igreja = load_json("igreja.json")
    return render_template("contato.html", igreja=igreja)


@app.route("/galeria")
def galeria_publica():
    igreja = load_json("igreja.json")
    posts = gallery.listar_posts_ativos()
    return render_template("galeria.html", igreja=igreja, posts=posts)


# ---------- Admin (mídia da igreja) ----------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    igreja = load_json("igreja.json")
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if check_password_hash(ADMIN_PASSWORD_HASH, senha):
            session["admin_ok"] = True
            destino = request.args.get("next") or url_for("admin_galeria")
            return redirect(destino)
        erro = "Senha incorreta. Tente novamente."
    if session.get("admin_ok"):
        return redirect(url_for("admin_galeria"))
    return render_template("admin_login.html", igreja=igreja, erro=erro)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/admin/galeria", methods=["GET", "POST"])
@login_required
def admin_galeria():
    igreja = load_json("igreja.json")
    cultos = load_json("cultos.json").get("cultos", [])

    if request.method == "POST":
        culto_titulo = request.form.get("culto_titulo", "").strip()
        culto_dia = request.form.get("culto_dia", "").strip()
        titulo = request.form.get("titulo", "").strip() or f"Fotos — {culto_titulo}"
        arquivos = request.files.getlist("fotos")

        salvos = []
        gallery.init_db()
        for arquivo in arquivos:
            if not arquivo or not arquivo.filename:
                continue
            if not gallery.extensao_ok(arquivo.filename):
                flash(f"Formato não permitido: {arquivo.filename}", "erro")
                continue
            nome_seguro = secure_filename(arquivo.filename)
            extensao = Path(nome_seguro).suffix.lower()
            nome_final = f"{uuid.uuid4().hex}{extensao}"
            destino = gallery.UPLOAD_DIR / nome_final
            arquivo.save(destino)
            salvos.append(nome_final)

        if not culto_titulo or not culto_dia:
            flash("Escolha o culto e o dia.", "erro")
        elif not salvos:
            flash("Envie ao menos uma foto válida (JPG, PNG, WEBP ou GIF).", "erro")
        else:
            gallery.criar_post(culto_titulo, culto_dia, titulo, salvos)
            flash(
                f"Postagem publicada! As fotos ficam no ar por {gallery.DIAS_EXPIRACAO} dias.",
                "ok",
            )
            return redirect(url_for("admin_galeria"))

    posts = gallery.listar_posts_ativos()
    return render_template(
        "admin_galeria.html",
        igreja=igreja,
        cultos=cultos,
        posts=posts,
        dias_expiracao=gallery.DIAS_EXPIRACAO,
    )


@app.route("/admin/galeria/<int:post_id>/apagar", methods=["POST"])
@login_required
def admin_apagar_post(post_id: int):
    if gallery.apagar_post(post_id):
        flash("Postagem apagada.", "ok")
    else:
        flash("Postagem não encontrada.", "erro")
    return redirect(url_for("admin_galeria"))


# ---------- API ----------

@app.route("/api/info")
def api_info():
    return jsonify(load_json("igreja.json"))


@app.route("/api/cultos")
def api_cultos():
    return jsonify(load_json("cultos.json"))


@app.route("/api/eventos")
def api_eventos():
    return jsonify(load_json("eventos.json"))


@app.route("/api/contato")
def api_contato():
    igreja = load_json("igreja.json")
    return jsonify(
        {
            "nome": igreja.get("nome"),
            "endereco": igreja.get("endereco"),
            "contato": igreja.get("contato"),
        }
    )


@app.route("/api/galeria")
def api_galeria():
    posts = gallery.listar_posts_ativos()
    return jsonify({"posts": posts, "dias_expiracao": gallery.DIAS_EXPIRACAO})


@app.route("/data/<path:filename>")
def data_files(filename: str):
    """Expõe os JSON para o front estático / GitHub Pages."""
    return send_from_directory(DATA_DIR, filename)


# Garante pastas/banco mesmo com Gunicorn (produção)
gallery.init_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
