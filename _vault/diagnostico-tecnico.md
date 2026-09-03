# Diagnóstico técnico

    status: diagnóstico (foto de 03/09/2026 — revisitar se o código mudar)
    atualizado: 2026-09-03

Achados verificados no código e no manuscrito. Contexto e prioridade em
[Caminho para publicação](caminho-para-publicacao.md).

---

## 1. A rede bayesiana entrega um dia a menos ⚠️

**O mais grave. Os números publicados na subseção *Belief updating* estão errados.**

Em `complex_network/create_cpt_final.py:58`, o tempo de conclusão de uma atividade **sem
predecessoras** parte de `-1`:

```python
max_of_t_parents = max(t_parent_states_indices) if t_parent_states_indices else -1
...
result_state = min(max_of_t_parents + d_state_value, num_completion_states - 1)
```

A primeira atividade termina em `d - 1` em vez de `d`, e o deslocamento propaga por toda a
rede até o nó final. **Deveria ser `0`.**

### Evidência

Reproduzindo a recursão determinística das CPTs sobre 10⁶ amostras triangulares do próprio
`benchmark.xlsx`:

| Modelo | Média | Moda | P80 | P95 |
|---|---:|---:|---:|---:|
| Monte Carlo contínuo | 10,77 | 11 | 11,47 | 12,16 |
| **BN — código atual** | **9,74** | **10** | **11,00** | **11,00** |
| BN — corrigida | 10,74 | 11 | 12,00 | 12,00 |

A moda 10 com p = 0,375 do código bugado **bate com o "10 days, p = 0.38" publicado no
artigo** — confirmando que os números vieram do código com o erro.

### Script reprodutor

Rodar da raiz do repositório. Só precisa de `numpy`, `pandas` e `openpyxl` — reimplementa a
recursão das CPTs, não precisa de `pgmpy`.

```python
import numpy as np, pandas as pd

rng = np.random.default_rng(7)
df = pd.read_excel("benchmark.xlsx", sheet_name="Plan")
p = {r["Code"]: (r["Min."], r["Mode"], r["Max."]) for _, r in df.iterrows()}

N = 1_000_000
S = {k: rng.triangular(a, m, b, N) for k, (a, m, b) in p.items()}
D = {k: np.round(v).astype(int) for k, v in S.items()}   # discretização da BN

def run(X, base=0.0):
    t = {}
    t["A"] = base + X["A"]
    t["B"] = t["A"] + X["B"]
    t["C"] = t["A"] + X["C"]
    t["D"] = t["B"] + X["D"]
    t["E"] = t["C"] + X["E"]
    t["F"] = np.maximum(t["D"], t["E"]) + X["F"]
    return t["F"]

for nome, x in [("MC contínuo", run(S)),
                ("BN código atual", run(D, -1)),   # o bug
                ("BN corrigida",    run(D,  0))]:
    s = pd.Series(np.round(x).astype(int)).value_counts(normalize=True)
    print("%-16s média=%.2f  moda=%s (p=%.3f)  P80=%.2f  P95=%.2f"
          % (nome, x.mean(), s.idxmax(), s.max(),
             np.percentile(x, 80), np.percentile(x, 95)))
```

### A correção

1. Trocar `-1` por `0` em `create_cpt_final.py:58`.
2. Refazer todos os números da subseção *Belief updating* e a figura `inference_result.png`.
3. **Adicionar o teste que teria pego isto:** a marginal a priori de `T_fim` tem que bater
   com o histograma do Monte Carlo dentro do erro de discretização. Hoje não existe nenhuma
   checagem cruzada entre os dois motores — foi exatamente essa ausência que deixou o viés
   passar até a redação.

## 2. A rede não escala

`create_completion_cpt` monta CPT **densa** de `num_completion_states × ∏(evidence_card)`:

| Cenário | Células |
|---|---:|
| *Toy problem* (20 estados, 2 pais T + 1 D) | 40 mil |
| Obra de 400 dias, atividade com 2 predecessoras | ~640 milhões |

E cresce por uma potência a cada predecessora adicional. **Bloqueia o experimento fatorial**,
que exige rodar centenas de instâncias de 30 a 120 atividades.

**Correção:** decompor o `max` em árvore binária de nós auxiliares de dois pais → CPTs de
O(k²) por nó, rede linear no número de atividades.

### Dois defeitos no dimensionamento dos estados

Em `complex_network/create_bayesian_network.py:39-44`:

- `nx.dag_longest_path` é chamado **sem pesos** — devolve o caminho com *mais arestas*, não o
  mais longo em duração.
- O total soma apenas os máximos das atividades daquele caminho, ignorando as demais.

Quando `num_completion_states` fica curto, o `min(..., num_completion_states - 1)` de
`create_cpt_final.py:65` **trunca a cauda e empilha massa de probabilidade no último
estado, em silêncio** — exatamente na região que VaR e CVaR medem.

**Correção:** usar como limite superior a soma de *todos* os máximos. Barato e seguro.

## 3. As durações são independentes

Os nós `D_x` são *priors* marginais **sem pais**. Consequência: a rede bayesiana só faz
atualização de crença, e não há resposta para *"por que uma BN, se um Monte Carlo
condicionado daria o mesmo?"*.

Este é o ponto que a nova pergunta de pesquisa ataca de frente — ver
[Caminho para publicação §2](caminho-para-publicacao.md#2-a-pergunta-que-temos-condição-de-responder).

## 4. Informação calculada e descartada

`pages/planning.py` acumula `caminhos_encontrados` para as 10.000 amostras e depois usa
**apenas o caminho da mediana**, para desenhar uma figura.

Os **índices de criticidade** — P(atividade pertencer ao caminho crítico) — e a *cruciality*
— correlação entre duração da atividade e *makespan* — saem quase de graça daí. É o que a
literatura de *schedule risk analysis* espera ver, e é o que diz ao engenheiro **onde** agir.

## 5. Pendências do manuscrito

### Estrutura

- `Section_5` ("Results") é uma conclusão que **duplica** `Section_6`.
- Os resultados de verdade estão dentro de `Section_4` ("Implementation").
- Não há seção de discussão.

### Restos de template em `main.tex`

`\lipsum`, seção "Introduction2", `cat_momo_1.png`, tabelas de exemplo, nomenclatura de
temperatura e dissipação turbulenta, *abstract* e *keywords* ainda com o texto de instrução,
oito ORCID `0000-0000-0000-0000`. E o template é `biblatex`+APA, não o `elsarticle.cls` da
Elsevier.

### Notação e afirmações erradas

- Convenção de VaR divergente: o texto define `P(X > VaR_α) = α` com α = 5 %, mas
  `var_cvar.py` faz `np.percentile(data, confidence_level·100)`, usando o argumento como
  nível do quantil.
- Na Seção 4: *"the CVaR₂₀% drops to 11.48 days and the CVaR₂₀% to 11.95"* — o primeiro é VaR.
- A Seção 4 afirma que a amostragem usa `Scipy`. O código usa
  `parepy_toolbox.random_sampling` com **Latin Hypercube**, não Monte Carlo simples — o que
  muda inclusive como se estimam intervalos de confiança.
- Frase truncada: *"a value consistent with the Monte Carlo sample sizes."* seguida de
  `% [citar 1 ou 2 trabalhos]`.
- Estatísticas **incondicionais** (10,77 / 10,75 / 0,82) repetidas no parágrafo da inferência
  condicional.
- Comentário em português ainda pendente: *"%HK. Acho que a Figura 6 nao eh densidade…"* —
  que está certo e não foi endereçado.

### Referências e figuras

- `\ref{fig:risk_analysis}` aponta para figura comentada → sai `??` no PDF.
- `pearl1988probabilistic` é citada na Seção 2 e **não existe** no `references.bib`.
- **39 das 82 entradas nunca são citadas** — Lamport, TUGBoat, ACSM, *deep learning*,
  geotecnia: herança de template.
- `fig:031024` e `fig2:031024` nunca são citadas; `fig_grafo_direcionado.png` e
  `fig2_grafo_direcionado.png` parecem o mesmo grafo repetido.
- Mistura de `\cite` / `\citep` / `\parencite`.
- Arquivos mortos: `bn.tex` vazio, `main1.old`, `mybibfile.bib` duplicando `references.bib`.
- **Zero citações** à JOBE ou à *Automation in Construction*.

## 6. Pendências do repositório

- Sem `LICENSE`, `CITATION.cff` ou DOI. Um *release* no Zenodo dá DOI e vira a linha de
  *Data and Code Availability* — que, no desenho sintético, é **argumento de venda**, não
  formalidade.
- `readme.md` em português e só ensina a criar *venv*. Falta o que interessa ao revisor:
  como reproduzir cada figura e tabela do artigo, com um comando.
- **Sem semente e sem testes.** Um teste de consistência MC × BN teria pego o item 1.
- `caminho_critico_node.py` executa um exemplo em nível de módulo e imprime no `import`.
- `pages/budget.py` é stub *"under construction"* — e o artigo divulga a URL pública do app.
- Versão do Python não fixada; `notebook/` tem arquivo com espaço no nome;
  `app_deterministic.py` parece código morto.
