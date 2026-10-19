"""Escala automática dos obreiros e separação do cadastro."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import batismo  # noqa: E402
import pastores  # noqa: E402
import pdf_relatorios  # noqa: E402
from app import app  # noqa: E402

NOMES = [
    "Dc. Ana",
    "Dc. Bruno",
    "Dc. Carla",
    "Dc. Diego",
    "Dc. Elena",
    "Dc. Fabio",
    "Dc. Gisele",
    "Dc. Heitor",
    "Dc. Iris",
    "Dc. Joao",
]


class EscalaAutomaticaTest(unittest.TestCase):
    def test_so_quarta_sexta_e_domingo(self) -> None:
        linhas = pastores.montar_escala_automatica(NOMES, 2026, 10)
        self.assertGreaterEqual(len(linhas), 12)
        for linha in linhas:
            dia = date.fromisoformat(linha["data"])
            self.assertEqual(dia.month, 10)
            self.assertIn(dia.weekday(), pastores.DIAS_CULTO)
            pessoas = linha["porta_vidro"].split(" & ") + [
                linha["abertura"],
                linha["porta_escada"],
            ]
            self.assertEqual(len(pessoas), 4)
            self.assertEqual(len(set(pessoas)), 4)

    def test_mes_seguinte_muda_os_nomes(self) -> None:
        outubro = pastores.montar_escala_automatica(NOMES, 2026, 10)
        novembro = pastores.montar_escala_automatica(NOMES, 2026, 11)
        de_novo = pastores.montar_escala_automatica(NOMES, 2026, 10)
        self.assertEqual(outubro, de_novo)
        self.assertNotEqual(outubro[0]["porta_vidro"], novembro[0]["porta_vidro"])

    def test_lista_curta_nao_gera(self) -> None:
        self.assertEqual(pastores.montar_escala_automatica(["A", "B", "C"], 2026, 10), [])

    def test_pdf_da_escala(self) -> None:
        linhas = pastores.montar_escala_automatica(NOMES, 2026, 10)
        for linha in linhas:
            dia = date.fromisoformat(linha["data"])
            linha["data_br"] = dia.strftime("%d/%m/%Y")
            linha["dia_semana"] = "Domingo" if dia.weekday() == 6 else "Quarta"
            linha["eh_domingo"] = dia.weekday() == 6
        corpo = pdf_relatorios.gerar_pdf_escala_obreiros(linhas, "Outubro", 2026)
        self.assertTrue(corpo.startswith(b"%PDF"))
        self.assertGreater(len(corpo), 1000)

    def test_cada_pessoa_em_um_item(self) -> None:
        pessoas = batismo.pessoas_da_inscricao(
            {
                "nome_completo": "Família",
                "nome_marido": "",
                "nome_mulher": "",
                "filhos_objs": [
                    {"nome": "Ana Souza", "sexo": "F", "documento": "123"},
                    {"nome": "Bruno Souza", "sexo": "M", "documento": ""},
                ],
            }
        )
        self.assertEqual([p["nome"] for p in pessoas], ["Ana Souza", "Bruno Souza"])
        self.assertEqual(pessoas[0]["documento"], "123")


class CadastroSeparadoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_cadastro_e_onibus_em_paginas_diferentes(self) -> None:
        with self.client.session_transaction() as sess:
            sess["batismo_ok"] = True
        cadastro = self.client.get("/cadastro/batismo")
        onibus = self.client.get("/cadastro/onibus")
        self.assertEqual(cadastro.status_code, 200)
        self.assertEqual(onibus.status_code, 200)
        html_cadastro = cadastro.get_data(as_text=True)
        html_onibus = onibus.get_data(as_text=True)
        self.assertIn("Cadastro de Batismo", html_cadastro)
        self.assertIn("Famílias cadastradas", html_cadastro)
        self.assertIn("Nova inscrição", html_cadastro)
        self.assertIn("ÔNIBUS CEASDREI", html_onibus)
        self.assertNotIn("onibus-mapa", html_cadastro)
        self.assertIn("Mapa dos assentos", html_onibus)
        self.assertNotIn("Inscrições das famílias", html_onibus)
        self.assertIn("Cadastro do batismo", html_onibus)

    def test_gerar_escala_aparece_no_painel(self) -> None:
        with self.client.session_transaction() as sess:
            sess["pastores_ok"] = True
        resp = self.client.get("/pastores/admin?aba=escala&ano=2026&mes=10")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Gerar escala do mês", html)
        self.assertIn("Baixar PDF para imprimir", html)

    def test_pdf_publico_do_comunicado(self) -> None:
        resp = self.client.get("/comunicado/escala.pdf?ano=2026&mes=10")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/pdf")
        self.assertTrue(resp.get_data().startswith(b"%PDF"))
