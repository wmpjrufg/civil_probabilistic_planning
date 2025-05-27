# Criando e usando um virtual environment

A tag `<>` deve ser eliminada quando usar o comando pois ela representa um trecho de código editável por parte do usuário.

Para ccriar o seu virtual env. não se esqueça de colocar o terminal na pasta desejada.

`python -m venv <meu_ambiente_virtual>`

## Ativando ela no Windows

`<meu_ambiente_virtual>\Scripts\activate`

## Ativando ela no Mac e Linux

`source <meu_ambiente_virtual>/bin/activate`

# Instalar Graphviz

É necessário ter instalado na máquina o Graphviz para o funcionamento da aplicação

https://graphviz.org/download/

# Instalando os requirements

Após a acriação da venv você pode instalar os requirements com o seguinte comando:  
`pip install -r requirements.txt`

# Rodar projeto

`streamlit run app.py`
