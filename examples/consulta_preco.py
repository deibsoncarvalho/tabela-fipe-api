from fipeapi import CARRO, CAMINHAO, MOTO, consulta_preco_veiculo, pega_anos_modelo, pega_modelos
from time import sleep


def consulta_preco(marca="HONDA"):
    modelo = pega_modelos(tipo_veiculo=CAMINHAO, marca=marca)[0]['modelo']
    print(f"\nAnos do Modelo {modelo} da {marca}:")
    sleep(2)
    anos = pega_anos_modelo(marca=marca, modelo=modelo, tipo_veiculo=CAMINHAO)[0]
    preco = consulta_preco_veiculo(tipo_veiculo=CAMINHAO, marca=marca, modelo=modelo,
                                   ano_do_modelo=anos['ano'], combustivel=anos['combustivel'])
    print(preco)


if __name__ == '__main__':
    consulta_preco()
