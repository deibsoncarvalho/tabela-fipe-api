# -*- coding: utf-8 -*-
import pytest
from fipeapi import FipeAPI, IncorrectValueException, ValueNotFoundException
from datetime import datetime

HOJE = datetime.today()
MES_FUTURO = int(HOJE.month) + 1
ANO_FUTURO = int(HOJE.year) + 1
ANO_CORRENTE = HOJE.year
MES_CORRENTE = HOJE.month


class TestConexao:

    api = FipeAPI()

    def test_conexao(self):
        assert self.api.status_conexao == 200

    @pytest.mark.parametrize(
        'erro, mes, ano', (
                (IncorrectValueException, MES_FUTURO, ANO_FUTURO),
                (ValueNotFoundException, MES_FUTURO, ANO_CORRENTE),
                (IncorrectValueException, 1, 2000),
                (IncorrectValueException, 20, ANO_CORRENTE),
        )
    )
    def test_selecao_referencia_invalida(self, erro, mes, ano):
        with pytest.raises(erro):
            self.api.seleciona_referencia(mes=mes, ano=ano)

    @pytest.mark.parametrize(
        'mes, ano', (
                (MES_CORRENTE, ANO_CORRENTE),
                (MES_CORRENTE, ANO_CORRENTE-1),
                (MES_CORRENTE-1, ANO_CORRENTE),
                (MES_CORRENTE-1, ANO_CORRENTE-1),
        )
    )
    def test_selecao_referencia(self, mes, ano):
        assert self.api.seleciona_referencia(mes=mes, ano=ano)
