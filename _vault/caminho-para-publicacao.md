# Caminho para publicação

    status: estratégia (viva)
    atualizado: 2026-09-03

Discussão sobre o que é preciso para o artigo ser aceito numa revista com bom JCR, e como
fazer isso **sem acesso a dado real de obra**.

---

## 1. O problema de verdade não é técnico

O bug de um dia, o template do Overleaf, o *toy problem* de seis atividades — todos reais,
todos precisam ser resolvidos, e **nenhum deles é a razão pela qual o artigo seria
rejeitado**. A razão é:

> O artigo descreve um sistema. Revistas aceitam artigos que respondem uma pergunta.

Hoje, à pergunta "o que vocês descobriram?", a resposta é "construímos uma plataforma que
faz PERT/CPM com Monte Carlo e rede bayesiana". Isso é relato de implementação. O revisor
escreve *"the paper does not articulate a research question, and the combination of Monte
Carlo simulation with Bayesian networks for schedule risk is well established"* — e está
certo.

Corrigir o bug e trocar o template faz o artigo passar da triagem editorial. **Não faz ele
ser aceito.**

## 2. A pergunta que temos condição de responder

Está escondida na nossa própria seção de limitações:

> *"The current model assumes relative independence between activity durations. In
> real-world scenarios, external factors such as adverse weather conditions can cause
> correlated delays across multiple tasks."*

Está listado como limitação. **É a contribuição.**

O raciocínio: a prática — e boa parte da literatura — trata durações como independentes. Sob
independência, as durações dos caminhos se concentram (efeito de TCL) e a cauda direita do
*makespan* fica fina demais. Consequência prática: **a data P80 que vai para o contrato é
otimista, e ninguém sabe por quanto.** Na obra, chuva atinge todas as atividades externas ao
mesmo tempo; uma equipe improdutiva atrasa todas as atividades dela; fornecedor atrasado
trava tudo que depende daquele material.

Rede bayesiana é exatamente a ferramenta para isso — e é o que justifica nossa arquitetura,
que **hoje não se justifica**: com os nós `D_x` sem pais, as durações são independentes e a
BN não faz nada que um Monte Carlo condicionado não faça.

**Pergunta de pesquisa:**

> Quanto a hipótese de independência entre durações subestima a data comprometida em
> cronogramas de edificação, e a propagação de evidência durante a execução recupera essa
> diferença?

Tem pergunta, resposta mensurável, consequência prática direta (a data do contrato), e usa a
plataforma que já construímos.

## 3. Sem dado real: por que sintético é o desenho *correto*

Decisão de 03/09/2026: não teremos dado real de obra. É sigiloso e inviável.

Isso não é um problema para esta pergunta — é o desenho certo. Pensem no que seria preciso
para responder com dado real: uma obra real termina em **uma** data. n = 1. Não dá para
estimar um P90, muito menos medir o *viés* de um P90, a partir de uma realização. Seriam
necessárias centenas de obras comparáveis.

Com dado sintético, **conhecemos a verdade**. Geramos o mundo, sabemos o P90 verdadeiro, e
medimos exatamente quanto o modelo independente erra. É o mesmo argumento que sustenta
estudos de simulação em estatística e em confiabilidade: só se mede viés e cobertura contra
uma verdade conhecida.

> **Isso vira um parágrafo explícito de justificativa metodológica no artigo.** Escrito
> assim, o revisor não vê "não conseguiram dados"; vê "escolheram o desenho certo".

## 4. Antes disso: talvez não precisemos ser 100 % sintéticos

Dois caminhos de dado público de terceiros, que contornam o sigilo. Valem uma tarde de
investigação:

**Bases empíricas do grupo OR&S (Ghent, Mario Vanhoucke).** Base pública de projetos reais —
incluindo obras de construção — com cronograma de linha de base *e* dados de execução,
coletados na indústria e anonimizados para pesquisa. Referência de origem: Batselier &
Vanhoucke, sobre construção de base de projetos reais, *International Journal of Project
Management*.
⚠️ **Recuperado de memória — confirmar disponibilidade e licença antes de contar com isso.**
Se for o que parece, resolve o problema inteiro: dado real, de obra, público, citável, sem
sigilo.

**PSPLIB e bibliotecas de instâncias.** PSPLIB (Kolisch & Sprecher), RG30/RG300 e afins são
o padrão da comunidade de *project scheduling*. São geradas, não reais — mas são **o padrão
aceito**, com milhares de citações. Usar as instâncias padrão é radicalmente diferente de
inventar uma rede: os resultados passam a ser comparáveis com a literatura.

**Desenho ideal:** experimento sintético controlado para medir o viés com verdade conhecida
(validade interna) + instâncias públicas para mostrar que o efeito aparece em topologias
realistas (validade externa).

## 5. Os quatro requisitos de um estudo sintético publicável

Falhar em qualquer um derruba o artigo.

### 5.1 Experimento fatorial, não exemplo

A morte de um artigo sintético é *"geramos uma rede com 50 atividades"*. O revisor pergunta:
por que 50? por que essa topologia? Solução: varrer sistematicamente o espaço de fatores.

| Fator | Níveis | Observação |
|---|---|---|
| Topologia | grade sobre indicadores padrão | serial/paralelo, distribuição de atividades, comprimento de arcos, folga topológica; *order strength* de Kolisch |
| Tamanho | 30 / 60 / 90 / 120 | casa com os tamanhos do PSPLIB, garante comparabilidade |
| Variabilidade das durações | CV baixo / médio / alto | |
| **Força da correlação** | vários níveis | **fator de tratamento — é o que o artigo mede** |
| Fração exposta à causa comum | % de atividades atingidas | ex.: quantas atividades a chuva atinge |

O ponto mais importante é a topologia: a área tem **indicadores topológicos padrão**, e
gerar redes sobre uma grade controlada desses indicadores é metodologia aceita e citável. É
o que transforma "inventamos uma rede" em "amostramos o espaço de topologias segundo os
indicadores de [citação]".

Com replicações, vira experimento com estatística e superfície de resposta — não anedota.

### 5.2 Não gerar do mesmo modelo que ajustamos

Se geramos os dados com uma BN discreta e depois ajustamos uma BN discreta, não provamos
nada — é circular, e revisor de métodos vê na hora.

Gerar a verdade com mecanismo **diferente**: série climática contínua + modelo de fator
latente ou cópula sobre as durações contínuas. Aí a BN discreta é uma *aproximação sendo
testada*, e o erro de discretização vira resultado mensurável em vez de premissa escondida.

### 5.3 Parâmetros ancorados em fonte pública e citável

É isto que separa "sintético" de "inventado". Temos fontes brasileiras gratuitas e
excelentes:

- **INMET** — série histórica de precipitação diária, pública. Estimar P(dia adverso) por mês
  para uma cidade real. O nó de clima deixa de ser *prior* chutado e passa a ser estimado de
  ~20 anos de série.
- **SINAPI** (Caixa) e **TCPO** — composições com coeficientes de produtividade para serviços
  de construção. Oficiais, públicos, atualizados. Dá para derivar faixas de duração
  plausíveis e montar um cronograma sintético defensável: EAP de edifício residencial +
  durações vindas de composição oficial.

> Um cronograma construído sobre SINAPI, com clima calibrado no INMET, **não é um cronograma
> inventado** — é paramétrico, ancorado em fonte oficial. Essa distinção é tudo.

### 5.4 Métricas de verdade conhecida

Explorar o que só o sintético permite: **cobertura**.

> "O modelo independente declara P90; sob a verdade correlacionada, esse intervalo cobre
> apenas 71 % dos casos."

Falha de calibração medida exatamente — impossível com dado real. **É o resultado principal
do artigo.**

## 6. Os experimentos que constituem o artigo

1. **O viés da independência.** Mesmo cronograma, **mesmas marginais**, duas estruturas de
   dependência: independente vs. com nós de causa comum. Manter as marginais idênticas é
   essencial — isola o efeito da dependência. Reportar diferença em P80, P90 e CVaR do
   *makespan*, e a cobertura real dos intervalos nominais.
2. **Valor da atualização por evidência.** *Walk-forward*: a cada 10 % de avanço, condicionar
   nas durações observadas e recalcular. Comparar erro contra a conclusão verdadeira entre
   CPM determinístico, P80 estático, BN independente e BN correlacionada. Métricas: erro
   absoluto médio **e calibração**. Calibração é o que separa artigo sério de demonstração.
   (Com dado sintético temos a verdade, então este experimento fica disponível — era o que
   dependeria do cronograma realizado de uma obra real.)
3. **Escalabilidade.** Tempo e memória contra número de atividades, depois de resolver a
   explosão da CPT. Responde "isto roda em projeto de verdade?" antes que perguntem.

O **índice de criticidade** sai de graça (`pages/planning.py` já calcula e descarta os
caminhos das amostras) e dá a camada prática: não só *qual* é o risco, mas *onde* agir.

## 7. A revista muda — e para melhor

Sem estudo de caso real, a **JOBE fica difícil**: perfil aplicado, os revisores vão pedir
obra. Manteria na mesa só se a base do OR&S se confirmar utilizável — aí temos a perna
empírica que ela pede.

Um estudo metodológico controlado tem casas naturais, várias com JCR **acima** da JOBE:

| Revista | Por que encaixa |
|---|---|
| **International Journal of Project Management** | Casa natural para metodologia de risco de cronograma; é onde a literatura de benchmarks de projeto vive |
| **Reliability Engineering & System Safety** | Publica exatamente isso: método de incerteza validado em benchmark sintético com verdade conhecida |
| **European Journal of Operational Research** | Estudo experimental fatorial sobre redes de projeto é gênero corrente |
| **J. of Construction Eng. and Management (ASCE)** | Se quisermos manter o vínculo explícito com construção civil |

⚠️ Confirmar os JCR no *Journal Citation Reports* — os valores que carrego são aproximados.

**A restrição não rebaixa o alvo, redireciona** para revistas que valorizam justamente o
desenho que somos obrigados a adotar.

## 8. Duas vantagens a não desperdiçar

**Velocidade.** Sem construtora para convencer, sem NDA, sem dado sujo para limpar. O
cronograma passa a depender só de nós — o item de maior prazo de espera sai do caminho
crítico.

**Reprodutibilidade total.** Publicar gerador, instâncias e código com DOI no Zenodo.
Qualquer revisor reproduz cada número. Um artigo baseado em dado sigiloso de construtora
**nunca** pode oferecer isso. Virar argumento explícito na seção de disponibilidade de
dados — é diferencial real, não desculpa.

## 9. O que não muda

- O **bug de um dia** continua invalidando os números atuais → [Diagnóstico técnico](diagnostico-tecnico.md).
- A **CPT densa** continua impedindo rodar redes de 60–120 atividades — e agora é ainda mais
  crítico, porque o experimento fatorial *exige* centenas de instâncias desse porte.
- A alegação de **Digital Twin** fica mais frágil ainda sem obra. Abandonar o enquadramento
  de DT de vez.
- O **template** continua precisando de limpeza.

Ser honesto sobre uma coisa: **isto não é uma revisão do artigo atual, é um artigo novo
construído sobre a mesma plataforma.** Introdução, lacuna, resultados e conclusão serão
outros. Aproveita-se a fundamentação teórica, a implementação e o *toy problem* — que vira
exemplo didático do método, não a validação.

## Próximo passo

Escrever o desenho experimental completo: grade de fatores fechada, mecanismo gerador,
métricas, e o que cada tabela e figura do artigo mostraria.
