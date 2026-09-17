### 🌐 DocTranslate Pro

O **DocTranslate Pro** é uma aplicação web interativa desenvolvida em Python que permite a tradução de documentos de texto mantendo o design, o layout e a formatação originais (como negrito, itálico e estilos de parágrafos). O usuário faz o upload do arquivo, escolhe os idiomas e baixa o documento pronto instantaneamente. 

### 🚀 Funcionalidades

* **Preservação de Layout:** Tradução inteligente baseada em parágrafos e estruturas nativas do documento.
* **Fatiamento Inteligente:** Quebra textos longos automaticamente para respeitar os limites operacionais das APIs de tradução.
* **Controle de Cota (Privacy by Design):** Permite que cada usuário insira sua própria credencial de e-mail na barra lateral para expandir os limites de requisições diárias sem expor dados do desenvolvedor.
* **Interface Fluida e UX Avançada:** Barra de progresso em tempo real e exibição de métricas (número de parágrafos e contagem total de palavras processadas).

### 🛠️ Stack Tecnológica

* **Linguagem:** Python
* **Interface Web:** [Streamlit](https://streamlit.io/)
* **Manipulação de Arquivos:** [python-docx](https://python-docx.readthedocs.io/)
* **Motor de Tradução:** [deep-translator](https://github.com/nidhaloff/deep-translator) (Integração com MyMemory API)

### 💻 Como Rodar Localmente

1. **Clone o repositório:** 

bash

git clone https://github.com/seu-usuario/DocTranslate.git
cd DocTranslate

Use code with caution.
2. **Crie e ative o ambiente virtual:** 

bash

python -m venv .venv
# No Windows (PowerShell):
.venv\Scripts\activate

Use code with caution.
3. **Instale as dependências:** 

bash

pip install -r requirements.txt

Use code with caution.
4. **Execute a aplicação:** 

bash

streamlit run app.py

Use code with caution.

Desenvolvido como um projeto prático de engenharia de software e portfólio.