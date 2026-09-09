"""Inscrição de batismo: duplicados e convite em PDF."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import batismo  # noqa: E402
from app import app  # noqa: E402


class BatismoInscricaoTest(unittest.TestCase):
    def setUp(self) -> None:
        batismo.init_db()
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self._ids: list[int] = []

    def tearDown(self) -> None:
        with batismo._connect() as conn:
            for inscricao_id in self._ids:
                conn.execute("DELETE FROM inscricoes WHERE id = ?", (inscricao_id,))

    def _criar(self, **kwargs) -> int:
        dados = {
            "nome_completo": "Família Silva",
            "nome_marido": "",
            "nome_mulher": "",
            "filhos": [{"nome": "João Silva", "documento": "", "sexo": "M"}],
            "rg_marido": "",
            "rg_mulher": "",
            "telefone": "11987171937",
            "participantes": ["familia"],
            "status": "vou",
        }
        dados.update(kwargs)
        inscricao_id = batismo.criar_inscricao(**dados)
        self._ids.append(inscricao_id)
        return inscricao_id

    def test_nome_trocado_ainda_bloqueia_pelo_telefone(self) -> None:
        self._criar()
        achou = batismo.buscar_inscricao_existente(
            telefone="11987171937",
            nomes=["Outra Pessoa"],
        )
        self.assertIsNotNone(achou)

    def test_telefone_com_mascara(self) -> None:
        self._criar()
        achou = batismo.buscar_inscricao_existente(
            telefone="(11) 98717-1937",
            nomes=["Nome Novo"],
        )
        self.assertIsNotNone(achou)

    def test_familia_nova_nao_conflita(self) -> None:
        self._criar()
        achou = batismo.buscar_inscricao_existente(
            telefone="11911112222",
            nomes=["Maria Souza"],
        )
        self.assertIsNone(achou)

    def test_formulario_bloqueia_mesmo_telefone(self) -> None:
        original = self._criar()
        antes = len(batismo.listar_inscricoes())
        resp = self.client.post(
            "/batismo/inscricao",
            data={
                "pessoas": ["Ricardo Alves"],
                "pessoas_doc": [""],
                "pessoas_sexo": ["M"],
                "telefone": "(11) 98717-1937",
                "status": "vou",
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"/batismo/confirmacao/{original}", resp.headers["Location"])
        self.assertIn("ja=1", resp.headers["Location"])
        self.assertEqual(len(batismo.listar_inscricoes()), antes)

    def test_confirmacao_tem_botao_de_convite(self) -> None:
        inscricao_id = self._criar()
        resp = self.client.get(f"/batismo/confirmacao/{inscricao_id}")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Baixar convite (PDF)", html)
        self.assertIn(f"/batismo/confirmacao/{inscricao_id}/convite.pdf", html)

    def test_mensagem_cadastro_repetido(self) -> None:
        inscricao_id = self._criar()
        resp = self.client.get(f"/batismo/confirmacao/{inscricao_id}?ja=1")
        html = resp.get_data(as_text=True)
        self.assertIn("já realizou o cadastro com sucesso", html)

    def test_pdf_do_convite(self) -> None:
        inscricao_id = self._criar()
        resp = self.client.get(f"/batismo/confirmacao/{inscricao_id}/convite.pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/pdf")
        corpo = resp.get_data()
        self.assertTrue(corpo.startswith(b"%PDF"))
        self.assertGreater(len(corpo), 1000)

    def test_valor_pago_editavel_e_comprovante(self) -> None:
        inscricao_id = self._criar(nome_completo="rebeca neguinha")
        self.assertTrue(batismo.atualizar_valor_pago(inscricao_id, "85,50"))
        item = batismo.obter_inscricao(inscricao_id)
        self.assertTrue(item["tem_pagamento"])
        self.assertEqual(item["valor_pago"], "85.50")
        self.assertEqual(item["valor_pago_texto"], "R$ 85,50")
        self.assertTrue(item["pago_em"])

        buffer = batismo.gerar_comprovante_pagamento_pdf(
            item, {"nome": "IGREJA CEASDREI"}
        )
        corpo = buffer.getvalue()
        self.assertTrue(corpo.startswith(b"%PDF"))
        self.assertGreater(len(corpo), 1000)

        with self.client.session_transaction() as sess:
            sess["batismo_ok"] = True
        resp = self.client.get(
            f"/batismo/admin/inscricao/{inscricao_id}/comprovante.pdf"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/pdf")

        html = self.client.get("/batismo/admin").get_data(as_text=True)
        self.assertIn("Valor pago", html)
        self.assertIn('name="valor_pago"', html)
        self.assertIn('placeholder="Ex.: 100,00"', html)
        self.assertIn("Baixar comprovante", html)
        self.assertIn("85,50", html)

        # limpar pagamento
        self.assertTrue(batismo.atualizar_valor_pago(inscricao_id, ""))
        item2 = batismo.obter_inscricao(inscricao_id)
        self.assertFalse(item2["tem_pagamento"])

    def test_parse_valor_pago_formatos(self) -> None:
        self.assertEqual(batismo.parse_valor_pago("100"), "100.00")
        self.assertEqual(batismo.parse_valor_pago("R$ 1.250,75"), "1250.75")
        self.assertEqual(batismo.parse_valor_pago(""), "")
        self.assertIsNone(batismo.parse_valor_pago("abc"))
        self.assertEqual(batismo.formatar_valor_pago_brl("1250.75"), "R$ 1.250,75")

    def test_comprovante_sem_valor_redireciona(self) -> None:
        inscricao_id = self._criar()
        with self.client.session_transaction() as sess:
            sess["batismo_ok"] = True
        resp = self.client.get(
            f"/batismo/admin/inscricao/{inscricao_id}/comprovante.pdf",
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/batismo/admin", resp.headers["Location"])


if __name__ == "__main__":
    unittest.main()
