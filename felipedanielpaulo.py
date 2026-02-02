# função de expressão regular

# aplicar aqui no total time uma distribuição triangular min=0.8 * total_time, mode=total_time, max=1.2 * total_time
# gera 10 mil amostras

index, time
0, 111.11
1, 95
2, 130
3, 85
..
9999, 120


# custo exemplo U$ 1095 por dia
cost_fix = sum(df["type of cost"=='Construction'])
cost_var = sum(df["type of cost"=='by time'])
index, time, cost (cost_var * ['time'] + cost_fix)
