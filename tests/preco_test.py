# -*- coding: utf-8 -*-
import pytest
from fipeapi import (
    CARRO, CAMINHAO, MOTO, FipeAPI, pega_anos_modelo, consulta_preco_veiculo, pega_modelos
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
    def test_consulta_preco(self, tipo_veiculo, marca):
        modelos = pega_modelos(marca=marca, tipo_veiculo=tipo_veiculo)
        assert len(modelos) > 0
        modelo = modelos[0]['modelo']
        sleep(1)
        anos_modelo = pega_anos_modelo(tipo_veiculo=tipo_veiculo, marca=marca, modelo=modelo)
        sleep(1)
        preco = consulta_preco_veiculo(marca=marca, modelo=modelo, ano_do_modelo=anos_modelo[0]['ano'],
                                       combustivel=anos_modelo[0]['combustivel'],
                                       tipo_veiculo=tipo_veiculo)
        assert type(preco) is dict
        assert preco.get('Valor') is not None
        sleep(2)
