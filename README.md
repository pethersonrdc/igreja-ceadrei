# Igreja CEADREI — Site Completo

Site institucional da **Igreja CEADREI**, feito em **Python (Flask)** com **HTML** e **CSS**, e uma **API JSON** para informações da igreja, cultos e eventos.

Projeto vinculado ao GitHub Project: [Igreja CEADREI — site Completo](https://github.com/users/pethersonrdc/projects/2)

---

## Tecnologias

- **Python 3** + **Flask** — páginas e API
- **HTML / CSS / JavaScript** — interface do site
- **JSON** — dados editáveis em `data/`

---

## Como rodar localmente

```bash
# 1. Entrar na pasta do projeto
cd "Projeto Igreja"

# 2. (Opcional) criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Iniciar o servidor
python app.py
```

Abra no navegador: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Páginas

| Rota | Conteúdo |
|------|----------|
| `/` | Página inicial |
| `/sobre` | Missão, visão e valores |
| `/cultos` | Horários de culto |
| `/eventos` | Agenda de eventos |
| `/contato` | Endereço e contatos |

---

## API

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/info` | Dados gerais da igreja |
| `GET /api/cultos` | Lista de cultos |
| `GET /api/eventos` | Lista de eventos |
| `GET /api/contato` | Endereço e contatos |
| `GET /data/<arquivo>.json` | Arquivos JSON brutos |

Exemplo:

```bash
curl http://127.0.0.1:5000/api/cultos
```

---

## Como atualizar as informações

Edite os arquivos em `data/`:

- `data/igreja.json` — nome, lema, endereço, sobre
- `data/cultos.json` — horários de culto
- `data/eventos.json` — eventos

Reinicie o servidor Flask (se estiver rodando) para ver as mudanças.

---

## Estrutura do projeto

```
.
├── app.py                 # Aplicação Flask + API
├── requirements.txt
├── README.md
├── data/                  # Dados da API / conteúdo
├── static/
│   ├── css/styles.css
│   └── js/main.js
└── templates/             # Páginas HTML (Jinja2)
```

---

## Hospedagem no GitHub

O **código** fica neste repositório.

> **Importante:** o GitHub Pages hospeda sites **estáticos** (HTML/CSS/JS). Ele **não executa Python/Flask**.  
> Para o site completo com API Python online, use um serviço gratuito como [Render](https://render.com), [Railway](https://railway.app) ou [PythonAnywhere](https://www.pythonanywhere.com), apontando para `app.py` / `gunicorn app:app`.

### Publicar o código

```bash
git add .
git commit -m "Atualiza o site da Igreja CEADREI"
git push
```

---

## GitHub Project

No Project settings, defina o **Default repository** como este repositório (`igreja-ceadrei`), e não o `sistema-mercado`.

---

## Próximos passos sugeridos

1. Atualizar endereço, telefone e redes em `data/igreja.json`
2. Colocar fotos reais da igreja (substituir a imagem do hero no CSS)
3. Publicar a API Flask em um host gratuito
4. Organizar tarefas no [Project #2](https://github.com/users/pethersonrdc/projects/2)

---

Feito com fé e propósito para a comunidade CEADREI.
