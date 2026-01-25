import warnings
import streamlit as st

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
        /* Sidebar inteira */
        section[data-testid="stSidebar"] {
            display: none !important;
        }

        /* Botão de abrir sidebar (hamburger) */
        button[kind="header"] {
            display: none !important;
        }

        /* Margem que sobra quando sidebar existe */
        .block-container {
            padding-left: 2rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

warnings.filterwarnings("ignore", category=RuntimeWarning, module="torch._classes")

try:
    from networkx.drawing.nx_pydot import graphviz_layout
except ImportError:
    st.error("The graphviz module is not installed. Install it with: pip install pygraphviz or pydot.")

st.title("Probabilistic Project Planning")

st.markdown("Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.")

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    with open("benchmark.xlsx", "rb") as f:
        st.download_button(
            label="📥 Download sheet example",
            data=f,
            file_name="example.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
with col3:
    if st.button("Start"):
        st.switch_page("pages/app_page.py")
