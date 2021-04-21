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
import requests
import logging
import sys
import json
import os
import redis

from datetime import datetime

from .exceptions import (
    IncorrectValueException,
    NotConnectedException,
    ValueNotFoundException,
    RequestFailedException)

from typing import Tuple, List, Any, Dict
from .utils import meses_do_ano

log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# writing to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(log_format)
logger.addHandler(handler)


# Tipos de veículo
CARRO: int = 1
MOTO: int = 2
CAMINHAO: int = 3


# Combustíveis
GASOLINA = 1
ALCOOL = 2
DIESEL = 3


class FipeAPI:
    """
    Classe de Manipulação de Seção e Consulta com o website e API oficial FIPE

    Atributes:
    ---------
    is_verbose : bool, optional
        Informa se quer que seja mostrada as mensagens completas. Default: False

    Methods:
    --------
    conectar():
        Tenta estabelecer conexão com o website da FIPE para pegar os cookies e o cabeçalho de resposta
        para efetuar as chamadas de API

    atualiza_tabela_referencia():

    pega_marcas(codigo_tipo_veiculo, codigo_tabela_referencia):
        Faz requisição para API oficial da FIPE com o endpoint
        <https://veiculos.fipe.org.br/api/veiculos//ConsultarMarcas> para retornar um Json Object com o label e o
        código numérico da marca


    """

    __version__ = '0.1.0'

    def __init__(self, is_verbose=False, silently=False):
        # configuring log
        if silently:
            log_level = logging.WARNING
        elif is_verbose:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO

        logger.setLevel(log_level)

        # Chama a rotina para preparar os dados de conexão e o objeto
        self._prepara_conexao()

        # faz a conexão com o website FIPE para pegar os cookies de sessão
        self._conectar()

        # seta os dados necessários
        self._prepara_dados()

        # Chama a rotina para preparar o cache
        self._prepara_cache()

    def __del__(self):
        try:
            self._req.close()
        except Exception as error:
            logger.error(f'Error in close connection {error}')

    @property
    def status_conexao(self) -> int:
        if not self._req:
            return 0
        return self._req.status_code

    def _prepara_dados(self) -> None:
        """ Método interno simples para setar os valores iniciais das variáveis na inicialização """

        self._use_redis = os.environ.get('USE_REDIS', 'False').strip().lower()
        self._redis_host = os.environ.get('REDIS_HOST')
        self._redis_port = os.environ.get('REDIS_PORT', 6379)
        self._redis_db = os.environ.get('REDIS_DB', 0)

        self._tabela_referencia = None
        self._codigo_referencia_corrente = None
        self._prefixo_redis = 'fipeAPI'
        self._codigo_tipo_veiculo_corrente = None
        self._chave_tabela_referencia = 'TabelaReferencia'
        self._codigo_marca_corrente = None
        self._codigo_modelo_corrente = None
        self._codigo_ano_modelo_corrente = None

        self._marcas = dict()
        self._modelos = dict()
        self._anos_modelo = dict()
        self._preco = dict()

    def limpa_dados_selecionados(self):
        """ Função para limpar os dados da seleção """
        self._codigo_referencia_corrente = None # noqa
        self._codigo_tipo_veiculo_corrente = None # noqa
        self._codigo_marca_corrente = None # noqa
        self._codigo_modelo_corrente = None # noqa
        self._codigo_ano_modelo_corrente = None  # noqa

    def _prepara_conexao(self):
        """ Método para preparar as variáveis de conexão e o objeto de request """
        self._url = 'https://veiculos.fipe.org.br'
        self._api_root = 'api/veiculos/'
        self._session = requests.Session()
        self._headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                       'Chrome/51.0.2704.103 Safari/537.36',
                         'Accept': 'text/html, application/xhtml+xml, application/json, text/javascript',
                         'referrer': self._url,
                         'Connection': 'keep-alive',
                         'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
                         'Host': self._url.split("://")[1],
                         'Origin': self._url,
                         }
        self._req = None

    def _prepara_cache(self):
        """ Método para preparar o objeto de conexão com o Redis e as objetos e dados para cache """

        if self._use_redis == 'true':
            if not self._redis_host:
                logger.error(
                    """
                    Para fazer conexão com o Redis, é necessário informar o host na variável de ambiente REDIS_HOST
                    """
                )
                self._cache = False
                return

            logger.debug(f"""
            Iniciando a conexão com o Redis host: {self._redis_host} porta: {self._redis_port} 
            db: {self._redis_db} ...
            """)

            try:
                connection_pool = redis.ConnectionPool(host=self._redis_host,
                                                       port=self._redis_port,
                                                       db=self._redis_db)
                self._redis = redis.Redis(connection_pool=connection_pool)
                self._redis.time()
                logger.debug("""
                        Conexão com o Redis realizada com sucesso. Vamos utilizar o Cache.  
                """)
                self._cache = True
            except redis.exceptions.ConnectionError:
                logger.error(f"""
                    Falha na conexão com o Redis -> host: {self._redis_host} porta: {self._redis_port} 
                    db: {self._redis_db}
                """)
                logger.warning("""
                É altamente recomendado a utilização de cache para evitar muitas requisições à API da FIPE. Então, caso não
                tenha informado o servidor Redis para cache, faça o quanto antes, pois, seu IP pode ser bloqueado pela
                API. Além disso, sobrecarrega o servidor da FIPE. LEMBRE-SE: A FIPE NÃO DISPONIBILIZA API OFICIAL PREPARADA 
                PARA RECEBER ALTAS CARGAS DE REQUISIÇÕES. ENTÃO, VAMOS SER CONSCIENTES. 
                """)
                self._cache = False
        else:
            logger.warning("""
                É altamente recomendado a utilização de cache para evitar muitas 
                requisições à API da FIPE. Então, caso não
                tenha informado o servidor Redis para cache, faça 
                o quanto antes, pois, seu IP pode ser bloqueado pela
                API. Além disso, sobrecarrega o servidor da FIPE. LEMBRE-SE: 
                A FIPE NÃO DISPONIBILIZA API OFICIAL PREPARADA 
                PARA RECEBER ALTAS CARGAS DE REQUISIÇÕES. ENTÃO, VAMOS SER CONSCIENTES. 
                        """)
            self._cache = False
            return

    def _pega_codigo_referencia(self,
                                mes_referencia: int = None,
                                ano_referencia: int = None) -> int:
        """ Função interna para pegar o mes/ano de referência informado e retornar o código FIPE """

        if not mes_referencia or mes_referencia < 1:
            mes_referencia = datetime.today().month
        elif mes_referencia > 12:
            raise IncorrectValueException(
                f"""
                O valor do mês de referência informado "{mes_referencia}" não pode ser maior que 12. 
                """
            )
        else:
            mes_referencia = mes_referencia

        current_year = datetime.today().year

        if not ano_referencia or ano_referencia < 1:
            ano_referencia = current_year
        elif ano_referencia > current_year:
            raise IncorrectValueException(
                f"""
                O valor do ano de referência informado "{ano_referencia}" não pode ser no futuro. 
                """
            )
        else:
            try:
                first_year = int(self._tabela_referencia[-1]['Mes'].split("/")[1]) # noqa
            except Exception as error:
                logger.error(f'Erro ao verificar o primeiro Mes/Ano de referência: \n '
                             f'Dados: {self._tabela_referencia}'
                             f'\n Error Message: {error}.') # noqa
                return False

            if ano_referencia < first_year:
                raise IncorrectValueException(
                    f"""
                    O valor de ano informado não pode ser menor do que o primeiro ano da 
                    série {first_year}.
                    """
                )

        search = f'{meses_do_ano[mes_referencia]}/{ano_referencia}'

        logger.debug(f'Efetuando a busca do código de referência para {search} ...')

        codigo_tabela_referencia = 0

        for item in self._tabela_referencia:
            if item['Mes'].strip() == search:
                codigo_tabela_referencia = item['Codigo']
                break

        if codigo_tabela_referencia == 0:
            raise ValueNotFoundException(
                f"""
                    Não foi possível encontrar o Código da Tabela de Referência para {search}.
                """
            )
        return codigo_tabela_referencia

    def seleciona_referencia(self, mes: int = None, ano: int = None) -> bool:
        """ Função para definir o mês e ano desejado para a pesquisa """
        if not self._tabela_referencia:
            if not self._atualiza_tabela_referencia():
                raise ValueNotFoundException(
                    f"""
                        Não foi possível pegar o código da tabela de referência. Sem esta informação, não é possível
                        fazer requisições à FIPE.
                    """
                )
        self._codigo_referencia_corrente = self._pega_codigo_referencia(mes_referencia=mes, ano_referencia=ano)  # noqa
        return True

    def seleciona_tipo_veiculo(self, tipo_veiculo: int) -> bool:
        """ Método para definir o típo de veículo a ser pesquisado """
        if tipo_veiculo not in [CARRO, MOTO, CAMINHAO]:
            raise IncorrectValueException(
                f"""
                Valor de tipo de veículo está incorreto.
                """
            )
        self._codigo_tipo_veiculo_corrente = tipo_veiculo  # noqa
        return True

    def seleciona_marca(self, marca: str) -> bool:
        """ Método para definir a marca de veículo a ser pesquisada """
        marca = marca.strip().lower()
        marcas = self.pega_marcas()
        for m in marcas:
            name = m['marca'].lower()
            if name == marca or marca in name:
                self._codigo_marca_corrente = int(m['codigo']) # noqa
                return True
        raise IncorrectValueException(
            f"""
              A marca de carro informada "{marca}" não foi localizada.
            """
        )

    def seleciona_modelo(self, modelo: str) -> bool:
        """ Método para definir o modelo de veículo a ser pesquisado """
        modelo = modelo.strip().lower()
        modelos = self.pega_modelos()
        for m in modelos:
            name = m['modelo'].lower()
            if name == modelo or modelo in name:
                self._codigo_modelo_corrente = int(m['codigo']) # noqa
                return True
        raise IncorrectValueException(
            f"""
              O modelo de veículo informado "{modelo}" não foi localizado.
            """
        )

    def _verifica_ano_modelo(self, ano: int, combustivel: int) -> bool:
        """ Método interno para verificar se o ano e modelo estão corretos """
        anos = self.pega_anos_modelo()
        for a in anos:
            if a['ano'] == int(ano) and combustivel == a['combustivel']:
                return True
        return False

    def _verifica_condicoes_pesquisa(self) -> bool:
        """ Método interno para verificar se foi estabelecida conexão, se foi definida a tabela de referência e
        se foi definido o tipo de veículo """

        if not self._req:
            raise NotConnectedException(
                """
            Para fazer requisições de dados é necessário estabelecer conexão.  Para Criar conexão, chame o objeto 
            instanciado. 
                 """)

        if not self._codigo_referencia_corrente:
            raise IncorrectValueException(
                """
                O mês/ano de referência não foi definido. Usa a função define_referencia() para indicar o mês e ano
                da tabela que deseja informações. 
                 """)

        if not self._codigo_tipo_veiculo_corrente:
            raise IncorrectValueException(
                f"""
                 O tipo de veículo não foi definido. Informe qual o tipo de veículo que deseja informações. 
                 Tipos possíveis: "CARRO", "MOTO", "CAMINHAO"
                """)

        return True

    def _conectar(self) -> bool:
        """ Estabelece conexão com o web site da FIPE utilizando o header gerado """
        try:
            logger.info(f'iniciando conexão para o site {self._url} ...')
            logger.debug(f'Cabeçalho da requisição: {self._headers}')
            self._req = self._session.get(self._url, headers=self._headers)
        except requests.exceptions.ConnectTimeout:
            logger.error(f'tempo esgotado de conexão ... faça uma nova tentativa mais tarde.')
            return False
        except requests.exceptions.RequestException as error:
            logger.error(f'Ocorreu o seguinte erro na tentativa de conexão: {error}.')
            return False
        else:
            logger.debug(f'Cabeçalho da Resposta: \n{self._req.headers}.')
            if self._req.status_code < 400:
                logger.info('Conexão estabelecida com sucesso!')
                return True
            else:
                logger.info(f'Ocorreu um erro na conexão. Resposta: {self._req.status_code}.')
                return False

    def _verifica_cache(self) -> bool:
        """ Método interno para verificar se está utilzando cache e enviar mensagem de alerta """
        if not self._use_redis or not self._cache:
            return False
        return True

    def _salva_cache(self, origem: str, chave: str, valor: Any) -> bool:
        """ Função interna para salvar os dados em cache """
        if not self._verifica_cache():
            return False
        try:
            self._redis.set(f'{self._prefixo_redis}-{chave}', json.dumps(valor))
            logger.debug(f"""
            Dados de {origem} salvos com sucesso em cache -> \n
            chave: {chave} \n
            valor: {valor} 
            """)
        except redis.RedisError as error:
            logger.error(f"""
            Erro ao salvar o de {origem}: \n
            chave: {chave} \n
            valor: {valor} \n
            error: {error}
            """)
            return False
        return True

    def _pega_cache(self, origem: str, chave: str) -> bool:
        """ Método interno para pegar o cache das informações  """

        if not self._verifica_cache():
            return False

        logger.debug(f'pesquisando cache para {origem} com a chave {chave} ... ')

        try:
            _cache = self._redis.get(f'{self._prefixo_redis}-{chave}')
        except redis.RedisError as error:
            logger.error(f"""
            Falha em obter o cache do servidor Redis. \n
            origem: {origem} \n
            chave: {chave} \n
            Mensagem de erro: {error}
            """)
            return False

        if not _cache:
            logger.debug(f'Não há cache para a chave {chave} ({origem}).')
            return False
        else:
            return json.loads(_cache)

    def _pega_cache_tabela(self) -> bool:
        """ Método interno para pegar o cache das informações  """

        _cache_tabela = self._pega_cache('TabelaDeReferencia', self._chave_tabela_referencia)

        if not _cache_tabela:
            return False

        self._tabela_referencia = _cache_tabela

        # Pega o mês e ano atual
        today = datetime.today()
        current_month = today.month
        current_year = today.year

        try:
            last_reference = self._tabela_referencia[0]['Mes'].split("/")
            logger.debug(f'Checando se a última referência salva "{last_reference}" é igual ao mês/ano atual.')
            if meses_do_ano[current_month] == last_reference[0] and current_year == int(last_reference[1]):
                logger.info(f'A tabela de referências está atualizada ({last_reference[0]}/{last_reference[1]}).')
                return True
            else:
                return False
        except Exception as error:
            logger.error(f"""Erro ao verificar o último Mes/Ano de referência:\n "
            Dados: {self._tabela_referencia} \n
            Error Message: {error}.""")
            return False

    def _faz_requisicao(self, **kwargs) -> requests.Response:
        """ Método interno para fazer requisição á API"""
        consulta = self._session.post(**kwargs,
                                      headers=self._headers,
                                      cookies=self._req.cookies)
        if consulta.status_code == 200:
            logger.debug(f'requisição realizada com sucesso.')
            return consulta
        else:
            logger.error(f"""
                    Falha na requisição:
                    status code: {consulta.status_code} \n
                    url: {kwargs.get('url')}
                    data:{kwargs.get('data')}
                    headers: {consulta.headers}
                    """)
            return None

    def _atualiza_tabela_referencia(self) -> bool:
        """ Função para atualizar o código da tabela de referência para efetuar buscas no web site oficial da FIPE. Ela
        organiza os meses de referência em tabelas com códigos numéricos. Então cada código é equivalente a um
        mês e ano de referência. É necessário atualizar pelo menos uma vez no mês para pegar o código de referência do
        mês atual. É um código sequencial. Entretanto, é mais seguro pegar direto da fonte. Atualiza pelo menos uma vez

        Returns
        -------
        bool
            True (verdadeiro) se a atualização foi bem sucedida e False (falso) se tiver ocorrido algum erro
        """
        if not self._req:
            raise NotConnectedException(
                """
                    Não há conexão ativa para atualizar a tabela de referência.
                 """)

        if self._pega_cache_tabela():
            logger.debug('A Tabela de referências está atualizada e cacheada.')
            return True

        logger.debug("Fazendo a requisição de tabela de referência à FIPE ...")

        consulta = self._faz_requisicao(url=f'{self._url}/{self._api_root}/ConsultarTabelaDeReferencia')

        if not consulta:
            raise RequestFailedException(f"""
            Falha na requisição de atualização de tabela
            """)

        resultado = consulta.json()
        logger.debug(f'consulta realizada com sucesso. Dados obtidos > {resultado}')
        self._tabela_referencia = resultado
        self._salva_cache('tabela de referência', self._chave_tabela_referencia, resultado)
        return True

    def pega_marcas(self) -> List:
        """
        Faz requisição para a API oficial FIPE para pegar todas as marcas de acordo com os parâmetros
        Returns
        -------
        List:
            Lista dos modelos com dicionário com codigo e marca
        """

        self._verifica_condicoes_pesquisa()

        chave = f'{self._codigo_tipo_veiculo_corrente}{self._codigo_referencia_corrente}'

        try:
            return self._marcas[chave]
        except KeyError:
            pass

        _cache = self._pega_cache('marcas', chave)

        if _cache:
            self._marcas[chave] = _cache # noqa
            return _cache

        logger.info('Efetuando consulta à FIPE.')

        # Faz a requisição a API da FIPE
        data = {
            'codigoTabelaReferencia': self._codigo_referencia_corrente,
            'codigoTipoVeiculo': self._codigo_tipo_veiculo_corrente
        }

        res = self._faz_requisicao(url=f'{self._url}/{self._api_root}/ConsultarMarcas',
                                   data=data)

        if not res:
            raise RequestFailedException(f"""
            Falha na requisição de marcas
            """)

        conteudo = res.json()
        _dados_reformatados = list()

        # Reformatando os dados para ficarem mais apresentáveis
        for item in conteudo:
            _dados_reformatados.append({'codigo': int(item['Value']), 'marca': item['Label'].strip()})

        self._salva_cache(origem='marcas', chave=chave, valor=_dados_reformatados)
        self._marcas[chave] = _dados_reformatados # noqa
        return _dados_reformatados

    def pega_modelos(self) -> List:
        """
        Função interna para pegar todos os modelos de uma determinada marca de veículos

        Returns
        --------
        List:
            Lista dos modelos
        """

        self._verifica_condicoes_pesquisa()

        if not self._codigo_marca_corrente:
            raise IncorrectValueException(
                f"""
                A marca não foi selecionada. Selecione a marca com a função "seleciona_marca"
                """
            )

        chave = f'{self._codigo_tipo_veiculo_corrente}' \
                f'{self._codigo_referencia_corrente}' \
                f'{self._codigo_marca_corrente}'

        try:
            return self._modelos[chave]
        except KeyError:
            pass

        _cache = self._pega_cache('modelos', chave)

        if _cache:
            self._modelos[chave] = _cache  # noqa
            return _cache

        logger.info(f'Efetuando consulta à FIPE.')

        # Faz a requisição a API da FIPE
        data = {
            'codigoTabelaReferencia': self._codigo_referencia_corrente,
            'codigoTipoVeiculo': self._codigo_tipo_veiculo_corrente,
            'codigoModelo': '',
            'codigoMarca': self._codigo_marca_corrente,
            'ano': '',
            'codigoTipoCombustivel': '',
            'anoModelo': '',
            'modeloCodigoExterno': ''
        }

        consulta = self._faz_requisicao(url=f'{self._url}/{self._api_root}/ConsultarModelos',
                                        data=data)

        if not consulta:
            raise RequestFailedException(f"""
            Falha na requisição de modelos
            """)

        conteudo = consulta.json()['Modelos']

        # Reformatação dos dados
        _reformatado = list()
        for item in conteudo:
            _reformatado.append({'codigo': item['Value'], 'modelo': item['Label']})
        self._salva_cache(origem='modelos', chave=chave, valor=_reformatado)
        self._modelos[chave] = _reformatado  # noqa
        return _reformatado

    def pega_anos_modelo(self) -> List:
        """
        Função interna para pegar todos os Ano/modelos de uma determinado modelo e marca de veículos

        Returns
        --------
        List:
            Lista dos modelos
        """

        self._verifica_condicoes_pesquisa()

        if not self._codigo_marca_corrente:
            raise IncorrectValueException(
                f"""
                        A marca não foi selecionada. Selecione a marca com a função "seleciona_marca"
                """
            )

        if not self._codigo_modelo_corrente:
            raise IncorrectValueException(
                f"""
                        O modelo do veículo não foi selecionado. Selecione a marca com a função "seleciona_modelo"
                """
            )

        chave = f'{self._codigo_tipo_veiculo_corrente}' \
                f'{self._codigo_referencia_corrente}' \
                f'{self._codigo_marca_corrente}' \
                f'{self._codigo_modelo_corrente}'

        try:
            return self._anos_modelo[chave]
        except KeyError:
            pass

        _cache = self._pega_cache('anos-modelo', chave)

        if _cache:
            self._anos_modelo[chave] = _cache  # noqa
            return _cache

        logger.info(f'Efetuando consulta à FIPE.')

        # Faz a requisição a API da FIPE
        data = {
            'codigoTabelaReferencia': self._codigo_referencia_corrente,
            'codigoTipoVeiculo': self._codigo_tipo_veiculo_corrente,
            'codigoModelo': self._codigo_modelo_corrente,
            'codigoMarca': self._codigo_marca_corrente,
            'ano': '',
            'codigoTipoCombustivel': '',
            'anoModelo': '',
            'modeloCodigoExterno': ''
        }

        consulta = self._faz_requisicao(url=f'{self._url}/{self._api_root}/ConsultarAnoModelo',
                                        data=data)

        if not consulta:
            raise RequestFailedException(f"""
                    Falha na requisição de Anos modelo de veículo
                    """)

        conteudo = consulta.json()

        # Reformata os dados
        _reformatado = list()
        _combustiveis = {'Gasolina': GASOLINA,
                         'Álcool': ALCOOL,
                         'Diesel': DIESEL}
        for item in conteudo:
            _s = item['Value'].split("-")
            _reformatado.append({'ano': int(_s[0]),
                                 'combustivel': int(_s[1]),
                                 'descricao': item['Label'],
                                 'codigo': item['Value']})
        self._salva_cache(origem='anos-modelo', chave=chave, valor=_reformatado)
        self._anos_modelo[chave] = _reformatado  # noqa
        return _reformatado

    def consulta_preco_veiculo(self, ano: int, combustivel: int) -> Dict:
        """ Função para consultar preço de veículo na tabela FIPE """

        self._verifica_condicoes_pesquisa()

        if not self._codigo_marca_corrente:
            raise IncorrectValueException(
                f"""
                        A marca não foi selecionada. Selecione a marca com a função "seleciona_marca"
                """
            )

        if not self._codigo_modelo_corrente:
            raise IncorrectValueException(
                f"""
                        O modelo do veículo não foi selecionado. Selecione a marca com a função "seleciona_modelo"
                """
            )

        if combustivel not in [GASOLINA, ALCOOL, DIESEL]:
            raise IncorrectValueException(
                f"""
                      O combustível informado é inválido.
                 """
            )

        if not self._verifica_ano_modelo(ano=ano, combustivel=combustivel):
            raise IncorrectValueException(
                f"""
                     O ano ou o combustível informado estão incorretos. Não foi localizado com a marca e modelo
                     selecionados.
                """
            )

        chave = f'{self._codigo_tipo_veiculo_corrente}' \
                f'{self._codigo_referencia_corrente}' \
                f'{self._codigo_marca_corrente}' \
                f'{self._codigo_modelo_corrente}-' \
                f'{ano}-{combustivel}'

        try:
            return self._preco[chave]
        except KeyError:
            pass

        _cache = self._pega_cache('anos-modelo', chave)

        if _cache:
            self._anos_modelo[chave] = _cache  # noqa
            return _cache

        logger.info(f'Efetuando consulta à FIPE.')

        tipos = {1: 'carro', 2: 'moto', 3: 'caminhao'}

        #if _ano_modelo[0] == "Zero KM":
        #    _ano_modelo[0] = 32000

        # Faz a requisição a API da FIPE
        data = {
            'codigoTabelaReferencia': self._codigo_referencia_corrente,
            'codigoTipoVeiculo': self._codigo_tipo_veiculo_corrente,
            'codigoModelo': self._codigo_modelo_corrente,
            'codigoMarca': self._codigo_marca_corrente,
            'codigoTipoCombustivel': combustivel,
            'anoModelo': ano,
            'modeloCodigoExterno': '',
            'tipoVeiculo': tipos[self._codigo_tipo_veiculo_corrente],
            'tipoConsulta': 'tradicional'
        }

        consulta = self._faz_requisicao(url=f'{self._url}/{self._api_root}/ConsultarValorComTodosParametros',
                                        data=data)

        if not consulta:
            raise RequestFailedException(f"""
                    Falha na requisição de consulta de preço
                    """)

        conteudo = consulta.json()

        self._salva_cache(origem='preco', chave=chave, valor=conteudo)
        self._preco[chave] = conteudo  # noqa
        self._salva_codigo_fipe(**conteudo)
        return conteudo

    def _salva_codigo_fipe(self, **kwargs):
        """ Função para salvar o código fipe de um determinado veículo, modelo e ano """
        if not self._cache or not self._use_redis:
            return
        try:
            referencia = kwargs.get('MesReferencia').strip().split(" ")
            self._salva_cache(origem='tabela-fipe', chave=kwargs.get('CodigoFipe'), valor={
                'marca': kwargs.get('Marca'),
                'modelo': kwargs.get('Modelo'),
                'ano_modelo': kwargs.get('AnoModelo'),
                'combustivel': kwargs.get('Combustivel'),
                'tipo_veiculo': kwargs.get('TipoVeiculo'),
                'ano_referencia': referencia[2],
                'mes_referencia': referencia[0],
                'data_consulta': kwargs.get('DataConsulta'),
                'valor': kwargs.get('valor'),
            })
        except Exception as error:
            logger.error(
                f"""
                Ocorreu erro ao salvar os dados da tabela fipe: {kwargs}. Mensagem de erro: {error}
                """
            )
