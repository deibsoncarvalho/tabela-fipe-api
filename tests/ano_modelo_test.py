# -*- coding: utf-8 -*-
import pytest
from fipeapi import (
    CARRO, CAMINHAO, MOTO, FipeAPI, pega_anos_modelo, pega_modelos
)
from time import sleep


MARCA_CARRO = 'GM'
MARCA_CAMINHAO = 'SCANIA'
MARCA_MOTO = 'HONDA'


class TestMarcas:

    api = FipeAPI()
    modelos_de_teste = {}

    @pytest.mark.parametrize(
        'tipo_veiculo, marca', (
                (CARRO, MARCA_CARRO),
                (MOTO, MARCA_MOTO),
                (CAMINHAO, MARCA_CAMINHAO),
        ))
    def test_pega_anos_modelo(self, tipo_veiculo, marca):
        modelos = pega_modelos(marca=marca, tipo_veiculo=tipo_veiculo)
        sleep(1)
        anos_modelo = pega_anos_modelo(tipo_veiculo=tipo_veiculo, marca=marca, modelo=modelos[0]['modelo'])
        assert len(anos_modelo) > 0
        assert anos_modelo[0].get('ano') is not None
        assert anos_modelo[0].get('combustivel') is not None
        sleep(2)
