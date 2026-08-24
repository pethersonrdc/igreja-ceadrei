"""Inscrição de casais: duplicados e convite em PDF."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import casais  # noqa: E402
from app import app  # noqa: E402


class CasaisInscricaoTest(unittest.TestCase):
    def setUp(self) -> None:
        casais.init_db()
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self._ids: list[int] = []

    def tearDown(self) -> None:
        with casais._connect() as conn:
            for inscricao_id in self._ids:
                conn.execute("DELETE FROM inscricoes WHERE id = ?", (inscricao_id,))

    def _criar(self, **kwargs) -> int:
        dados = {
            "nome_marido": "Heilo Ribeiro",
            "telefone_marido": "00000000000",
            "nome_mulher": "Yasmin Gomes",
            "telefone_mulher": "00000000000000",
            "status": "vou",
        }
        dados.update(kwargs)
        inscricao_id = casais.criar_inscricao(**dados)
        self._ids.append(inscricao_id)
        return inscricao_id

    def test_detecta_mesmo_telefone(self) -> None:
        self._criar()
        achou = casais.buscar_inscricao_existente(
            nome_marido="Outro Nome",
            telefone_marido="(00) 00000-0000",
            nome_mulher="Outra Pessoa",
            telefone_mulher="11999999999",
        )
        self.assertIsNotNone(achou)
        self.assertEqual(achou["nome_marido"], "Heilo Ribeiro")

    def test_detecta_mesmo_casal_por_nome(self) -> None:
        self._criar(telefone_marido="11988887777", telefone_mulher="11988886666")
        achou = casais.buscar_inscricao_existente(
            nome_marido="heilo  ribeiro",
            telefone_marido="11111111111",
            nome_mulher="YASMIN GOMES",
            telefone_mulher="22222222222",
        )
        self.assertIsNotNone(achou)

    def test_casal_novo_nao_conflita(self) -> None:
        self._criar()
        achou = casais.buscar_inscricao_existente(
            nome_marido="João Silva",
            telefone_marido="11911112222",
            nome_mulher="Maria Silva",
            telefone_mulher="11933334444",
        )
        self.assertIsNone(achou)

    def test_formulario_duplicado_nao_cria_outra_inscricao(self) -> None:
        original = self._criar()
        antes = len(casais.listar_inscricoes())
        resp = self.client.post(
            "/casais/inscricao",
            data={
                "nome_marido": "Heilo ribeiro",
                "telefone_marido": "00000000000",
                "nome_mulher": "Yasmin Gomes",
                "telefone_mulher": "00000000000000",
                "status": "vou",
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"/casais/confirmacao/{original}", resp.headers["Location"])
        self.assertIn("ja=1", resp.headers["Location"])
        self.assertEqual(len(casais.listar_inscricoes()), antes)

    def test_mensagem_cadastro_repetido(self) -> None:
        inscricao_id = self._criar()
        resp = self.client.get(f"/casais/confirmacao/{inscricao_id}?ja=1")
        html = resp.get_data(as_text=True)
        self.assertIn("já realizou o cadastro com sucesso", html)
        self.assertIn("Baixar convite (PDF)", html)

    def test_confirmacao_tem_botao_de_convite(self) -> None:
        inscricao_id = self._criar()
        resp = self.client.get(f"/casais/confirmacao/{inscricao_id}")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Baixar convite (PDF)", html)
        self.assertIn(f"/casais/confirmacao/{inscricao_id}/convite.pdf", html)

    def test_pdf_do_convite(self) -> None:
        inscricao_id = self._criar()
        resp = self.client.get(f"/casais/confirmacao/{inscricao_id}/convite.pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/pdf")
        corpo = resp.get_data()
        self.assertTrue(corpo.startswith(b"%PDF"))
        self.assertGreater(len(corpo), 1000)


if __name__ == "__main__":
    unittest.main()
