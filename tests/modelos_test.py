# -*- coding: utf-8 -*-
import pytest
from fipeapi import CARRO, CAMINHAO, MOTO, FipeAPI, IncorrectValueException, pega_modelos
from time import sleep


MARCA_CARRO = 'GM'
MARCA_CAMINHAO = 'SCANIA'
MARCA_MOTO = 'HONDA'

MODELO_INVALIDO = 'xxxxx'


class TestMarcas:

    api = FipeAPI()
    modelos_de_teste = {}

    @pytest.mark.parametrize(
        'tipo_veiculo, marca', (
                (CARRO, MARCA_CARRO),
                (MOTO, MARCA_MOTO),
                (CAMINHAO, MARCA_CAMINHAO),
        ))
    def test_pega_modelos(self, tipo_veiculo, marca):
        modelos = pega_modelos(tipo_veiculo=tipo_veiculo, marca=marca)
        assert len(modelos) > 0
        assert int(modelos[0]['codigo'])
        assert modelos[0]['modelo'] is not None
        self.modelos_de_teste[marca] = modelos[0]['modelo']
        sleep(2)

    @pytest.mark.parametrize(
        'tipo_veiculo, marca', (
                (CARRO, MARCA_CARRO),
                (MOTO, MARCA_MOTO),
                (CAMINHAO, MARCA_CAMINHAO),
        ))
    def test_seleciona_modelo(self, tipo_veiculo, marca):
        assert self.api.seleciona_referencia()
        sleep(.5)
        assert self.api.seleciona_tipo_veiculo(tipo_veiculo=tipo_veiculo)
        sleep(.5)
        assert self.api.seleciona_marca(marca=marca)
        sleep(.5)
        assert self.api.seleciona_modelo(modelo=self.modelos_de_teste[marca])
        sleep(1)
        self.api.limpa_dados_selecionados()

    def test_seleciona_modelo_invalido(self):
        with pytest.raises(IncorrectValueException):
            self.api.seleciona_modelo(modelo=MODELO_INVALIDO)
        self.api.limpa_dados_selecionados()
        sleep(1)

    @pytest.mark.parametrize(
        'tipo_veiculo, marca', (
                (CARRO, MARCA_CARRO),
                (MOTO, MARCA_MOTO),
                (CAMINHAO, MARCA_CAMINHAO),
        ))
    def test_seleciona_modelo_termo_invalido(self, tipo_veiculo, marca):
        with pytest.raises(IncorrectValueException):
            self.api.seleciona_referencia()
            self.api.seleciona_tipo_veiculo(tipo_veiculo=tipo_veiculo)
            self.api.seleciona_marca(marca=marca)
            self.api.seleciona_modelo(modelo=MODELO_INVALIDO)
        self.api.limpa_dados_selecionados()
        sleep(1)
