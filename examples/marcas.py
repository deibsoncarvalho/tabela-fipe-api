from fipeapi import pega_marcas, CARRO, CAMINHAO, MOTO


def cria_lista_marcas_carros():
    marcas = pega_marcas(tipo_veiculo=CARRO, mes_referencia=1, ano_referencia=2020)
    print("\nMarcas de carro disponíveis para a referência janeiro/2020:\n")
    for marca in marcas:
        print(f'-> Marca: {marca["marca"]} - Codigo FIPE: {marca["codigo"]}')


if __name__ == '__main__':
    cria_lista_marcas_carros()
