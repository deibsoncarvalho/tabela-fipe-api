# -*- coding: utf-8 -*-
import pytest
from fipeapi import pega_marcas, CARRO, CAMINHAO, MOTO, FipeAPI, IncorrectValueException
from time import sleep


MARCA_CARRO = 'GM'
MARCA_CAMINHAO = 'SCANIA'
MARCA_MOTO = 'HONDA'

MARCA_CARRO_INVALIDA = 'AAAAA'
MARCA_CAMINHAO_INVALIDA = 'ZZZZ'
MARCA_MOTO_INDALIDA = 'ZWIA'


class TestMarcas:

    api = FipeAPI()

    @pytest.mark.parametrize(
        'tipo_veiculo', (
                (CARRO),
                (MOTO),
                (CAMINHAO),
        ))
    def test_pega_marcas(self, tipo_veiculo):
        marcas = pega_marcas(tipo_veiculo=tipo_veiculo)
        assert len(marcas) > 0
        assert int(marcas[0]['codigo'])
        assert marcas[0]['marca'] is not None
        sleep(1)

    @pytest.mark.parametrize(
        'tipo_veiculo, marca', (
                (CARRO, MARCA_CARRO),
                (MOTO, MARCA_MOTO),
                (CAMINHAO, MARCA_CAMINHAO),
        ))
    def test_seleciona_marca(self, tipo_veiculo, marca):
        assert self.api.seleciona_referencia(mes=4, ano=2020)
        sleep(.5)
        assert self.api.seleciona_tipo_veiculo(tipo_veiculo=tipo_veiculo)
        sleep(.5)
        assert self.api.seleciona_marca(marca=marca)
        self.api.limpa_dados_selecionados()
        sleep(1)

    def test_seleciona_tipo_veiculo_invalido(self):
        with pytest.raises(IncorrectValueException):
            self.api.seleciona_tipo_veiculo(tipo_veiculo=4)

    @pytest.mark.parametrize(
        'tipo_veiculo, marca', (
                (CARRO, MARCA_CARRO_INVALIDA),
                (MOTO, MARCA_MOTO_INDALIDA),
                (CAMINHAO, MARCA_CAMINHAO_INVALIDA),
        ))
    def test_seleciona_marca_invalida(self, tipo_veiculo, marca):
        with pytest.raises(IncorrectValueException):
            self.api.seleciona_tipo_veiculo(tipo_veiculo=tipo_veiculo)
            self.api.seleciona_marca(marca=marca)
        self.api.limpa_dados_selecionados()
        sleep(1)
