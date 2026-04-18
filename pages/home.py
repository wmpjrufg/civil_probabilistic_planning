import warnings
import streamlit as st

warnings.filterwarnings("ignore", category=RuntimeWarning, module="torch._classes")

try:
    from networkx.drawing.nx_pydot import graphviz_layout
except ImportError:
    st.error("The graphviz module is not installed. Install it with: pip install pygraphviz or pydot.")

# ── Language toggle ──────────────────────────────────────────────────────────
lang = st.selectbox("🌐 Language / Idioma", ["English", "Português"], index=1)

# ── Content per language ─────────────────────────────────────────────────────
content = {
    "English": {
        "title": "Probabilistic Project Planning",
        "description": """
A computational tool for probabilistic project scheduling that combines **Monte Carlo simulation**
with **Bayesian network inference**.

The user downloads the standardized input template, fills in each activity with its
**minimum, average, and maximum** duration estimates, and uploads it back to the platform.
All simulations are performed under a **triangular distribution** with **10,000 scenarios**,
capturing asymmetric uncertainty in activity durations.

From the simulation, the tool extracts the **critical path** and maps the
**dependency relationships between tasks**. The key differentiator is the integration of
Bayesian networks: once the simulation is complete, the user can insert observed evidence —
for example, *"Activity 3 took 5 days"* — and the network propagates that information across
all dependent tasks, **dynamically updating the remaining schedule forecasts**.

This allows for real-time, evidence-based replanning throughout the project lifecycle.
        """,
        "download_label": "📥 Download input template",
        "download_subtext": "Fill in the template with your activity data and upload it to get started.",
    },
    "Português": {
        "title": "Planejamento Probabilístico de Projetos",
        "description": """
Uma ferramenta computacional para planejamento probabilístico de projetos que combina
**simulação de Monte Carlo** com **inferência em redes bayesianas**.

O usuário baixa a planilha de entrada padronizada, preenche cada atividade com os tempos
**mínimo, médio e máximo** estimados e faz o upload para a plataforma. Todas as simulações são realizadas com base na **distribuição triangular** com **10.000 cenários**,
capturando a assimetria na incerteza das durações das atividades.

A partir da simulação, a ferramenta identifica o **caminho crítico** e mapeia as
**relações de dependência entre as tarefas**. O grande diferencial é a integração de redes
bayesianas: após a simulação, o usuário pode inserir evidências observadas —
por exemplo, *"A atividade 3 durou 5 dias"* — e a rede propaga essa informação por todas as
tarefas dependentes, **atualizando dinamicamente as previsões do restante do cronograma**.

Isso permite o replanejamento em tempo real, baseado em evidências, ao longo de todo o ciclo de vida do projeto.
        """,
        "download_label": "📥 Baixar planilha de exemplo",
        "download_subtext": "Preencha a planilha com os dados das suas atividades e faça o upload para começar.",
    },
}

# ── Render ────────────────────────────────────────────────────────────────────
c = content[lang]

st.title(c["title"])
st.markdown(c["description"])

st.markdown("---")
st.caption(c["download_subtext"])

with open("benchmark.xlsx", "rb") as f:
    st.download_button(
        label=c["download_label"],
        data=f,
        file_name="example.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )