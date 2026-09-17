import io
import time
import streamlit as st
from docx import Document
from deep_translator import MyMemoryTranslator

# --------------------------------------------------------------------------- #
# Configuração da página e Estilo Visual
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="DocTranslate Pro",
    page_icon="🌐",
    layout="centered",
)

st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem; }
    .sub-title { font-size: 1.1rem; color: #4B5563; margin-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

# Lista de idiomas regionais suportados
IDIOMAS_SUPORTADOS = {
    "pt-PT": "Português (Portugal)",
    "pt-BR": "Português (Brasil)",
    "en-US": "Inglês (EUA)",
    "en-GB": "Inglês (Reino Unido)",
    "es-ES": "Espanhol (Espanha)",
    "es-419": "Espanhol (América Latina)",
    "fr-FR": "Francês",
    "de-DE": "Alemão",
    "it-IT": "Italiano",
    "zh-CN": "Chinês Simplificado",
    "ja-JP": "Japonês",
    "ko-KR": "Coreano",
    "ru-RU": "Russo",
    "ar-SA": "Árabe",
    "hi-IN": "Hindi",
    "emakhuwa": "Emakhuwa (Moçambique)",
    "ndau": "Ndau (Moçambique)",
    "tswa": "Tswa (Moçambique)",
    "af-ZA": "Afrikaans",
    "sq-AL": "Albanês",
    "hy-AM": "Arménio",
    "az-AZ": "Azerbaijano"
}

idiomas_ordenados = sorted(IDIOMAS_SUPORTADOS.keys(), key=lambda k: IDIOMAS_SUPORTADOS[k])

# --------------------------------------------------------------------------- #
# Lógica de fatiamento e tradução robusta
# --------------------------------------------------------------------------- #

def dividir_em_blocos(texto: str, limite: int = 450) -> list:
    if len(texto) <= limite:
        return [texto]
    blocos = []
    bloco_atual = ""
    for palavra in texto.split(" "):
        if len(bloco_atual) + len(palavra) + 1 > limite:
            blocos.append(bloco_atual.strip())
            bloco_atual = palavra
        else:
            bloco_atual += " " + palavra
    if bloco_atual:
        blocos.append(bloco_atual.strip())
    return blocos

def traduzir_texto_seguro(texto: str, idioma_origem: str, idioma_destino: str, email_api: str) -> str:
    texto_limpo = texto.strip()
    if not texto_limpo:
        return texto

    blocos = dividir_em_blocos(texto_limpo)
    resultados_traduzidos = []

    for bloco in blocos:
        try:
            time.sleep(1.0)
            tradutor = MyMemoryTranslator(source=idioma_origem, target=idioma_destino, email=email_api)
            resultado = tradutor.translate(bloco)
            if resultado:
                resultados_traduzidos.append(resultado)
            else:
                resultados_traduzidos.append(bloco)
        except Exception as erro:
            print(f"[ERRO] Falha no bloco: {erro}")
            resultados_traduzidos.append(bloco)

    return " ".join(resultados_traduzidos)

def processar_e_traduzir_paragrafo(paragrafo, origem: str, destino: str, email_api: str) -> int:
    texto_completo = paragrafo.text.strip()
    if not texto_completo:
        return 0
        
    contagem_palavras = len(texto_completo.split())
    texto_traduzido = traduzir_texto_seguro(texto_completo, origem, destino, email_api)
    
    if paragrafo.runs:
        run_alvo = None
        for run in paragrafo.runs:
            # Proteção estrita: Não tocamos nem limpamos runs com mídias ou formas geométricas
            if "drawing" in run._r.xml or "blip" in run._r.xml:
                continue
            
            # Se o run tiver texto legível
            if run.text.strip() or run.text:
                if run_alvo is None:
                    run_alvo = run
                    run_alvo.text = texto_traduzido
                else:
                    # Esvazia apenas textos secundários duplicados
                    run.text = ""
                    
        # Fallback de segurança se todos os runs forem tags complexas mas o parágrafo contiver texto
        if run_alvo is None and len(paragrafo.runs) > 0:
            paragrafo.runs[0].text = texto_traduzido
            
    return contagem_palavras

def traduzir_documento_completo(arquivo, origem: str, destino: str, email_api: str):
    documento = Document(arquivo)
    
    total_paragrafos = len(documento.paragraphs)
    total_palavras = 0
    
    barra_progresso = st.progress(0)
    status_texto = st.empty()
    
    # 1) Parágrafos do corpo
    for i, paragrafo in enumerate(documento.paragraphs):
        progresso_atual = (i + 1) / total_paragrafos if total_paragrafos > 0 else 1.0
        barra_progresso.progress(progresso_atual)
        status_texto.markdown(f"⏳ **Progresso:** Processando parágrafo {i+1} de {total_paragrafos}...")
        
        palavras_processadas = processar_e_traduzir_paragrafo(paragrafo, origem, destino, email_api)
        total_palavras += palavras_processadas
        
    # 2) Tabelas
    for tabela in documento.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for paragrafo in celula.paragraphs:
                    palavras_processadas = processar_e_traduzir_paragrafo(paragrafo, origem, destino, email_api)
                    total_palavras += palavras_processadas

    barra_progresso.empty()
    status_texto.empty()

    buffer = io.BytesIO()
    documento.save(buffer)
    buffer.seek(0)
    
    return buffer, total_paragrafos, total_palavras

# --------------------------------------------------------------------------- #
# Interface Gráfica — Barra Lateral
# --------------------------------------------------------------------------- #
st.sidebar.markdown("### ⚙️ Painel de Controle")

idx_origem = idiomas_ordenados.index("en-US") if "en-US" in idiomas_ordenados else 0
idx_destino = idiomas_ordenados.index("pt-PT") if "pt-PT" in idiomas_ordenados else 0

idioma_origem = st.sidebar.selectbox(
    "Idioma de origem",
    options=idiomas_ordenados,
    format_func=lambda sigla: IDIOMAS_SUPORTADOS[sigla],
    index=idx_origem
)

idioma_destino = st.sidebar.selectbox(
    "Idioma de destino",
    options=idiomas_ordenados,
    format_func=lambda sigla: IDIOMAS_SUPORTADOS[sigla],
    index=idx_destino
)

st.sidebar.divider()
st.sidebar.markdown("### 🔐 Credenciais da API")

email_usuario = st.sidebar.text_input(
    "E-mail para cota premium (Recomendado)",
    value="seu_email@exemplo.com",
    help="O MyMemory disponibiliza mais limite diário gratuito caso você envie um e-mail válido nas requisições."
)

st.sidebar.divider()
st.sidebar.markdown("### 📈 Status do Sistema")

if st.sidebar.button("🔍 Testar Linha de Conexão", use_container_width=True):
    try:
        teste = MyMemoryTranslator(source="en-US", target="pt-PT", email=email_usuario).translate("Hello")
        st.sidebar.success(f"Conectado com sucesso usando: {email_usuario}")
    except Exception as e:
        st.sidebar.error(f"Instabilidade detectada: {e}")

# --------------------------------------------------------------------------- #
# Interface Gráfica — Tela Principal
# --------------------------------------------------------------------------- #
st.markdown("<div class='main-title'>🌐 DocTranslate Pro</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Traduza arquivos Word mantendo o design, tabelas e logotipos intactos.</div>", unsafe_allow_html=True)

arquivo_enviado = st.file_uploader("", type=["docx"])

if arquivo_enviado is not None:
    st.success(f"📋 Arquivo pronto para análise: **{arquivo_enviado.name}**")
    
    if idioma_origem == idioma_destino:
        st.warning("⚠️ Ajuste os seletores! Idiomas de origem e destino idênticos.")
        
    if st.button("🚀 Iniciar Tradução Inteligente", type="primary", use_container_width=True):
        try:
            documento_pronto, n_paragrafos, n_palavras = traduzir_documento_completo(
                arquivo_enviado, idioma_origem, idioma_destino, email_usuario
            )
            
            st.balloons() 
            st.success("🎉 Processamento concluído com absoluto sucesso!")
            
            col1, col2 = st.columns(2)
            col1.metric("Parágrafos Traduzidos", n_paragrafos)
            col2.metric("Total de Palavras", n_palavras)
            
            st.download_button(
                label="📥 Baixar Documento Traduzido",
                data=documento_pronto,
                file_name=f"traduzido_{arquivo_enviado.name}",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        except Exception as erro:
            st.error(f"Falha operacional interna: {erro}")
else:
    st.info("💡 Envie um arquivo formatado em .docx para iniciar a esteira de tradução.")
