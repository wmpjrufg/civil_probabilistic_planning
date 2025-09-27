import numpy as np


def discretizar_por_dias_inteiros(df_amostras):
    """
    Discretiza as amostras arredondando para o dia inteiro mais próximo.
    Os estados são os próprios dias. As probabilidades são suas frequências.
    """
    # 1. Arredonda todas as amostras para o inteiro mais próximo e converte para int
    df_arredondado = np.round(df_amostras).astype(int)
    
    parametros_discretizacao = {}
    print("\nDiscretizando por Dias Inteiros (arredondamento):")

    for atividade_codigo in df_arredondado.columns:
        counts = df_arredondado[atividade_codigo].value_counts(normalize=True).sort_index()

        estados = counts.index.tolist()
        probabilidades = counts.values.tolist()
     
        value_map = {estado: estado for estado in estados}
        
        parametros_discretizacao[atividade_codigo] = {
            'labels': estados,
            'value_map': value_map,
            'probs': probabilidades
        }
        # Este print mostrará o aumento da complexidade (número de estados)
        print(f" - Atividade {atividade_codigo}: {len(estados)} estados -> {estados}")
        
    return parametros_discretizacao