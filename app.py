"""
Igreja CEASDREI — servidor Flask com páginas HTML, API JSON e galeria admin.
"""

from __future__ import annotations

import io
import os
import uuid
from datetime import date
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import arraial
import batismo
import campanha_eventos
import casais
import gallery
import louvor
import mocidade
import pastores
import lideres_midia
import porta_altar

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ceasdrei-dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 120 * 1024 * 1024  # 120 MB (vídeos do Papo de Altar)

# Senha do painel da mídia (troque em produção via variável de ambiente)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ceasdrei")
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Senha do painel do Evento Batismo (Evangelista Sueli)
BATISMO_PASSWORD = os.environ.get("BATISMO_PASSWORD", "Sueli")
BATISMO_PASSWORD_HASH = generate_password_hash(BATISMO_PASSWORD)

# Senha do painel do Encontro de Casais (Diac. Robson & Diac. Luana)
CASAIS_PASSWORD = os.environ.get("CASAIS_PASSWORD", "Robson&Luana")
CASAIS_PASSWORD_HASH = generate_password_hash(CASAIS_PASSWORD)

# Senha do painel dos Pastores
PASTORES_PASSWORD = os.environ.get("PASTORES_PASSWORD", "Solange123")
PASTORES_PASSWORD_HASH = generate_password_hash(PASTORES_PASSWORD)

# Senha do departamento Arraiá / Cantina (Diac. Cássia)
ARRAIAL_PASSWORD = os.environ.get("ARRAIAL_PASSWORD", "Cassia")
ARRAIAL_PASSWORD_HASH = generate_password_hash(ARRAIAL_PASSWORD)

# Senha dos Líderes dos Filhos do Rei (Diác. Natan e Diác. Ana Beatriz)
MOCIDADE_PASSWORD = os.environ.get("MOCIDADE_PASSWORD", "Mocidade")
MOCIDADE_PASSWORD_HASH = generate_password_hash(MOCIDADE_PASSWORD)

# Senhas Leoas da Fé / Leão de Judá / Dança Maranata / Soldadinhos de Cristo
LEOAS_PASSWORD = os.environ.get("LEOAS_PASSWORD", "Leoasdafe")
LEOAS_PASSWORD_HASH = generate_password_hash(LEOAS_PASSWORD)
LEAODEJUDA_PASSWORD = os.environ.get("LEAODEJUDA_PASSWORD", "Leaodejuda")
LEAODEJUDA_PASSWORD_HASH = generate_password_hash(LEAODEJUDA_PASSWORD)
MARANATA_PASSWORD = os.environ.get("MARANATA_PASSWORD", "Maranatas")
MARANATA_PASSWORD_HASH = generate_password_hash(MARANATA_PASSWORD)
SOLDADINHOS_PASSWORD = os.environ.get("SOLDADINHOS_PASSWORD", "Soldadinhos")
SOLDADINHOS_PASSWORD_HASH = generate_password_hash(SOLDADINHOS_PASSWORD)

# Senha do Grupo de Louvor
LOUVOR_PASSWORD = os.environ.get("LOUVOR_PASSWORD", "Louvor")
LOUVOR_PASSWORD_HASH = generate_password_hash(LOUVOR_PASSWORD)

CAMPANHA_PASSWORD_HASH = {
    "leoas": LEOAS_PASSWORD_HASH,
    "leaodejuda": LEAODEJUDA_PASSWORD_HASH,
    "maranata": MARANATA_PASSWORD_HASH,
    "soldadinhos": SOLDADINHOS_PASSWORD_HASH,
}
CAMPANHA_SESSION_KEY = {
    "leoas": "leoas_ok",
    "leaodejuda": "leaodejuda_ok",
    "maranata": "maranata_ok",
    "soldadinhos": "soldadinhos_ok",
}


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


def batismo_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("batismo_ok"):
            return redirect(url_for("batismo_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def casais_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("casais_ok"):
            return redirect(url_for("casais_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def pastores_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("pastores_ok"):
            return redirect(url_for("pastores_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def arraial_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("arraial_ok"):
            return redirect(url_for("arraial_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def mocidade_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("mocidade_ok"):
            return redirect(url_for("mocidade_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def campanha_login_required(view):
    @wraps(view)
    def wrapped(slug: str, *args, **kwargs):
        if slug not in CAMPANHA_SESSION_KEY:
            return redirect(url_for("eventos_page"))
        if not session.get(CAMPANHA_SESSION_KEY[slug]):
            return redirect(url_for("campanha_login", slug=slug, next=request.path))
        return view(slug, *args, **kwargs)

    return wrapped


def louvor_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("louvor_ok"):
            return redirect(url_for("louvor_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_admin():
    return {
        "admin_logado": bool(session.get("admin_ok")),
        "batismo_logado": bool(session.get("batismo_ok")),
        "casais_logado": bool(session.get("casais_ok")),
        "pastores_logado": bool(session.get("pastores_ok")),
        "arraial_logado": bool(session.get("arraial_ok")),
        "mocidade_logado": bool(session.get("mocidade_ok")),
        "leoas_logado": bool(session.get("leoas_ok")),
        "leaodejuda_logado": bool(session.get("leaodejuda_ok")),
        "maranata_logado": bool(session.get("maranata_ok")),
        "soldadinhos_logado": bool(session.get("soldadinhos_ok")),
        "louvor_logado": bool(session.get("louvor_ok")),
    }


def mensagem_do_dia() -> dict:
    """Retorna um versículo diferente a cada dia do ano."""
    lista = load_json("mensagens_dia.json").get("mensagens") or []
    if not lista:
        return {
            "texto": "Porque onde estiverem dois ou três reunidos em meu nome, aí estou eu no meio deles.",
            "referencia": "Mateus 18:20",
        }
    indice = date.today().timetuple().tm_yday % len(lista)
    item = lista[indice]
    return {
        "texto": (item.get("texto") or "").strip(),
        "referencia": (item.get("referencia") or "").strip(),
    }


@app.route("/")
def home():
    igreja = load_json("igreja.json")
    cultos = load_json("cultos.json").get("cultos", [])[:3]
    posts = gallery.listar_posts_ativos()
    destaque = posts[0] if posts else None
    fotos_batismo = batismo.listar_fotos()
    fotos_casais = casais.listar_fotos()
    programacao_casais = casais.obter_programacao()
    escala_hoje = pastores.obter_proxima_escala()
    destaque_culto = pastores.obter_destaque()
    eventos_destaque = pastores.eventos_destaque_home(6)
    info_arraial = arraial.info_evento()
    aviso_home = gallery.obter_aviso_home()
    ministerios_destaque = campanha_eventos.listar_destaques_home()
    mocidade_destaque = mocidade.obter_destaque_publico()
    if mocidade_destaque:
        ministerios_destaque = sorted(
            [*ministerios_destaque, mocidade_destaque],
            key=lambda x: x.get("data_obj") or date.max,
        )
    whatsapp_escala_obreiros = ""
    if escala_hoje:
        whatsapp_escala_obreiros = pastores.url_whatsapp(
            pastores.texto_whatsapp_dia(
                escala_hoje,
                igreja.get("nome") or "IGREJA CEASDREI",
                url_for("comunicado_obreiros", _external=True),
            )
        )
    escala_louvor = louvor.obter_proxima_escala()
    whatsapp_escala_louvor = ""
    if escala_louvor:
        whatsapp_escala_louvor = louvor.url_whatsapp(
            louvor.texto_whatsapp_dia(
                escala_louvor,
                igreja.get("nome") or "IGREJA CEASDREI",
                url_for("louvor_page", _external=True),
            )
        )
    return render_template(
        "index.html",
        igreja=igreja,
        cultos=cultos,
        galeria_destaque=destaque,
        batismo_fotos=fotos_batismo,
        casais_fotos=fotos_casais,
        casais_programacao=programacao_casais,
        escala_hoje=escala_hoje,
        destaque_culto=destaque_culto,
        eventos_destaque=eventos_destaque,
        ministerios_destaque=ministerios_destaque,
        arraial=info_arraial,
        cantina_texto=arraial.obter_cantina(),
        aviso_home=aviso_home,
        whatsapp_escala_obreiros=whatsapp_escala_obreiros,
        escala_louvor=escala_louvor,
        whatsapp_escala_louvor=whatsapp_escala_louvor,
    )


@app.route("/mensagem-do-dia")
def mensagem_dia_page():
    igreja = load_json("igreja.json")
    return render_template(
        "mensagem_dia.html",
        igreja=igreja,
        mensagem_dia=mensagem_do_dia(),
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
    return render_template(
        "eventos.html",
        igreja=igreja,
        eventos=eventos,
        fotos_lideres=lideres_midia.mapa_fotos(),
    )


@app.route("/contato")
def contato():
    igreja = load_json("igreja.json")
    return render_template("contato.html", igreja=igreja)


@app.route("/galeria")
def galeria_publica():
    igreja = load_json("igreja.json")
    posts = gallery.listar_posts_ativos()
    return render_template("galeria.html", igreja=igreja, posts=posts)


# ---------- Papo de Altar (mídia — mesmo login do painel) ----------

@app.route("/porta-do-altar")
def porta_altar_page():
    igreja = load_json("igreja.json")
    return render_template(
        "porta_altar.html",
        igreja=igreja,
        videos_culto=porta_altar.listar_videos_publicos(tipo="pos_culto"),
        videos_papo=porta_altar.listar_videos_publicos(tipo="papo_altar"),
        perguntas=porta_altar.listar_perguntas(apenas_ativas=True),
        aguardando=porta_altar.listar_videos_aguardando()[:6],
    )


@app.route("/porta-do-altar/admin", methods=["GET", "POST"])
@login_required
def porta_altar_admin():
    igreja = load_json("igreja.json")
    edit_video = None
    edit_pergunta = None
    edit_video_id = request.args.get("editar_video", type=int)
    edit_pergunta_id = request.args.get("editar_pergunta", type=int)
    if edit_video_id:
        edit_video = porta_altar.obter_video(edit_video_id)
    if edit_pergunta_id:
        edit_pergunta = porta_altar.obter_pergunta(edit_pergunta_id)

    if request.method == "POST":
        acao = request.form.get("acao", "video_criar").strip()

        if acao == "pergunta_salvar":
            pergunta = request.form.get("pergunta", "").strip()
            resposta = request.form.get("resposta", "").strip()
            ordem_raw = request.form.get("ordem", "0").strip() or "0"
            pergunta_id = request.form.get("pergunta_id", type=int)
            try:
                ordem = int(ordem_raw)
            except ValueError:
                ordem = 0
            if not pergunta:
                flash("Escreva a pergunta.", "erro")
                return redirect(url_for("porta_altar_admin"))
            porta_altar.salvar_pergunta(
                pergunta=pergunta,
                resposta=resposta,
                ordem=ordem,
                pergunta_id=pergunta_id,
            )
            flash("Pergunta salva.", "ok")
            return redirect(url_for("porta_altar_admin") + "#perguntas")

        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        culto_titulo = request.form.get("culto_titulo", "").strip()
        termino_em = request.form.get("termino_em", "").strip()
        tipo = request.form.get("tipo", "pos_culto").strip() or "pos_culto"
        link_instagram = request.form.get("link_instagram", "").strip()
        link_facebook = request.form.get("link_facebook", "").strip()
        palavra_culto = request.form.get("palavra_culto", "").strip()
        arquivo = request.files.get("video")
        capa_file = request.files.get("capa")
        video_id = request.form.get("video_id", type=int)

        if not titulo or not termino_em:
            flash("Informe o título e o horário de liberação.", "erro")
            return redirect(url_for("porta_altar_admin"))

        porta_altar.init_db()
        nome_video = ""
        nome_capa = ""

        if arquivo and arquivo.filename:
            if not porta_altar.extensao_video_ok(arquivo.filename):
                flash("Vídeo: use MP4, WEBM, OGG ou MOV.", "erro")
                return redirect(url_for("porta_altar_admin"))
            nome_seguro = secure_filename(arquivo.filename)
            extensao = Path(nome_seguro).suffix.lower()
            nome_video = f"{uuid.uuid4().hex}{extensao}"
            arquivo.save(porta_altar.UPLOAD_DIR / nome_video)

        if capa_file and capa_file.filename:
            if not porta_altar.extensao_capa_ok(capa_file.filename):
                flash("Capa: use JPG, PNG, WEBP ou GIF.", "erro")
                return redirect(url_for("porta_altar_admin"))
            capa_segura = secure_filename(capa_file.filename)
            capa_ext = Path(capa_segura).suffix.lower()
            nome_capa = f"{uuid.uuid4().hex}{capa_ext}"
            capa_file.save(porta_altar.UPLOAD_DIR / nome_capa)

        if acao == "video_editar" and video_id:
            if porta_altar.atualizar_video(
                video_id,
                titulo=titulo,
                descricao=descricao,
                culto_titulo=culto_titulo,
                termino_em=termino_em,
                tipo=tipo,
                arquivo=nome_video,
                capa=nome_capa,
                link_instagram=link_instagram,
                link_facebook=link_facebook,
                palavra_culto=palavra_culto,
            ):
                flash("Vídeo atualizado.", "ok")
            else:
                flash("Vídeo não encontrado.", "erro")
            return redirect(url_for("porta_altar_admin"))

        if not nome_video:
            flash("Envie o arquivo de vídeo.", "erro")
            return redirect(url_for("porta_altar_admin"))

        porta_altar.criar_video(
            titulo=titulo,
            descricao=descricao,
            arquivo=nome_video,
            capa=nome_capa,
            culto_titulo=culto_titulo,
            termino_em=termino_em,
            tipo=tipo,
            link_instagram=link_instagram,
            link_facebook=link_facebook,
            palavra_culto=palavra_culto,
        )
        flash("Vídeo salvo. Ele aparece na página após o horário de liberação.", "ok")
        return redirect(url_for("porta_altar_admin"))

    return render_template(
        "porta_altar_admin.html",
        igreja=igreja,
        videos=porta_altar.listar_videos(),
        perguntas=porta_altar.listar_perguntas(),
        edit_video=edit_video,
        edit_pergunta=edit_pergunta,
        tipos_video=porta_altar.TIPOS_VIDEO,
    )


@app.route("/porta-do-altar/admin/video/<int:video_id>/apagar", methods=["POST"])
@login_required
def porta_altar_apagar(video_id: int):
    if porta_altar.apagar_video(video_id):
        flash("Vídeo apagado.", "ok")
    else:
        flash("Vídeo não encontrado.", "erro")
    return redirect(url_for("porta_altar_admin"))


@app.route("/porta-do-altar/admin/video/<int:video_id>/desativar", methods=["POST"])
@login_required
def porta_altar_desativar(video_id: int):
    if porta_altar.desativar_video(video_id):
        flash("Vídeo desativado.", "ok")
    else:
        flash("Vídeo não encontrado.", "erro")
    return redirect(url_for("porta_altar_admin"))


@app.route("/porta-do-altar/admin/video/<int:video_id>/ativar", methods=["POST"])
@login_required
def porta_altar_ativar(video_id: int):
    if porta_altar.ativar_video(video_id):
        flash("Vídeo ativado.", "ok")
    else:
        flash("Vídeo não encontrado.", "erro")
    return redirect(url_for("porta_altar_admin"))


@app.route("/porta-do-altar/admin/pergunta/<int:pergunta_id>/apagar", methods=["POST"])
@login_required
def porta_altar_pergunta_apagar(pergunta_id: int):
    if porta_altar.apagar_pergunta(pergunta_id):
        flash("Pergunta apagada.", "ok")
    else:
        flash("Pergunta não encontrada.", "erro")
    return redirect(url_for("porta_altar_admin") + "#perguntas")


@app.route("/porta-do-altar/admin/pergunta/<int:pergunta_id>/desativar", methods=["POST"])
@login_required
def porta_altar_pergunta_desativar(pergunta_id: int):
    if porta_altar.desativar_pergunta(pergunta_id):
        flash("Pergunta desativada.", "ok")
    else:
        flash("Pergunta não encontrada.", "erro")
    return redirect(url_for("porta_altar_admin") + "#perguntas")


@app.route("/porta-do-altar/admin/pergunta/<int:pergunta_id>/ativar", methods=["POST"])
@login_required
def porta_altar_pergunta_ativar(pergunta_id: int):
    if porta_altar.ativar_pergunta(pergunta_id):
        flash("Pergunta ativada.", "ok")
    else:
        flash("Pergunta não encontrada.", "erro")
    return redirect(url_for("porta_altar_admin") + "#perguntas")


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
        next_url = request.args.get("next")
        return redirect(next_url or url_for("admin_galeria"))
    return render_template("admin_login.html", igreja=igreja, erro=erro)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_ok", None)
    return redirect(url_for("home"))


@app.route("/admin/galeria", methods=["GET", "POST"])
@login_required
def admin_galeria():
    igreja = load_json("igreja.json")
    cultos = load_json("cultos.json").get("cultos", [])

    if request.method == "POST":
        acao = request.form.get("acao", "galeria").strip()

        if acao == "lider_foto":
            perfil_id = request.form.get("perfil_id", "").strip()
            arquivo = request.files.get("foto")
            if not perfil_id:
                flash("Perfil inválido.", "erro")
                return redirect(url_for("admin_galeria") + "#lideres")
            if not arquivo or not arquivo.filename:
                flash("Envie a nova foto do líder.", "erro")
                return redirect(url_for("admin_galeria") + "#lideres")
            if not lideres_midia.extensao_ok(arquivo.filename):
                flash("Foto: use JPG, PNG, WEBP ou GIF.", "erro")
                return redirect(url_for("admin_galeria") + "#lideres")
            lideres_midia.init_db()
            nome_seguro = secure_filename(arquivo.filename)
            extensao = Path(nome_seguro).suffix.lower()
            nome_final = f"{perfil_id}_{uuid.uuid4().hex}{extensao}"
            arquivo.save(lideres_midia.UPLOAD_DIR / nome_final)
            if lideres_midia.atualizar_foto(perfil_id, nome_final):
                flash("Foto do líder atualizada.", "ok")
            else:
                flash("Não foi possível atualizar a foto.", "erro")
            return redirect(url_for("admin_galeria") + "#lideres")

        if acao == "lider_restaurar":
            perfil_id = request.form.get("perfil_id", "").strip()
            if lideres_midia.restaurar_padrao(perfil_id):
                flash("Foto restaurada para a imagem padrão.", "ok")
            else:
                flash("Perfil não encontrado.", "erro")
            return redirect(url_for("admin_galeria") + "#lideres")

        if acao == "aviso_home":
            texto = request.form.get("aviso_texto", "").strip()
            ativo = request.form.get("aviso_ativo") == "1"
            gallery.salvar_aviso_home(texto, ativo=ativo)
            if ativo and texto:
                flash("Aviso publicado na página inicial.", "ok")
            elif texto:
                flash("Aviso salvo (oculto na página inicial).", "ok")
            else:
                flash("Aviso da página inicial removido.", "ok")
            return redirect(url_for("admin_galeria") + "#aviso-home")

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
            flash("Postagem publicada! As fotos ficam no ar até você apagar no painel.", "ok")
            return redirect(url_for("admin_galeria"))

    posts = gallery.listar_posts_ativos()
    return render_template(
        "admin_galeria.html",
        igreja=igreja,
        cultos=cultos,
        posts=posts,
        perfis_lideres=lideres_midia.listar_perfis(),
        aviso_home=gallery.obter_aviso_home(),
    )


@app.route("/admin/galeria/<int:post_id>/apagar", methods=["POST"])
@login_required
def admin_apagar_post(post_id: int):
    if gallery.apagar_post(post_id):
        flash("Postagem apagada.", "ok")
    else:
        flash("Postagem não encontrada.", "erro")
    return redirect(url_for("admin_galeria"))


# ---------- Evento Batismo ----------

@app.route("/batismo/login", methods=["GET", "POST"])
def batismo_login():
    igreja = load_json("igreja.json")
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if check_password_hash(BATISMO_PASSWORD_HASH, senha):
            session["batismo_ok"] = True
            destino = request.args.get("next") or url_for("batismo_admin")
            return redirect(destino)
        erro = "Senha incorreta. Tente novamente."
    if session.get("batismo_ok"):
        return redirect(url_for("batismo_admin"))
    return render_template("batismo_login.html", igreja=igreja, erro=erro)


@app.route("/batismo/logout")
def batismo_logout():
    session.pop("batismo_ok", None)
    return redirect(url_for("eventos_page"))


def _processar_evento_responsavel(origem: str) -> bool:
    """Salva evento do responsável no calendário compartilhado. Retorna True se processou."""
    info = pastores.RESPONSAVEIS_EVENTO.get(origem)
    if not info:
        return False
    data_bruta = request.form.get("data", "").strip()
    data_iso = campanha_eventos.data_para_iso(data_bruta)
    if not data_iso:
        flash("Informe a data no formato dd/mm/aaaa (ex.: 14/08/2026).", "erro")
        return True
    evento_id = request.form.get("evento_id", type=int)
    titulo = request.form.get("titulo", "").strip() or info["titulo"]
    pastores.salvar_evento_lider(
        titulo=titulo,
        lider=info["lider"],
        origem=origem,
        data_iso=data_iso,
        horario=request.form.get("horario", ""),
        local=request.form.get("local", ""),
        descricao=request.form.get("descricao", ""),
        aviso=request.form.get("aviso", ""),
        evento_id=evento_id,
    )
    flash("Evento registrado no calendário dos líderes.", "ok")
    return True


@app.route("/batismo/admin", methods=["GET", "POST"])
@batismo_login_required
def batismo_admin():
    igreja = load_json("igreja.json")

    if request.method == "POST":
        acao = request.form.get("acao", "fotos").strip()
        if acao == "evento":
            _processar_evento_responsavel("batismo")
            return redirect(url_for("batismo_admin"))

        titulo = request.form.get("titulo", "").strip() or "Local do batismo"
        arquivos = request.files.getlist("fotos")
        salvos = []
        batismo.init_db()
        for arquivo in arquivos:
            if not arquivo or not arquivo.filename:
                continue
            if not batismo.extensao_ok(arquivo.filename):
                flash(f"Formato não permitido: {arquivo.filename}", "erro")
                continue
            nome_seguro = secure_filename(arquivo.filename)
            extensao = Path(nome_seguro).suffix.lower()
            nome_final = f"{uuid.uuid4().hex}{extensao}"
            destino = batismo.UPLOAD_DIR / nome_final
            arquivo.save(destino)
            salvos.append(nome_final)

        if not salvos:
            flash("Envie ao menos uma foto válida (JPG, PNG, WEBP ou GIF).", "erro")
        else:
            batismo.adicionar_fotos(salvos, titulo)
            flash("Fotos do sítio publicadas! Elas aparecem na página inicial.", "ok")
            return redirect(url_for("batismo_admin"))

    editar_evento = None
    if request.args.get("editar_evento"):
        editar_evento = pastores.obter_evento_lider(
            request.args.get("editar_evento", type=int),
            origem="batismo",
        )

    return render_template(
        "batismo_admin.html",
        igreja=igreja,
        fotos=batismo.listar_fotos(),
        inscricoes=batismo.listar_inscricoes(),
        status_opcoes=batismo.STATUS_OPCOES,
        eventos_calendario=pastores.listar_eventos_lideres(origem="batismo"),
        editar_evento=editar_evento,
        info_evento=pastores.RESPONSAVEIS_EVENTO["batismo"],
    )


@app.route("/batismo/admin/foto/<int:foto_id>/apagar", methods=["POST"])
@batismo_login_required
def batismo_apagar_foto(foto_id: int):
    if batismo.apagar_foto(foto_id):
        flash("Foto apagada.", "ok")
    else:
        flash("Foto não encontrada.", "erro")
    return redirect(url_for("batismo_admin"))


@app.route("/batismo/admin/inscricao/<int:inscricao_id>/status", methods=["POST"])
@batismo_login_required
def batismo_atualizar_status(inscricao_id: int):
    status = request.form.get("status", "").strip()
    if batismo.atualizar_status(inscricao_id, status):
        flash("Status atualizado.", "ok")
    else:
        flash("Não foi possível atualizar o status.", "erro")
    return redirect(url_for("batismo_admin"))


@app.route("/batismo/admin/evento/<int:evento_id>/apagar", methods=["POST"])
@batismo_login_required
def batismo_apagar_evento(evento_id: int):
    if pastores.apagar_evento_lider(evento_id, origem="batismo"):
        flash("Evento removido do calendário.", "ok")
    else:
        flash("Evento não encontrado.", "erro")
    return redirect(url_for("batismo_admin"))


@app.route("/batismo/admin/inscricao/<int:inscricao_id>/apagar", methods=["POST"])
@batismo_login_required
def batismo_apagar_inscricao(inscricao_id: int):
    if batismo.apagar_inscricao(inscricao_id):
        flash("Família removida da lista de batismo.", "ok")
    else:
        flash("Inscrição não encontrada.", "erro")
    return redirect(url_for("batismo_admin"))


@app.route("/batismo/inscricao", methods=["GET", "POST"])
def batismo_inscricao():
    igreja = load_json("igreja.json")
    fotos = batismo.listar_fotos()
    erro = None

    if request.method == "POST":
        nomes_pessoas = request.form.getlist("pessoas")
        docs_pessoas = request.form.getlist("pessoas_doc")
        sexos_pessoas = request.form.getlist("pessoas_sexo")
        pessoas = []
        for i, nome in enumerate(nomes_pessoas):
            nome_limpo = (nome or "").strip()
            if not nome_limpo:
                continue
            doc = docs_pessoas[i].strip() if i < len(docs_pessoas) else ""
            sexo = sexos_pessoas[i].strip() if i < len(sexos_pessoas) else ""
            pessoas.append({"nome": nome_limpo, "documento": doc, "sexo": sexo})

        telefone = request.form.get("telefone", "").strip()
        status = request.form.get("status", "analise").strip()

        if not pessoas:
            nome_completo = "Família"
        elif len(pessoas) == 1:
            nome_completo = pessoas[0]["nome"]
        elif len(pessoas) == 2:
            nome_completo = f"{pessoas[0]['nome']} & {pessoas[1]['nome']}"
        else:
            nome_completo = f"{pessoas[0]['nome']} e +{len(pessoas) - 1}"

        if not pessoas:
            erro = "Adicione ao menos uma pessoa da família."
        elif not telefone:
            erro = "Informe o telefone de contato."
        elif status not in batismo.STATUS_OPCOES:
            erro = "Selecione uma confirmação válida."
        else:
            inscricao_id = batismo.criar_inscricao(
                nome_completo=nome_completo,
                nome_marido="",
                nome_mulher="",
                filhos=pessoas,
                rg_marido="",
                rg_mulher="",
                sexo_marido="",
                sexo_mulher="",
                telefone=telefone,
                participantes=["familia"],
                status=status,
            )
            return redirect(url_for("batismo_confirmacao", inscricao_id=inscricao_id))

    return render_template(
        "batismo_inscricao.html",
        igreja=igreja,
        fotos=fotos,
        erro=erro,
        status_opcoes=batismo.STATUS_OPCOES,
    )


@app.route("/batismo/confirmacao/<int:inscricao_id>")
def batismo_confirmacao(inscricao_id: int):
    igreja = load_json("igreja.json")
    inscricao = batismo.obter_inscricao(inscricao_id)
    if not inscricao:
        flash("Inscrição não encontrada.", "erro")
        return redirect(url_for("batismo_inscricao"))
    return render_template(
        "batismo_confirmacao.html",
        igreja=igreja,
        inscricao=inscricao,
    )


@app.route("/batismo/admin/exportar.xlsx")
@batismo_login_required
def batismo_exportar_excel():
    from openpyxl import Workbook

    inscricoes = batismo.listar_inscricoes()
    wb = Workbook()
    ws = wb.active
    ws.title = "Inscricoes Batismo"
    ws.append(
        [
            "ID",
            "Família",
            "Pessoas",
            "Telefone",
            "Participantes",
            "Status",
            "Enviado em",
        ]
    )
    for item in inscricoes:
        pessoas = item.get("pessoas_texto") or item.get("filhos_texto") or ""
        legado = []
        if item.get("nome_marido"):
            legado.append(item["nome_marido"])
        if item.get("nome_mulher"):
            legado.append(item["nome_mulher"])
        if legado and pessoas:
            pessoas = ", ".join(legado) + " | " + pessoas
        elif legado:
            pessoas = ", ".join(legado)
        ws.append(
            [
                item["id"],
                item.get("nome_completo") or "",
                pessoas,
                item["telefone"],
                item["participantes_texto"],
                item["status_texto"],
                item["criado_em"].replace("T", " "),
            ]
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="inscricoes-batismo.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/batismo/admin/exportar.pdf")
@batismo_login_required
def batismo_exportar_pdf():
    from fpdf import FPDF

    inscricoes = batismo.listar_inscricoes()
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Inscricoes - Evento Batismo CEASDREI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0,
        8,
        "Responsavel: Evangelista Sueli",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)

    colunas = [
        ("ID", 12),
        ("Familia", 50),
        ("Pessoas", 90),
        ("Telefone", 35),
        ("Status", 40),
    ]
    pdf.set_font("Helvetica", "B", 8)
    for titulo, largura in colunas:
        pdf.cell(largura, 8, titulo, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    for item in inscricoes:
        pessoas = item.get("pessoas_texto") or item.get("filhos_texto") or ""
        valores = [
            str(item["id"]),
            (item.get("nome_completo") or "")[:45],
            pessoas[:80],
            item["telefone"][:22],
            item["status_texto"][:28],
        ]
        for valor, (_, largura) in zip(valores, colunas):
            pdf.cell(largura, 7, valor, border=1)
        pdf.ln()

    if not inscricoes:
        pdf.cell(0, 10, "Nenhuma inscricao registrada.", new_x="LMARGIN", new_y="NEXT")

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="inscricoes-batismo.pdf",
        mimetype="application/pdf",
    )


# ---------- Encontro de Casais ----------

@app.route("/casais/login", methods=["GET", "POST"])
def casais_login():
    igreja = load_json("igreja.json")
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if check_password_hash(CASAIS_PASSWORD_HASH, senha):
            session["casais_ok"] = True
            destino = request.args.get("next") or url_for("casais_admin")
            return redirect(destino)
        erro = "Senha incorreta. Tente novamente."
    if session.get("casais_ok"):
        return redirect(url_for("casais_admin"))
    return render_template("casais_login.html", igreja=igreja, erro=erro)


@app.route("/casais/logout")
def casais_logout():
    session.pop("casais_ok", None)
    return redirect(url_for("eventos_page"))


@app.route("/casais/admin", methods=["GET", "POST"])
@casais_login_required
def casais_admin():
    igreja = load_json("igreja.json")

    if request.method == "POST":
        acao = request.form.get("acao", "fotos").strip()

        if acao == "programacao":
            casais.salvar_programacao(request.form.get("programacao", ""))
            flash("Programação do encontro atualizada.", "ok")
            return redirect(url_for("casais_admin"))

        if acao == "evento":
            _processar_evento_responsavel("casais")
            return redirect(url_for("casais_admin"))

        titulo = request.form.get("titulo", "").strip() or "Encontro de Casais"
        arquivos = request.files.getlist("fotos")
        salvos = []
        casais.init_db()
        for arquivo in arquivos:
            if not arquivo or not arquivo.filename:
                continue
            if not casais.extensao_ok(arquivo.filename):
                flash(f"Formato não permitido: {arquivo.filename}", "erro")
                continue
            nome_seguro = secure_filename(arquivo.filename)
            extensao = Path(nome_seguro).suffix.lower()
            nome_final = f"{uuid.uuid4().hex}{extensao}"
            destino = casais.UPLOAD_DIR / nome_final
            arquivo.save(destino)
            salvos.append(nome_final)

        if not salvos:
            flash("Envie ao menos uma foto válida (JPG, PNG, WEBP ou GIF).", "erro")
        else:
            casais.adicionar_fotos(salvos, titulo)
            flash("Fotos publicadas! Elas aparecem na página do encontro e no início.", "ok")
            return redirect(url_for("casais_admin"))

    editar_evento = None
    if request.args.get("editar_evento"):
        editar_evento = pastores.obter_evento_lider(
            request.args.get("editar_evento", type=int),
            origem="casais",
        )

    return render_template(
        "casais_admin.html",
        igreja=igreja,
        fotos=casais.listar_fotos(),
        inscricoes=casais.listar_inscricoes(),
        programacao=casais.obter_programacao(),
        status_opcoes=casais.STATUS_OPCOES,
        h1_responsaveis=casais.H1_RESPONSAVEIS,
        eventos_calendario=pastores.listar_eventos_lideres(origem="casais"),
        editar_evento=editar_evento,
        info_evento=pastores.RESPONSAVEIS_EVENTO["casais"],
    )


@app.route("/casais/admin/foto/<int:foto_id>/apagar", methods=["POST"])
@casais_login_required
def casais_apagar_foto(foto_id: int):
    if casais.apagar_foto(foto_id):
        flash("Foto apagada.", "ok")
    else:
        flash("Foto não encontrada.", "erro")
    return redirect(url_for("casais_admin"))


@app.route("/casais/admin/inscricao/<int:inscricao_id>/status", methods=["POST"])
@casais_login_required
def casais_atualizar_status(inscricao_id: int):
    status = request.form.get("status", "").strip()
    if casais.atualizar_status(inscricao_id, status):
        flash("Status atualizado.", "ok")
    else:
        flash("Não foi possível atualizar o status.", "erro")
    return redirect(url_for("casais_admin"))


@app.route("/casais/admin/evento/<int:evento_id>/apagar", methods=["POST"])
@casais_login_required
def casais_apagar_evento(evento_id: int):
    if pastores.apagar_evento_lider(evento_id, origem="casais"):
        flash("Evento removido do calendário.", "ok")
    else:
        flash("Evento não encontrado.", "erro")
    return redirect(url_for("casais_admin"))


@app.route("/casais")
def casais_page():
    igreja = load_json("igreja.json")
    return render_template(
        "casais.html",
        igreja=igreja,
        fotos=casais.listar_fotos(),
        programacao=casais.obter_programacao(),
        h1_responsaveis=casais.H1_RESPONSAVEIS,
    )


@app.route("/casais/inscricao", methods=["GET", "POST"])
def casais_inscricao():
    igreja = load_json("igreja.json")
    erro = None

    if request.method == "POST":
        nome_marido = request.form.get("nome_marido", "").strip()
        telefone_marido = request.form.get("telefone_marido", "").strip()
        nome_mulher = request.form.get("nome_mulher", "").strip()
        telefone_mulher = request.form.get("telefone_mulher", "").strip()
        status = request.form.get("status", "analise").strip()

        if not nome_marido or not nome_mulher:
            erro = "Informe o nome do marido e da mulher."
        elif not telefone_marido and not telefone_mulher:
            erro = "Informe ao menos um telefone de contato."
        elif status not in casais.STATUS_OPCOES:
            erro = "Selecione uma confirmação válida."
        else:
            inscricao_id = casais.criar_inscricao(
                nome_marido=nome_marido,
                telefone_marido=telefone_marido,
                nome_mulher=nome_mulher,
                telefone_mulher=telefone_mulher,
                status=status,
            )
            return redirect(url_for("casais_confirmacao", inscricao_id=inscricao_id))

    return render_template(
        "casais_inscricao.html",
        igreja=igreja,
        fotos=casais.listar_fotos(),
        programacao=casais.obter_programacao(),
        erro=erro,
        status_opcoes=casais.STATUS_OPCOES,
        h1_responsaveis=casais.H1_RESPONSAVEIS,
    )


@app.route("/casais/confirmacao/<int:inscricao_id>")
def casais_confirmacao(inscricao_id: int):
    igreja = load_json("igreja.json")
    inscricao = casais.obter_inscricao(inscricao_id)
    if not inscricao:
        flash("Inscrição não encontrada.", "erro")
        return redirect(url_for("casais_inscricao"))
    return render_template(
        "casais_confirmacao.html",
        igreja=igreja,
        inscricao=inscricao,
        h1_responsaveis=casais.H1_RESPONSAVEIS,
    )


@app.route("/casais/admin/exportar.xlsx")
@casais_login_required
def casais_exportar_excel():
    from openpyxl import Workbook

    inscricoes = casais.listar_inscricoes()
    wb = Workbook()
    ws = wb.active
    ws.title = "Encontro Casais"
    ws.append(
        [
            "ID",
            "Marido",
            "Telefone marido",
            "Mulher",
            "Telefone mulher",
            "Status",
            "Enviado em",
        ]
    )
    for item in inscricoes:
        ws.append(
            [
                item["id"],
                item["nome_marido"],
                item["telefone_marido"],
                item["nome_mulher"],
                item["telefone_mulher"],
                item["status_texto"],
                item["criado_em"].replace("T", " "),
            ]
        )

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="inscricoes-encontro-casais.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/casais/admin/exportar.pdf")
@casais_login_required
def casais_exportar_pdf():
    from fpdf import FPDF

    inscricoes = casais.listar_inscricoes()
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Inscricoes - Encontro de Casais CEASDREI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0,
        8,
        "Responsaveis: Diac. Robson e Diac. Luana",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)

    colunas = [
        ("ID", 12),
        ("Marido", 50),
        ("Tel. marido", 35),
        ("Mulher", 50),
        ("Tel. mulher", 35),
        ("Status", 40),
        ("Enviado em", 40),
    ]
    pdf.set_font("Helvetica", "B", 8)
    for titulo, largura in colunas:
        pdf.cell(largura, 8, titulo, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    for item in inscricoes:
        valores = [
            str(item["id"]),
            item["nome_marido"][:40],
            item["telefone_marido"][:24],
            item["nome_mulher"][:40],
            item["telefone_mulher"][:24],
            item["status_texto"][:30],
            item["criado_em"].replace("T", " ")[:22],
        ]
        for valor, (_, largura) in zip(valores, colunas):
            pdf.cell(largura, 7, valor, border=1)
        pdf.ln()

    if not inscricoes:
        pdf.cell(0, 10, "Nenhuma inscricao registrada.", new_x="LMARGIN", new_y="NEXT")

    buffer = io.BytesIO(pdf.output())
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="inscricoes-encontro-casais.pdf",
        mimetype="application/pdf",
    )


# ---------- Pastores / Obreiros / Calendário ----------

@app.route("/pastores/login", methods=["GET", "POST"])
def pastores_login():
    igreja = load_json("igreja.json")
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if check_password_hash(PASTORES_PASSWORD_HASH, senha):
            session["pastores_ok"] = True
            destino = request.args.get("next") or url_for("pastores_admin")
            return redirect(destino)
        erro = "Senha incorreta. Tente novamente."
    if session.get("pastores_ok"):
        return redirect(url_for("pastores_admin"))
    return render_template("pastores_login.html", igreja=igreja, erro=erro)


@app.route("/pastores/logout")
def pastores_logout():
    session.pop("pastores_ok", None)
    return redirect(url_for("eventos_page"))


@app.route("/pastores/admin", methods=["GET", "POST"])
@pastores_login_required
def pastores_admin():
    igreja = load_json("igreja.json")
    hoje = pastores.hoje()
    ano = int(request.args.get("ano", hoje.year))
    mes = int(request.args.get("mes", hoje.month))
    if mes < 1 or mes > 12:
        mes = hoje.month

    if request.method == "POST":
        acao = request.form.get("acao", "").strip()

        if acao == "escala":
            data_iso = request.form.get("data", "").strip()
            if not data_iso:
                flash("Informe a data da escala.", "erro")
            else:
                escala_id = request.form.get("escala_id", type=int)
                pastores.salvar_escala(
                    data_iso=data_iso,
                    porta_vidro=pastores.juntar_obreiros(
                        *request.form.getlist("porta_vidro")
                    ),
                    abertura=pastores.juntar_obreiros(*request.form.getlist("abertura")),
                    porta_escada=pastores.juntar_obreiros(
                        *request.form.getlist("porta_escada")
                    ),
                    escala_id=escala_id,
                )
                flash("Escala de obreiros salva.", "ok")
            return redirect(url_for("pastores_admin", ano=ano, mes=mes, aba="escala"))

        if acao == "adicionar_obreiro":
            ok, mensagem = pastores.adicionar_obreiro(
                request.form.get("novo_obreiro", "")
            )
            flash(mensagem, "ok" if ok else "erro")
            return redirect(url_for("pastores_admin", ano=ano, mes=mes, aba="escala"))

        if acao == "remover_obreiro":
            obreiro_id = request.form.get("obreiro_id", type=int)
            if obreiro_id and pastores.remover_obreiro(obreiro_id):
                flash("Obreiro removido da lista.", "ok")
            else:
                flash("Não foi possível remover o obreiro.", "erro")
            return redirect(url_for("pastores_admin", ano=ano, mes=mes, aba="escala"))

        if acao == "destaque":
            pregador_nome = request.form.get("pregador_nome", "").strip()
            arquivo = request.files.get("pregador_foto")
            foto_nome = ""
            if pregador_nome:
                if arquivo and arquivo.filename:
                    if not pastores.extensao_ok(arquivo.filename):
                        flash("Foto do pregador: use JPG, PNG, WEBP ou GIF.", "erro")
                        return redirect(url_for("pastores_admin", aba="destaque"))
                    nome_seguro = secure_filename(arquivo.filename)
                    extensao = Path(nome_seguro).suffix.lower()
                    foto_nome = f"pregador-{uuid.uuid4().hex}{extensao}"
                    arquivo.save(pastores.UPLOAD_DIR / foto_nome)
                elif not pastores.obter_destaque().get("pregador_foto"):
                    flash("Ao informar o pregador, envie também a foto.", "erro")
                    return redirect(url_for("pastores_admin", aba="destaque"))

            pastores.salvar_destaque(
                data_iso=request.form.get("data", "").strip(),
                porta=request.form.get("porta", ""),
                abertura_culto=request.form.get("abertura_culto", ""),
                pregador_nome=pregador_nome,
                pregador_foto=foto_nome,
                mensagem_campanha=request.form.get("mensagem_campanha", ""),
                referencia=request.form.get("referencia", ""),
                manter_foto=True,
            )
            flash("Destaque do culto atualizado.", "ok")
            return redirect(url_for("pastores_admin", aba="destaque"))

    editar_escala = None
    if request.args.get("editar_escala"):
        for item in pastores.listar_escala(ano, mes):
            if item["id"] == request.args.get("editar_escala", type=int):
                editar_escala = item
                break

    selecionados_abertura = (
        pastores.partir_obreiros(editar_escala.get("abertura", ""))
        if editar_escala
        else []
    )
    selecionados_porta_vidro = (
        pastores.partir_obreiros(editar_escala.get("porta_vidro", ""))
        if editar_escala
        else []
    )
    selecionados_porta_escada = (
        pastores.partir_obreiros(editar_escala.get("porta_escada", ""))
        if editar_escala
        else []
    )

    return render_template(
        "pastores_admin.html",
        igreja=igreja,
        h1_pastores=pastores.H1_PASTORES,
        escala=pastores.listar_escala(ano, mes),
        destaque=pastores.obter_destaque(),
        eventos=pastores.listar_eventos_lideres(incluir_passados=True),
        calendario=pastores.calendario_mes(ano, mes),
        avisos=pastores.avisos_proximos(7),
        editar_escala=editar_escala,
        obreiros=pastores.listar_obreiros(),
        selecionados_abertura=selecionados_abertura,
        selecionados_porta_vidro=selecionados_porta_vidro,
        selecionados_porta_escada=selecionados_porta_escada,
        ano=ano,
        mes=mes,
        aba=request.args.get("aba", "escala"),
    )


@app.route("/pastores/admin/escala/<int:escala_id>/apagar", methods=["POST"])
@pastores_login_required
def pastores_apagar_escala(escala_id: int):
    if pastores.apagar_escala(escala_id):
        flash("Dia removido da escala.", "ok")
    else:
        flash("Registro não encontrado.", "erro")
    return redirect(url_for("pastores_admin", aba="escala"))


@app.route("/pastores/admin/evento/<int:evento_id>/apagar", methods=["POST"])
@pastores_login_required
def pastores_apagar_evento(evento_id: int):
    if pastores.apagar_evento_lider(evento_id):
        flash("Evento removido do calendário.", "ok")
    else:
        flash("Evento não encontrado.", "erro")
    return redirect(url_for("pastores_admin", aba="calendario"))


@app.route("/comunicado")
def comunicado_obreiros():
    igreja = load_json("igreja.json")
    hoje = pastores.hoje()
    ano = int(request.args.get("ano", hoje.year))
    mes = int(request.args.get("mes", hoje.month))
    escala = pastores.listar_escala(ano, mes)
    escala_destaque = pastores.obter_proxima_escala()
    calendario = pastores.calendario_mes(ano, mes)
    nome_igreja = igreja.get("nome") or "IGREJA CEASDREI"
    link = url_for("comunicado_obreiros", ano=ano, mes=mes, _external=True)
    whatsapp_dia = ""
    if escala_destaque:
        whatsapp_dia = pastores.url_whatsapp(
            pastores.texto_whatsapp_dia(escala_destaque, nome_igreja, link)
        )
    whatsapp_mes = pastores.url_whatsapp(
        pastores.texto_whatsapp_mes(
            escala,
            calendario["nome_mes"],
            ano,
            nome_igreja,
            link,
        )
    )
    return render_template(
        "comunicado.html",
        igreja=igreja,
        escala=escala,
        escala_destaque=escala_destaque,
        destaque=pastores.obter_destaque(),
        avisos=pastores.avisos_proximos(7),
        calendario=calendario,
        ano=ano,
        mes=mes,
        whatsapp_dia=whatsapp_dia,
        whatsapp_mes=whatsapp_mes,
    )


@app.route("/calendario-lideres")
def calendario_lideres():
    igreja = load_json("igreja.json")
    hoje = pastores.hoje()
    ano = int(request.args.get("ano", hoje.year))
    mes = int(request.args.get("mes", hoje.month))
    return render_template(
        "calendario_lideres.html",
        igreja=igreja,
        calendario=pastores.calendario_mes(ano, mes),
        eventos=pastores.listar_eventos_lideres(incluir_passados=True),
        avisos=pastores.avisos_proximos(14),
        ano=ano,
        mes=mes,
    )


# ---------- Arraiá Gospel / Cantina (Diac. Cássia) ----------

@app.route("/arraial/login", methods=["GET", "POST"])
def arraial_login():
    igreja = load_json("igreja.json")
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if check_password_hash(ARRAIAL_PASSWORD_HASH, senha):
            session["arraial_ok"] = True
            destino = request.args.get("next") or url_for("arraial_admin")
            return redirect(destino)
        erro = "Senha incorreta. Tente novamente."
    if session.get("arraial_ok"):
        return redirect(url_for("arraial_admin"))
    info = arraial.info_evento()
    return render_template(
        "arraial_login.html",
        igreja=igreja,
        erro=erro,
        h1_responsavel=info["h1"],
        info=info,
    )


@app.route("/arraial/logout")
def arraial_logout():
    session.pop("arraial_ok", None)
    return redirect(url_for("eventos_page"))


@app.route("/arraial/admin", methods=["GET", "POST"])
@arraial_login_required
def arraial_admin():
    igreja = load_json("igreja.json")

    if request.method == "POST":
        acao = request.form.get("acao", "cantina").strip()
        if acao == "evento":
            _processar_evento_responsavel("arraial")
            return redirect(url_for("arraial_admin"))

        if acao == "convite":
            flyer_nome = None
            arquivo = request.files.get("flyer")
            if arquivo and arquivo.filename:
                ext = Path(arquivo.filename).suffix.lower()
                if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                    flash("Flyer: use JPG, PNG, WEBP ou GIF.", "erro")
                    return redirect(url_for("arraial_admin"))
                nome_seguro = secure_filename(arquivo.filename)
                ext = Path(nome_seguro).suffix.lower() or ext
                flyer_nome = f"flyer-{uuid.uuid4().hex}{ext}"
                arquivo.save(arraial.UPLOAD_DIR / flyer_nome)

            arraial.salvar_convite(
                h1=request.form.get("h1", ""),
                convite=request.form.get("convite", ""),
                data_iso=request.form.get("data", ""),
                horario=request.form.get("horario", ""),
                local=request.form.get("local", ""),
                adulto=request.form.get("adulto", ""),
                crianca=request.form.get("crianca", ""),
                pedido=request.form.get("pedido", ""),
                flyer_arquivo=flyer_nome,
            )
            flash("Convite do Arraiá atualizado (textos e imagem).", "ok")
            return redirect(url_for("arraial_admin"))

        arraial.salvar_cantina(request.form.get("cantina", ""))
        flash("Cardápio / avisos da cantina atualizados.", "ok")
        return redirect(url_for("arraial_admin"))

    editar_evento = None
    if request.args.get("editar_evento"):
        editar_evento = pastores.obter_evento_lider(
            request.args.get("editar_evento", type=int),
            origem="arraial",
        )

    info = arraial.info_evento()
    return render_template(
        "arraial_admin.html",
        igreja=igreja,
        h1_responsavel=info["h1"],
        cantina=arraial.obter_cantina(),
        info=info,
        eventos_calendario=pastores.listar_eventos_lideres(origem="arraial"),
        editar_evento=editar_evento,
        info_evento=pastores.RESPONSAVEIS_EVENTO["arraial"],
    )


@app.route("/arraial/admin/evento/<int:evento_id>/apagar", methods=["POST"])
@arraial_login_required
def arraial_apagar_evento(evento_id: int):
    if pastores.apagar_evento_lider(evento_id, origem="arraial"):
        flash("Evento removido do calendário.", "ok")
    else:
        flash("Evento não encontrado.", "erro")
    return redirect(url_for("arraial_admin"))


@app.route("/arraial")
def arraial_page():
    igreja = load_json("igreja.json")
    info = arraial.info_evento()
    return render_template(
        "arraial.html",
        igreja=igreja,
        h1_responsavel=info["h1"],
        info=info,
        cantina=arraial.obter_cantina(),
    )


# ---------- Filhos do Rei (mocidade) ----------

@app.route("/mocidade/login", methods=["GET", "POST"])
def mocidade_login():
    igreja = load_json("igreja.json")
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if check_password_hash(MOCIDADE_PASSWORD_HASH, senha):
            session["mocidade_ok"] = True
            destino = request.args.get("next") or url_for("mocidade_admin")
            return redirect(destino)
        erro = "Senha incorreta. Tente novamente."
    if session.get("mocidade_ok"):
        return redirect(url_for("mocidade_admin"))
    return render_template(
        "mocidade_login.html",
        igreja=igreja,
        erro=erro,
        h1_responsaveis=mocidade.H1_RESPONSAVEIS,
        foto_lideres=mocidade.FOTO_LIDERES,
    )


@app.route("/mocidade/logout")
def mocidade_logout():
    session.pop("mocidade_ok", None)
    return redirect(url_for("eventos_page"))


@app.route("/mocidade/admin", methods=["GET", "POST"])
@mocidade_login_required
def mocidade_admin():
    igreja = load_json("igreja.json")

    if request.method == "POST":
        acao = request.form.get("acao", "post").strip()
        if acao == "evento":
            _processar_evento_responsavel("mocidade")
            return redirect(url_for("mocidade_admin"))

        if acao == "destaque":
            data_iso = request.form.get("data", "").strip()
            mensagem = request.form.get("mensagem", "").strip()
            arquivo = request.files.get("imagem")
            nome_final = ""
            if arquivo and arquivo.filename:
                if not mocidade.extensao_ok(arquivo.filename):
                    flash("Imagem: use JPG, PNG, WEBP ou GIF.", "erro")
                    return redirect(url_for("mocidade_admin"))
                nome_seguro = secure_filename(arquivo.filename)
                extensao = Path(nome_seguro).suffix.lower()
                nome_final = f"destaque-{uuid.uuid4().hex}{extensao}"
                mocidade.init_db()
                arquivo.save(mocidade.UPLOAD_DIR / nome_final)
            mocidade.salvar_destaque(
                data_iso=data_iso,
                mensagem=mensagem,
                imagem=nome_final,
            )
            flash("Destaque salvo! Aparece na home 7 dias antes da data.", "ok")
            return redirect(url_for("mocidade_admin"))

        if acao == "limpar_destaque":
            mocidade.limpar_destaque()
            flash("Destaque limpo.", "ok")
            return redirect(url_for("mocidade_admin"))

        titulo = request.form.get("titulo", "").strip() or "Culto dos jovens"
        texto = request.form.get("texto", "").strip()
        arquivo = request.files.get("foto")
        if not texto:
            flash("Escreva a mensagem do post.", "erro")
            return redirect(url_for("mocidade_admin"))
        if not arquivo or not arquivo.filename:
            flash("Envie uma foto para o post.", "erro")
            return redirect(url_for("mocidade_admin"))
        if not mocidade.extensao_ok(arquivo.filename):
            flash("Foto: use JPG, PNG, WEBP ou GIF.", "erro")
            return redirect(url_for("mocidade_admin"))

        nome_seguro = secure_filename(arquivo.filename)
        extensao = Path(nome_seguro).suffix.lower()
        nome_final = f"{uuid.uuid4().hex}{extensao}"
        arquivo.save(mocidade.UPLOAD_DIR / nome_final)
        mocidade.criar_post(titulo=titulo, texto=texto, foto=nome_final)
        flash("Post publicado na página inicial!", "ok")
        return redirect(url_for("mocidade_admin"))

    editar_evento = None
    if request.args.get("editar_evento"):
        editar_evento = pastores.obter_evento_lider(
            request.args.get("editar_evento", type=int),
            origem="mocidade",
        )

    return render_template(
        "mocidade_admin.html",
        igreja=igreja,
        h1_responsaveis=mocidade.H1_RESPONSAVEIS,
        foto_lideres=mocidade.FOTO_LIDERES,
        posts=mocidade.listar_posts(),
        post_ativo=mocidade.obter_post_ativo(),
        destaque=mocidade.obter_destaque(),
        eventos_calendario=pastores.listar_eventos_lideres(origem="mocidade"),
        editar_evento=editar_evento,
        info_evento=pastores.RESPONSAVEIS_EVENTO["mocidade"],
    )


@app.route("/mocidade/admin/destaque/apagar-imagem", methods=["POST"])
@mocidade_login_required
def mocidade_apagar_imagem_destaque():
    if mocidade.apagar_imagem_destaque():
        flash("Imagem do destaque apagada.", "ok")
    else:
        flash("Nenhuma imagem para apagar.", "erro")
    return redirect(url_for("mocidade_admin"))


@app.route("/mocidade/admin/post/<int:post_id>/apagar", methods=["POST"])
@mocidade_login_required
def mocidade_apagar_post(post_id: int):
    if mocidade.apagar_post(post_id):
        flash("Post apagado.", "ok")
    else:
        flash("Post não encontrado.", "erro")
    return redirect(url_for("mocidade_admin"))


@app.route("/mocidade/admin/post/<int:post_id>/desativar", methods=["POST"])
@mocidade_login_required
def mocidade_desativar_post(post_id: int):
    if mocidade.desativar_post(post_id):
        flash("Post removido da página inicial.", "ok")
    else:
        flash("Post não encontrado.", "erro")
    return redirect(url_for("mocidade_admin"))


@app.route("/mocidade/admin/evento/<int:evento_id>/apagar", methods=["POST"])
@mocidade_login_required
def mocidade_apagar_evento(evento_id: int):
    if pastores.apagar_evento_lider(evento_id, origem="mocidade"):
        flash("Evento removido do calendário.", "ok")
    else:
        flash("Evento não encontrado.", "erro")
    return redirect(url_for("mocidade_admin"))


@app.route("/mocidade")
def mocidade_page():
    igreja = load_json("igreja.json")
    return render_template(
        "mocidade.html",
        igreja=igreja,
        h1_responsaveis=mocidade.H1_RESPONSAVEIS,
        foto_lideres=mocidade.FOTO_LIDERES,
        post_ativo=mocidade.obter_post_ativo(),
        destaque_publico=mocidade.obter_destaque_publico(),
    )


# ---------- Leoas / Leão / Maranata / Soldadinhos de Cristo ----------

@app.route("/evento/<slug>/login", methods=["GET", "POST"])
def campanha_login(slug: str):
    if slug not in CAMPANHA_PASSWORD_HASH:
        return redirect(url_for("eventos_page"))
    igreja = load_json("igreja.json")
    info = campanha_eventos.config(slug)
    erro = None
    chave = CAMPANHA_SESSION_KEY[slug]
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if check_password_hash(CAMPANHA_PASSWORD_HASH[slug], senha):
            session[chave] = True
            destino = request.args.get("next") or url_for("campanha_admin", slug=slug)
            return redirect(destino)
        erro = "Senha incorreta. Tente novamente."
    if session.get(chave):
        return redirect(url_for("campanha_admin", slug=slug))
    return render_template(
        "campanha_login.html",
        igreja=igreja,
        erro=erro,
        slug=slug,
        info=info,
    )


@app.route("/evento/<slug>/logout")
def campanha_logout(slug: str):
    chave = CAMPANHA_SESSION_KEY.get(slug)
    if chave:
        session.pop(chave, None)
    return redirect(url_for("eventos_page"))


@app.route("/evento/<slug>/admin", methods=["GET", "POST"])
@campanha_login_required
def campanha_admin(slug: str):
    igreja = load_json("igreja.json")
    info = campanha_eventos.config(slug)

    if request.method == "POST":
        acao = request.form.get("acao", "post").strip()
        if acao == "evento":
            _processar_evento_responsavel(slug)
            return redirect(url_for("campanha_admin", slug=slug))

        if acao == "destaque":
            data_bruta = request.form.get("data", "").strip()
            data_iso = ""
            if data_bruta:
                data_iso = campanha_eventos.data_para_iso(data_bruta)
                if not data_iso:
                    flash("Data inválida. Use dd/mm/aaaa (ex.: 14/08/2026).", "erro")
                    return redirect(url_for("campanha_admin", slug=slug))
            mensagem = request.form.get("mensagem", "").strip()
            arquivo = request.files.get("imagem")
            nome_final = ""
            if arquivo and arquivo.filename:
                if not campanha_eventos.extensao_ok(arquivo.filename):
                    flash("Imagem: use JPG, PNG, WEBP ou GIF.", "erro")
                    return redirect(url_for("campanha_admin", slug=slug))
                nome_seguro = secure_filename(arquivo.filename)
                extensao = Path(nome_seguro).suffix.lower()
                nome_final = f"destaque-{uuid.uuid4().hex}{extensao}"
                campanha_eventos.init_db(slug)
                arquivo.save(info["upload_dir"] / nome_final)
            campanha_eventos.salvar_destaque(
                slug,
                data_iso=data_iso,
                mensagem=mensagem,
                imagem=nome_final,
            )
            flash("Destaque salvo! Aparece na home 7 dias antes da data.", "ok")
            return redirect(url_for("campanha_admin", slug=slug))

        if acao == "limpar_destaque":
            campanha_eventos.limpar_destaque(slug)
            flash("Destaque limpo.", "ok")
            return redirect(url_for("campanha_admin", slug=slug))

        titulo = request.form.get("titulo", "").strip() or info["titulo"]
        texto = request.form.get("texto", "").strip()
        tipo = request.form.get("tipo", "culto_normal").strip()
        arquivo = request.files.get("foto")
        if not texto:
            flash("Escreva a mensagem da campanha.", "erro")
            return redirect(url_for("campanha_admin", slug=slug))

        nome_final = ""
        if arquivo and arquivo.filename:
            if not campanha_eventos.extensao_ok(arquivo.filename):
                flash("Foto: use JPG, PNG, WEBP ou GIF.", "erro")
                return redirect(url_for("campanha_admin", slug=slug))
            nome_seguro = secure_filename(arquivo.filename)
            extensao = Path(nome_seguro).suffix.lower()
            nome_final = f"{uuid.uuid4().hex}{extensao}"
            campanha_eventos.init_db(slug)
            arquivo.save(info["upload_dir"] / nome_final)

        campanha_eventos.criar_post(
            slug,
            titulo=titulo,
            texto=texto,
            tipo=tipo,
            foto=nome_final,
        )
        flash("Campanha publicada!", "ok")
        return redirect(url_for("campanha_admin", slug=slug))

    editar_evento = None
    if request.args.get("editar_evento"):
        editar_evento = pastores.obter_evento_lider(
            request.args.get("editar_evento", type=int),
            origem=slug,
        )

    return render_template(
        "campanha_admin.html",
        igreja=igreja,
        slug=slug,
        info=info,
        tipos=campanha_eventos.TIPOS_CULTO,
        posts=campanha_eventos.listar_posts(slug),
        post_ativo=campanha_eventos.obter_post_ativo(slug),
        destaque=campanha_eventos.obter_destaque(slug),
        eventos_calendario=pastores.listar_eventos_lideres(origem=slug),
        editar_evento=editar_evento,
        info_evento=pastores.RESPONSAVEIS_EVENTO[slug],
    )


@app.route("/evento/<slug>/admin/destaque/apagar-imagem", methods=["POST"])
@campanha_login_required
def campanha_apagar_imagem_destaque(slug: str):
    if campanha_eventos.apagar_imagem_destaque(slug):
        flash("Imagem do destaque apagada.", "ok")
    else:
        flash("Nenhuma imagem para apagar.", "erro")
    return redirect(url_for("campanha_admin", slug=slug))


@app.route("/evento/<slug>/admin/post/<int:post_id>/apagar", methods=["POST"])
@campanha_login_required
def campanha_apagar_post(slug: str, post_id: int):
    if campanha_eventos.apagar_post(slug, post_id):
        flash("Post apagado.", "ok")
    else:
        flash("Post não encontrado.", "erro")
    return redirect(url_for("campanha_admin", slug=slug))


@app.route("/evento/<slug>/admin/post/<int:post_id>/desativar", methods=["POST"])
@campanha_login_required
def campanha_desativar_post(slug: str, post_id: int):
    if campanha_eventos.desativar_post(slug, post_id):
        flash("Post desativado.", "ok")
    else:
        flash("Post não encontrado.", "erro")
    return redirect(url_for("campanha_admin", slug=slug))


@app.route("/evento/<slug>/admin/evento/<int:evento_id>/apagar", methods=["POST"])
@campanha_login_required
def campanha_apagar_evento(slug: str, evento_id: int):
    if pastores.apagar_evento_lider(evento_id, origem=slug):
        flash("Evento removido do calendário.", "ok")
    else:
        flash("Evento não encontrado.", "erro")
    return redirect(url_for("campanha_admin", slug=slug))


@app.route("/evento/<slug>")
def campanha_page(slug: str):
    if slug not in campanha_eventos.EVENTOS:
        return redirect(url_for("eventos_page"))
    igreja = load_json("igreja.json")
    info = campanha_eventos.config(slug)
    return render_template(
        "campanha.html",
        igreja=igreja,
        slug=slug,
        info=info,
        post_ativo=campanha_eventos.obter_post_ativo(slug),
        destaque_publico=campanha_eventos.obter_destaque_publico(slug),
    )


# ---------- Grupo de Louvor ----------

@app.route("/louvor/login", methods=["GET", "POST"])
def louvor_login():
    igreja = load_json("igreja.json")
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if check_password_hash(LOUVOR_PASSWORD_HASH, senha):
            session["louvor_ok"] = True
            destino = request.args.get("next") or url_for("louvor_admin")
            return redirect(destino)
        erro = "Senha incorreta. Tente novamente."
    if session.get("louvor_ok"):
        return redirect(url_for("louvor_admin"))
    return render_template(
        "louvor_login.html",
        igreja=igreja,
        erro=erro,
        h1_responsaveis=louvor.H1_RESPONSAVEIS,
    )


@app.route("/louvor/logout")
def louvor_logout():
    session.pop("louvor_ok", None)
    return redirect(url_for("eventos_page"))


@app.route("/louvor/admin", methods=["GET", "POST"])
@louvor_login_required
def louvor_admin():
    igreja = load_json("igreja.json")
    hoje = louvor.hoje()
    ano = int(request.args.get("ano", hoje.year))
    mes = int(request.args.get("mes", hoje.month))
    if mes < 1 or mes > 12:
        mes = hoje.month
    aba = request.args.get("aba", "escala")
    louvor.init_db()

    if request.method == "POST":
        acao = request.form.get("acao", "video").strip()

        if acao == "escala":
            data_iso = request.form.get("data", "").strip()
            if not data_iso:
                flash("Informe a data da escala.", "erro")
            else:
                escala_id = request.form.get("escala_id", type=int)
                louvor.salvar_escala(
                    data_iso=data_iso,
                    equipe=louvor.juntar_nomes(*request.form.getlist("equipe")),
                    louvores=request.form.get("louvores", ""),
                    escala_id=escala_id,
                )
                flash("Escala do louvor salva.", "ok")
            return redirect(
                url_for("louvor_admin", aba="escala", ano=ano, mes=mes)
            )

        if acao == "adicionar_membro":
            ok, mensagem = louvor.adicionar_membro(
                request.form.get("novo_membro", "")
            )
            flash(mensagem, "ok" if ok else "erro")
            return redirect(
                url_for("louvor_admin", aba="escala", ano=ano, mes=mes)
            )

        if acao == "remover_membro":
            membro_id = request.form.get("membro_id", type=int)
            if membro_id and louvor.remover_membro(membro_id):
                flash("Nome removido da lista.", "ok")
            else:
                flash("Não foi possível remover o nome.", "erro")
            return redirect(
                url_for("louvor_admin", aba="escala", ano=ano, mes=mes)
            )

        if acao == "video":
            titulo = request.form.get("titulo", "").strip() or "Vídeo do louvor"
            tema = request.form.get("tema", "").strip()
            link = request.form.get("link", "").strip()
            arquivo_capa = request.files.get("capa")
            arquivo_video = request.files.get("arquivo_video")
            # Compatível com formulário antigo / envio do MP4 no campo "capa"
            arquivo_unico = request.files.get("arquivo")
            link_vazio = link.lower() in {
                "",
                "não tem",
                "nao tem",
                "sem link",
                "n/a",
                "-",
            }
            if link_vazio:
                link = ""
            elif not louvor.link_valido(link):
                flash(
                    "Informe um link válido (YouTube ou Vimeo), ou deixe em branco.",
                    "erro",
                )
                return redirect(url_for("louvor_admin", aba="videos"))

            nome_capa = ""
            nome_video = ""

            def _salvar_video(upload) -> str | None:
                if not upload or not upload.filename:
                    return None
                if not louvor.extensao_video_ok(upload.filename):
                    return None
                nome_seguro = secure_filename(upload.filename)
                extensao = Path(nome_seguro).suffix.lower() or ".mp4"
                final = f"video-{uuid.uuid4().hex}{extensao}"
                upload.save(louvor.UPLOAD_DIR / final)
                return final

            def _salvar_capa(upload) -> str | None:
                if not upload or not upload.filename:
                    return None
                if not louvor.extensao_ok(upload.filename):
                    return None
                nome_seguro = secure_filename(upload.filename)
                extensao = Path(nome_seguro).suffix.lower()
                final = f"capa-{uuid.uuid4().hex}{extensao}"
                upload.save(louvor.UPLOAD_DIR / final)
                return final

            # 1) Campo dedicado de vídeo
            if arquivo_video and arquivo_video.filename:
                if not louvor.extensao_video_ok(arquivo_video.filename):
                    flash("Arquivo de vídeo: use MP4, WEBM, OGG ou MOV.", "erro")
                    return redirect(url_for("louvor_admin", aba="videos"))
                nome_video = _salvar_video(arquivo_video) or ""

            # 2) Campo único (ou MP4 enviado por engano em "capa")
            candidatos = []
            if arquivo_unico and arquivo_unico.filename:
                candidatos.append(arquivo_unico)
            if arquivo_capa and arquivo_capa.filename:
                candidatos.append(arquivo_capa)

            for upload in candidatos:
                nome = (upload.filename or "").lower()
                if louvor.extensao_video_ok(nome):
                    if not nome_video:
                        nome_video = _salvar_video(upload) or ""
                elif louvor.extensao_ok(nome):
                    if not nome_capa:
                        nome_capa = _salvar_capa(upload) or ""
                else:
                    flash(
                        "Envie vídeo em MP4/WEBM ou capa em JPG/PNG/WEBP/GIF.",
                        "erro",
                    )
                    return redirect(url_for("louvor_admin", aba="videos"))

            if not link and not nome_video and not nome_capa:
                flash(
                    "Envie o arquivo MP4 do vídeo (ou um link do YouTube/Vimeo).",
                    "erro",
                )
                return redirect(url_for("louvor_admin", aba="videos"))

            louvor.criar_video(
                titulo=titulo,
                tema=tema,
                link=link,
                capa=nome_capa,
                arquivo=nome_video,
            )
            if nome_video:
                flash("Vídeo publicado! O player aparece na página do louvor.", "ok")
            else:
                flash(
                    "Publicado só com capa/link. Para tocar o vídeo no site, envie o arquivo MP4.",
                    "ok",
                )
            return redirect(url_for("louvor_admin", aba="videos"))

        if acao == "integrante":
            nome = request.form.get("nome", "").strip()
            funcao = request.form.get("funcao", "").strip()
            arquivo = request.files.get("foto")
            if not nome:
                flash("Informe o nome do integrante.", "erro")
                return redirect(url_for("louvor_admin", aba="integrantes"))
            if not arquivo or not arquivo.filename:
                flash("Envie a foto do integrante.", "erro")
                return redirect(url_for("louvor_admin", aba="integrantes"))
            if not louvor.extensao_ok(arquivo.filename):
                flash("Foto: use JPG, PNG, WEBP ou GIF.", "erro")
                return redirect(url_for("louvor_admin", aba="integrantes"))
            nome_seguro = secure_filename(arquivo.filename)
            extensao = Path(nome_seguro).suffix.lower()
            nome_final = f"integrante-{uuid.uuid4().hex}{extensao}"
            arquivo.save(louvor.UPLOAD_DIR / nome_final)
            louvor.criar_integrante(nome=nome, funcao=funcao, foto=nome_final)
            flash("Integrante adicionado!", "ok")
            return redirect(url_for("louvor_admin", aba="integrantes"))

    editar_escala = None
    if request.args.get("editar_escala"):
        for item in louvor.listar_escala(ano, mes):
            if item["id"] == request.args.get("editar_escala", type=int):
                editar_escala = item
                break

    selecionados_equipe = (
        louvor.partir_nomes(editar_escala.get("equipe", ""))
        if editar_escala
        else []
    )

    return render_template(
        "louvor_admin.html",
        igreja=igreja,
        h1_responsaveis=louvor.H1_RESPONSAVEIS,
        videos=louvor.listar_videos(so_ativos=False),
        integrantes=louvor.listar_integrantes(so_ativos=False),
        membros=louvor.listar_membros(),
        escala=louvor.listar_escala(ano, mes),
        calendario=louvor.calendario_mes(ano, mes),
        editar_escala=editar_escala,
        selecionados_equipe=selecionados_equipe,
        ano=ano,
        mes=mes,
        aba=aba,
    )


@app.route("/louvor/admin/video/<int:video_id>/apagar", methods=["POST"])
@louvor_login_required
def louvor_apagar_video(video_id: int):
    if louvor.apagar_video(video_id):
        flash("Vídeo apagado.", "ok")
    else:
        flash("Vídeo não encontrado.", "erro")
    return redirect(url_for("louvor_admin", aba="videos"))


@app.route("/louvor/admin/integrante/<int:integrante_id>/apagar", methods=["POST"])
@louvor_login_required
def louvor_apagar_integrante(integrante_id: int):
    if louvor.apagar_integrante(integrante_id):
        flash("Integrante removido.", "ok")
    else:
        flash("Integrante não encontrado.", "erro")
    return redirect(url_for("louvor_admin", aba="integrantes"))


@app.route("/louvor/admin/escala/<int:escala_id>/apagar", methods=["POST"])
@louvor_login_required
def louvor_apagar_escala(escala_id: int):
    if louvor.apagar_escala(escala_id):
        flash("Dia removido da escala.", "ok")
    else:
        flash("Dia não encontrado.", "erro")
    return redirect(url_for("louvor_admin", aba="escala"))


@app.route("/louvor")
def louvor_page():
    igreja = load_json("igreja.json")
    hoje = louvor.hoje()
    ano = int(request.args.get("ano", hoje.year))
    mes = int(request.args.get("mes", hoje.month))
    if mes < 1 or mes > 12:
        mes = hoje.month
    busca = request.args.get("q", "").strip()
    escala = louvor.listar_escala(ano, mes)
    escala_destaque = louvor.obter_proxima_escala()
    calendario = louvor.calendario_mes(ano, mes)
    nome_igreja = igreja.get("nome") or "IGREJA CEASDREI"
    link = url_for("louvor_page", ano=ano, mes=mes, _external=True)
    whatsapp_dia = ""
    if escala_destaque:
        whatsapp_dia = louvor.url_whatsapp(
            louvor.texto_whatsapp_dia(escala_destaque, nome_igreja, link)
        )
    whatsapp_mes = louvor.url_whatsapp(
        louvor.texto_whatsapp_mes(
            escala,
            calendario["nome_mes"],
            ano,
            nome_igreja,
            link,
        )
    )
    return render_template(
        "louvor.html",
        igreja=igreja,
        h1_responsaveis=louvor.H1_RESPONSAVEIS,
        videos=louvor.listar_videos(busca=busca, so_ativos=True),
        integrantes=louvor.listar_integrantes(so_ativos=True),
        escala=escala,
        escala_destaque=escala_destaque,
        calendario=calendario,
        ano=ano,
        mes=mes,
        busca=busca,
        whatsapp_dia=whatsapp_dia,
        whatsapp_mes=whatsapp_mes,
    )


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
    return jsonify({"posts": posts})


@app.route("/api/batismo")
def api_batismo():
    return jsonify(
        {
            "fotos": batismo.listar_fotos(),
            "total_inscricoes": len(batismo.listar_inscricoes()),
        }
    )


@app.route("/api/casais")
def api_casais():
    return jsonify(
        {
            "fotos": casais.listar_fotos(),
            "programacao": casais.obter_programacao(),
            "total_inscricoes": len(casais.listar_inscricoes()),
        }
    )


@app.route("/api/obreiros")
def api_obreiros():
    return jsonify(
        {
            "escala_destaque": pastores.obter_proxima_escala(),
            "destaque_culto": pastores.obter_destaque(),
            "avisos": pastores.avisos_proximos(7),
        }
    )


@app.route("/data/<path:filename>")
def data_files(filename: str):
    """Expõe os JSON para o front estático / GitHub Pages."""
    return send_from_directory(DATA_DIR, filename)


# Garante pastas/banco mesmo com Gunicorn (produção)
gallery.init_db()
gallery.seed_fotos_iniciais()
batismo.init_db()
casais.init_db()
pastores.init_db()
arraial.init_db()
mocidade.init_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
