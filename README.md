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
| `/batismo/login` | Login do Evento Batismo (restrito) |
| `/batismo/admin` | Fotos do sítio + lista de inscritos |
| `/batismo/inscricao` | Formulário público das famílias |
| `/casais/login` | Login do Encontro de Casais (restrito) |
| `/casais/admin` | Fotos + programação + inscritos |
| `/casais` | Página especial do encontro |
| `/casais/inscricao` | Formulário dos casais |
| `/pastores/login` | Login dos pastores (restrito) |
| `/pastores/admin` | Escala, destaque do culto e calendário |
| `/comunicado` | Comunicado público dos obreiros |
| `/calendario-lideres` | Calendário compartilhado dos líderes |
| `/arraial/login` | Login Arraiá / Cantina (Diac. Cássia) |
| `/arraial/admin` | Cantina + calendário do Arraiá |
| `/arraial` | Página decorativa do Arraiá Gospel |
| `/mocidade/login` | Login Líderes da Mocidade |
| `/mocidade/admin` | Posts do culto dos jovens |
| `/mocidade` | Página da mocidade |

---

## Galeria da mídia (admin)

A equipe de mídia acessa o painel, escolhe o culto da semana e envia as fotos.

- **URL:** http://127.0.0.1:5000/admin/login
- **Senha padrão (local):** `ceasdrei`
- As fotos aparecem na **página inicial** (carrossel) e em `/galeria`
- As postagens **permanecem** até a equipe apagar manualmente no painel

---

## Onde ficam imagens e dados

Estrutura local de armazenamento (já em uso):

| Pasta / arquivo | Conteúdo |
|-----------------|----------|
| `data/*.db` | Bancos SQLite (galeria, batismo, casais, pastores, arraial, mocidade) |
| `static/uploads/galeria/` | Fotos enviadas pela mídia |
| `static/uploads/batismo/` | Fotos do sítio / batismo |
| `static/uploads/casais/` | Fotos do encontro de casais |
| `static/uploads/pastores/` | Foto do pregador etc. |
| `static/uploads/arraial/` | Flyer do arraiá |
| `static/uploads/mocidade/` | Posts do culto dos jovens |
| `static/images/` | Fotos fixas dos líderes/login (versionadas no Git) |

Uploads e bancos **não vão para o Git** (ficam só no disco do servidor),
exceto as **fotos iniciais da galeria** em `static/images/galeria/`, que sobem com o deploy.
No Render gratuito o disco é temporário: em redeploy uploads novos podem sumir,
mas as fotos seed voltam se a galeria estiver vazia.
Para produção definitiva, use disco persistente ou armazenamento em nuvem (S3 etc.).

Para mudar a senha em produção:

```bash
set ADMIN_PASSWORD=sua_senha_forte
set SECRET_KEY=chave_secreta_longa
python app.py
```

---

## Evento Batismo

Área da **Evangelista Sueli** para publicar fotos do sítio e acompanhar as famílias.

- **Acesso responsável:** http://127.0.0.1:5000/batismo/login
- **Senha padrão (local):** `Sueli`
- **Inscrição das famílias:** http://127.0.0.1:5000/batismo/inscricao
- Fotos do sítio aparecem na **página inicial**, abaixo da galeria dos cultos
- No painel dá para exportar inscritos em **Excel** ou **PDF**

Para mudar a senha do batismo em produção:

```bash
set BATISMO_PASSWORD=sua_senha_forte
```

---

## Encontro de Casais

Área dos **Diac. Robson e Diac. Luana**.

- **Acesso responsáveis:** http://127.0.0.1:5000/casais/login
- **Senha padrão (local):** `Robson&Luana`
- **Página do encontro:** http://127.0.0.1:5000/casais
- **Inscrição dos casais:** http://127.0.0.1:5000/casais/inscricao
- No painel: fotos, texto livre do que vai ter no dia, export Excel/PDF

```bash
set CASAIS_PASSWORD=sua_senha_forte
```

---

## Pastores / Obreiros

Painel pastoral com:

- **Escala do mês** (porta vidro, abertura, porta escada)
- **Destaque do culto** (porta, abertura, pregador + foto, mensagem da campanha)
- **Calendário dos líderes** (cada evento com data e aviso próximo)

- **Acesso:** http://127.0.0.1:5000/pastores/login
- **Senha padrão (local):** `Solange123`
- **Comunicado público:** http://127.0.0.1:5000/comunicado
- Na **página inicial**, o dia de hoje/próximo culto aparece em destaque; o botão abre o comunicado completo

```bash
set PASTORES_PASSWORD=sua_senha_forte
```

---

## Arraiá Gospel / Cantina (Diac. Cássia)

- **Acesso:** http://127.0.0.1:5000/arraial/login
- **Senha padrão (local):** `Cassia`
- **Página do Arraiá:** http://127.0.0.1:5000/arraial
- Aviso animado na home aparece **2 dias antes** do evento (25/07/2026)
- No painel: texto da cantina + registro no calendário dos líderes

```bash
set ARRAIAL_PASSWORD=sua_senha_forte
```

---

## Líderes da Mocidade

- **Acesso:** http://127.0.0.1:5000/mocidade/login
- **Senha padrão (local):** `Mocidade`
- **Responsáveis:** Diác. Natan e Diác. Ana Beatriz
- Post simples (foto + texto) do culto dos jovens na página inicial

```bash
set MOCIDADE_PASSWORD=sua_senha_forte
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
> Uploads ficam no disco do servidor (efêmero): em um redeploy as fotos/dados podem sumir. Use disco persistente se precisar manter.

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
