"""
Igreja CEADREI — servidor Flask com páginas HTML e API JSON.
"""

from pathlib import Path

from flask import Flask, jsonify, render_template, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = Flask(__name__)


def load_json(name: str) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        return {}
    return __import__("json").loads(path.read_text(encoding="utf-8"))


@app.route("/")
def home():
    igreja = load_json("igreja.json")
    cultos = load_json("cultos.json").get("cultos", [])[:3]
    return render_template("index.html", igreja=igreja, cultos=cultos)


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


@app.route("/data/<path:filename>")
def data_files(filename: str):
    """Expõe os JSON para o front estático / GitHub Pages."""
    return send_from_directory(DATA_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
