# -*- coding: utf-8 -*-
"""
Copyright (c) 2021 Deibson Carvalho.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
from .__version__ import (
    __title__,
    __description__,
    __url__,
    __version__,
    __author__,
    __author_email__,
    __license__,
    __copyright__
)
from .api import FipeAPI, CARRO, MOTO, CAMINHAO, GASOLINA, DIESEL, ALCOOL
from .exceptions import ValueNotFoundException, IncorrectValueException, IncorrectSettingsException
from typing import List, Dict, Optional


__all__ = ['FipeAPI', 'CARRO', 'MOTO', 'CAMINHAO', 'GASOLINA', 'DIESEL', 'ALCOOL', 'ValueNotFoundException',
           'IncorrectSettingsException', 'IncorrectValueException', 'pega_marcas', 'pega_modelos', 'pega_anos_modelo',
           'consulta_preco_veiculo']


def pega_marcas(tipo_veiculo: Optional[int] = CARRO,
                mes_referencia: Optional[int] = None,
                ano_referencia: Optional[int] = None) -> List:
    r""" Requisita todas as marcas de acordo com o tipo de veículo de acordo com o mês/ano da tabela de referência
    de preços da FIPE.
    :param tipo_veiculo: informa o tipo de veículo que pode ser "carro", "moto" ou "caminhao".
    :param mes_referencia: informa o mês da tabela de referência
    :param ano_referencia: informa o ano da tabela de referência
    :return: retorna a lista com as marcas
    :rtype: list
    """
    fipe_api = FipeAPI()
    fipe_api.seleciona_tipo_veiculo(tipo_veiculo=tipo_veiculo)
    fipe_api.seleciona_referencia(mes=mes_referencia, ano=ano_referencia)
    return fipe_api.pega_marcas()


def pega_modelos(marca: str,
                 tipo_veiculo: Optional[int] = CARRO,
                 mes_referencia: Optional[int] = None,
                 ano_referencia: Optional[int] = None) -> List:
    r""" Requisita todas os modelos de acordo com o tipo de veículo, o mês/ano da tabela de referência e a marca.
    :param marca: nome da marca.
    :param tipo_veiculo: informa o tipo de veículo que pode ser "carro", "moto" ou "caminhao".
    :param mes_referencia: informa o mês da tabela de referência (numérico)
    :param ano_referencia: informa o ano da tabela de referência (numérico com 4 dígitos)
    :return: retorna a lista com as marcas
    :rtype: list
    """
    fipe_api = FipeAPI()
    fipe_api.seleciona_tipo_veiculo(tipo_veiculo=tipo_veiculo)
    fipe_api.seleciona_referencia(mes=mes_referencia, ano=ano_referencia)
    fipe_api.seleciona_marca(marca=marca)
    return fipe_api.pega_modelos()


def pega_anos_modelo(marca: str,
                     modelo: str,
                     tipo_veiculo: Optional[int] = CARRO,
                     mes_referencia: Optional[int] = None,
                     ano_referencia: Optional[int] = None) -> List:
    r""" Requisita todas os modelos de acordo com o tipo de veículo, o mês/ano da tabela de referência e a marca.
    :param marca: nome da marca.
    :param modelo: nome do modelo
    :param tipo_veiculo: informa o tipo de veículo que pode ser "CARRO", "MOTO" ou "CAMINHAO".
    :param mes_referencia: informa o mês da tabela de referência (numérico)
    :param ano_referencia: informa o ano da tabela de referência (numérico com 4 dígitos)
    :return: retorna a lista com as marcas
    :rtype: list
    """
    fipe_api = FipeAPI()
    fipe_api.seleciona_tipo_veiculo(tipo_veiculo=tipo_veiculo)
    fipe_api.seleciona_referencia(mes=mes_referencia, ano=ano_referencia)
    fipe_api.seleciona_marca(marca=marca)
    fipe_api.seleciona_modelo(modelo=modelo)
    return fipe_api.pega_anos_modelo()


def consulta_preco_veiculo(marca: str,
                           modelo: str,
                           ano_do_modelo: int,
                           combustivel: Optional[int] = GASOLINA,
                           tipo_veiculo: Optional[int] = CARRO,
                           mes_referencia: Optional[int] = None,
                           ano_referencia: Optional[int] = None) -> Dict:
    r""" Requisita todas os modelos de acordo com o tipo de veículo, o mês/ano da tabela de referência e a marca.
    :param marca: nome da marca.
    :param modelo: nome do modelo
    :param ano_do_modelo: Ano do modelo
    :param combustivel: Combustível do veículo que pode ser "GASOLINA", "ALCOOL" ou "DIESEL".
    :param tipo_veiculo: informa o tipo de veículo que pode ser "CARRO", "MOTO" ou "CAMINHAO".
    :param mes_referencia: informa o mês da tabela de referência (numérico)
    :param ano_referencia: informa o ano da tabela de referência (numérico com 4 dígitos)
    :return: retorna um dicionário com as informações do veículo
    :rtype: dict
    """
    fipe_api = FipeAPI()
    fipe_api.seleciona_tipo_veiculo(tipo_veiculo=tipo_veiculo)
    fipe_api.seleciona_referencia(mes=mes_referencia, ano=ano_referencia)
    fipe_api.seleciona_marca(marca=marca)
    fipe_api.seleciona_modelo(modelo=modelo)
    return fipe_api.consulta_preco_veiculo(ano=ano_do_modelo, combustivel=combustivel)
