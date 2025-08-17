import numpy as np

def value_at_risk(data, confidence_level=0.95):
    """
    Calcula o Value at Risk (VaR) de uma lista de valores.

    Args:
        data (list or array): Lista de valores (por exemplo, perdas ou durações).
        confidence_level (float): Nível de confiança (ex: 0.95 para 95%).

    Returns:
        float: Valor de VaR no nível de confiança especificado.
    """
    data = np.array(data)
    var = np.percentile(data, (confidence_level) * 100)
    return var


def conditional_value_at_risk(data, confidence_level=0.95):
    """
    Calcula o CVaR (Conditional Value at Risk) de uma lista de valores.

    Args:
        data (list or array): Lista de valores (por exemplo, perdas ou durações).
        confidence_level (float): Nível de confiança (ex: 0.95 para 95%).

    Returns:
        float: Valor de CVaR no nível de confiança especificado.
    """
    data = np.array(data)
    var = value_at_risk(data, confidence_level)
    cvar = data[data >= var].mean()
    return cvar
