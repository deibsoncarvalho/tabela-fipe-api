# -*- coding: utf-8 -*-
"""
fipe-api.exceptions
~~~~~~~~~~~~~~~~~~~
This module contains the set of Fipe-API' exceptions.
"""
from requests.exceptions import RequestException


class NotConnectedException(RequestException):
    """ Não há conexão ativa para atualizar a tabela de referência.  """


class IncorrectValueException(ValueError):
    """ Valor informado está incorreto. """

    def __init__(self, *args, **kwargs):
        self.param = kwargs.pop('param', None)
        self.value = kwargs.pop('value', None)
        message = f'Valor informado para o parâmetro {self.param} "{self.value}" está incorreto.'
        super(IncorrectValueException, self).__init__(message, *args)


class ValueNotFoundException(ValueError):
    """ Não foi possível encontrar o valor para o termo """

    def __init__(self, *args):
        message = f'Não foi possível encontrar o valor para o termo "{args[0]}".'
        super(ValueNotFoundException, self).__init__(message, *args)


class IncorrectSettingsException(Exception):
    pass


class RequestFailedException(RequestException):
    pass
