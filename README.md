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
| `/galeria` | Fotos recentes dos cultos (públicas) |
| `/contato` | Endereço e contatos |
| `/admin/login` | Login da mídia (restrito) |
| `/admin/galeria` | Publicar/apagar fotos dos cultos |

---

## Galeria da mídia (admin)

A equipe de mídia acessa o painel, escolhe o culto da semana e envia as fotos.

- **URL:** http://127.0.0.1:5000/admin/login
- **Senha padrão (local):** `ceasdrei`
- As fotos aparecem na **página inicial** (carrossel) e em `/galeria`
- Cada postagem **expira em 2 dias** e é apagada automaticamente (arquivos + registro)
- Também dá para apagar manualmente no painel

Para mudar a senha em produção:

```bash
set ADMIN_PASSWORD=sua_senha_forte
set SECRET_KEY=chave_secreta_longa
python app.py
```

---

## API

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/info` | Dados gerais da igreja |
| `GET /api/cultos` | Lista de cultos |
| `GET /api/eventos` | Lista de eventos |
| `GET /api/contato` | Endereço e contatos |
| `GET /api/galeria` | Postagens ativas da galeria |
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

## Hospedagem (Render)

O código fica no GitHub e o site completo (com painel da mídia) roda no **Render**.

1. Abra o deploy: [Criar no Render com este repositório](https://dashboard.render.com/blueprint/new?repo=https://github.com/pethersonrdc/igreja-ceadrei)
2. Faça login no Render com a conta do GitHub
3. Confirme o Blueprint `igreja-ceadrei` e clique em **Apply**
4. Aguarde o deploy (pode levar alguns minutos na primeira vez)

Senha do painel em produção (padrão do `render.yaml`): `ceasdrei`

> No plano gratuito do Render, o site pode “dormir” após inatividade e demorar ~30s para acordar.  
> Uploads da galeria ficam no disco do servidor (efêmero): em um redeploy as fotos podem sumir antes dos 2 dias.

Arquivos de deploy:
- `Procfile` — inicia com Gunicorn
- `render.yaml` — configuração do serviço

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
