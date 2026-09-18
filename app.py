import io
import re
import time
import traceback
from typing import Dict, List

import streamlit as st
from deep_translator import MyMemoryTranslator
from docx import Document

# --------------------------------------------------------------------------- #
# Configuração da página e constantes
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="DocTranslate",
    page_icon="🌐",
    layout="centered",
)

PAUSA_ENTRE_CHAMADAS = 1.0
MAX_TENTATIVAS = 3
LIMITE_CARACTERES = 480

# --------------------------------------------------------------------------- #
# Carregamento de Idiomas Suportados (Lista Oficial MyMemory)
# --------------------------------------------------------------------------- #

@st.cache_data(show_spinner=False)
def carregar_todos_idiomas() -> Dict[str, str]:
    """Retorna o dicionário com a lista oficial de códigos regionais
    e idiomas suportados pelo servidor do MyMemoryTranslator.
    """
    idiomas_validos = {
        "af-ZA": "Afrikaans", "ak-GH": "Akan", "sq-AL": "Albanian", "am-ET": "Amharic",
        "ar-SA": "Arabic (Saudi Arabia)", "ar-EG": "Arabic (Egypt)", "hy-AM": "Armenian",
        "as-IN": "Assamese", "az-AZ": "Azerbaijani", "bm-ML": "Bambara", "ba-RU": "Bashkir",
        "eu-ES": "Basque", "be-BY": "Belarusian", "bn-IN": "Bengali", "bho-IN": "Bhojpuri",
        "bs-BA": "Bosnian", "br-FR": "Breton", "bg-BG": "Bulgarian", "my-MM": "Burmese",
        "ca-ES": "Catalan", "ceb-PH": "Cebuano", "ny-MW": "Chichewa", "zh-CN": "Chinese (Simplified)",
        "zh-TW": "Chinese (Traditional)", "hr-HR": "Croatian", "cs-CZ": "Czech", "da-DK": "Danish",
        "nl-NL": "Dutch", "en-US": "English (US)", "en-GB": "English (UK)", "en-CA": "English (Canada)",
        "en-AU": "English (Australia)", "eo-EU": "Esperanto", "et-EE": "Estonian", "ee-GH": "Ewe",
        "fil-PH": "Filipino", "fi-FI": "Finnish", "fr-FR": "French", "fr-BE": "French (Belgium)",
        "fr-CA": "French (Canada)", "gl-ES": "Galician", "lg-UG": "Ganda", "ka-GE": "Georgian",
        "de-DE": "German", "el-GR": "Greek", "gn-PY": "Guarani", "gu-IN": "Gujarati",
        "ht-HT": "Haitian Creole", "ha-NG": "Hausa", "haw-US": "Hawaiian", "he-IL": "Hebrew",
        "hi-IN": "Hindi", "hmn-CN": "Hmong", "hu-HU": "Hungarian", "is-IS": "Icelandic",
        "ig-NG": "Igbo", "id-ID": "Indonesian", "ga-IE": "Irish", "it-IT": "Italian",
        "ja-JP": "Japanese", "jv-ID": "Javanese", "kn-IN": "Kannada", "kk-KZ": "Kazakh",
        "km-KH": "Khmer", "rw-RW": "Kinyarwasa", "ko-KR": "Korean", "ku-TR": "Kurdish",
        "ky-KG": "Kyrgyz", "lo-LA": "Lao", "la-VA": "Latin", "lv-LV": "Latvian",
        "ln-CD": "Lingala", "lt-LT": "Lithuanian", "lb-LU": "Luxembourgish", "mk-MK": "Macedonian",
        "mg-MG": "Malagasy", "ms-MY": "Malay", "ml-IN": "Malayalam", "mt-MT": "Maltese",
        "mi-NZ": "Maori", "mr-IN": "Marathi", "mn-MN": "Mongolian", "ne-NP": "Nepali",
        "no-NO": "Norwegian", "or-IN": "Oriya", "om-ET": "Oromo", "ps-AF": "Pashto",
        "fa-IR": "Persian", "pl-PL": "Polish", "pt-PT": "Portuguese (Portugal)", "pt-BR": "Portuguese (Brazil)",
        "pa-IN": "Punjabi", "qu-PE": "Quechua", "ro-RO": "Romanian", "ru-RU": "Russian",
        "sm-WS": "Samoan", "gd-GB": "Scots Gaelic", "sr-RS": "Serbian", "st-LS": "Sesotho",
        "sn-ZW": "Shona", "sd-PK": "Sindhi", "si-LK": "Sinhala", "sk-SK": "Slovak",
        "sl-SI": "Slovenian", "so-SO": "Somali", "es-ES": "Spanish (Spain)", "es-MX": "Spanish (Mexico)",
        "su-ID": "Sundanese", "sw-TZ": "Swahili", "sv-SE": "Swedish", "tg-TJ": "Tajik",
        "ta-IN": "Tamil", "tt-RU": "Tatar", "te-IN": "Telugu", "th-TH": "Thai",
        "ti-ET": "Tigrinya", "ts-ZA": "Tsonga", "tr-TR": "Turkish", "tk-TM": "Turkmen",
        "uk-UA": "Ukrainian", "ur-PK": "Urdu", "ug-CN": "Uyghur", "uz-UZ": "Uzbek",
        "vi-VN": "Vietnamese", "cy-GB": "Welsh", "xh-ZA": "Xhosa", "yi-US": "Yiddish",
        "yo-NG": "Yoruba", "zu-ZA": "Zulu"
    }
    # Ordena alfabeticamente pelo nome do idioma para facilitar a busca do usuário
    return dict(sorted(idiomas_validos.items(), key=lambda item: item[1]))

IDIOMAS_SUPORTADOS = carregar_todos_idiomas()

def validar_idiomas(origem: str, destino: str) -> bool:
    """Confere se os códigos escolhidos existem na lista suportada."""
    if origem not in IDIOMAS_SUPORTADOS or destino not in IDIOMAS_SUPORTADOS:
        st.error("Um dos códigos de idioma selecionados não é reconhecido pelo servidor.")
        return False
    return True

# --------------------------------------------------------------------------- #
# Divisão de texto longo
# --------------------------------------------------------------------------- #

def dividir_em_blocos(texto: str, limite: int = LIMITE_CARACTERES) -> List[str]:
    if len(texto) <= limite:
        return [texto]

    frases = re.split(r"(?<=[.!?])\s+", texto)
    blocos: List[str] = []
    atual = ""

    for frase in frases:
        candidato = f"{atual} {frase}".strip() if atual else frase
        if len(candidato) <= limite:
            atual = candidato
        else:
            if atual:
                blocos.append(atual)
            if len(frase) <= limite:
                atual = frase
            else:
                for i in range(0, len(frase), limite):
                    blocos.append(frase[i : i + limite])
                atual = ""

    if atual:
        blocos.append(atual)

    return blocos

# --------------------------------------------------------------------------- #
# Tradução
# --------------------------------------------------------------------------- #

def traduzir_bloco(texto: str, tradutor: MyMemoryTranslator, cache: Dict[str, str]) -> str:
    if texto in cache:
        return cache[texto]

    espera = 2
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            time.sleep(PAUSA_ENTRE_CHAMADAS)
            resultado = tradutor.translate(texto)
        except Exception as erro:
            nome = type(erro).__name__
            print(f"[{nome}] tentativa {tentativa}/{MAX_TENTATIVAS}: {erro}")

            if tentativa < MAX_TENTATIVAS:
                time.sleep(espera)
                espera *= 2
                continue

            traceback.print_exc()
            st.warning(f"Falha após {MAX_TENTATIVAS} tentativas — {nome}: {erro}")
            cache[texto] = texto
            return texto
        else:
            resultado = resultado if resultado else texto
            cache[texto] = resultado
            return resultado

    return texto

def traduzir_texto(texto: str, tradutor: MyMemoryTranslator, cache: Dict[str, str]) -> str:
    blocos = dividir_em_blocos(texto)
    traduzidos = [traduzir_bloco(bloco, tradutor, cache) for bloco in blocos]
    return " ".join(traduzidos)

def traduzir_paragrafo(paragrafo, tradutor: MyMemoryTranslator, cache: Dict[str, str]) -> None:
    texto_original = paragrafo.text
    if not texto_original.strip():
        return

    if not paragrafo.runs:
        return

    texto_traduzido = traduzir_texto(texto_original, tradutor, cache)
    
    # CORREÇÃO: Aplica o texto ao primeiro elemento da lista de runs
    paragrafo.runs[0].text = texto_traduzido
    for run in paragrafo.runs[1:]:
        run.text = ""


def traduzir_documento(arquivo, idioma_origem: str, idioma_destino: str) -> io.BytesIO:
    documento = Document(arquivo)
    tradutor = MyMemoryTranslator(source=idioma_origem, target=idioma_destino)
    cache: Dict[str, str] = {}

    paragrafos = list(documento.paragraphs)

    for tabela in documento.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                paragrafos.extend(celula.paragraphs)

    for secao in documento.sections:
        paragrafos.extend(secao.header.paragraphs)
        paragrafos.extend(secao.footer.paragraphs)

    total = len(paragrafos)
    barra = st.progress(0.0, text="Preparando...")

    for indice, paragrafo in enumerate(paragrafos, start=1):
        traduzir_paragrafo(paragrafo, tradutor, cache)
        barra.progress(indice / total, text=f"Parágrafo {indice} de {total}")

    barra.empty()

    buffer = io.BytesIO()
    documento.save(buffer)
    buffer.seek(0)
    return buffer

# --------------------------------------------------------------------------- #
# Interface — barra lateral
# --------------------------------------------------------------------------- #

st.sidebar.title("⚙️ Configurações")

codigos_lista = list(IDIOMAS_SUPORTADOS.keys())
idx_origem = codigos_lista.index("en-US") if "en-US" in codigos_lista else 0
idx_destino = codigos_lista.index("pt-PT") if "pt-PT" in codigos_lista else 0

idioma_origem = st.sidebar.selectbox(
    "Idioma de origem",
    options=codigos_lista,
    format_func=lambda codigo: IDIOMAS_SUPORTADOS[codigo],
    index=idx_origem,
)

idioma_destino = st.sidebar.selectbox(
    "Idioma de destino",
    options=codigos_lista,
    format_func=lambda codigo: IDIOMAS_SUPORTADOS[codigo],
    index=idx_destino,
)

st.sidebar.caption(f"Códigos na API: origem=`{idioma_origem}`, destino=`{idioma_destino}`")

st.sidebar.divider()
st.sidebar.subheader("🔍 Diagnóstico")

if st.sidebar.button("Testar conexão com a API", use_container_width=True):
    try:
        saida = MyMemoryTranslator(source="en-US", target="pt-PT").translate("Hello world")
        st.sidebar.success(f"Resposta da API: {saida!r}")
    except Exception as erro:
        st.sidebar.error(f"{type(erro).__name__}: {erro}")

# --------------------------------------------------------------------------- #
# Interface — tela principal
# --------------------------------------------------------------------------- #

st.title("🌐 DocTranslate")
st.write("Traduza documentos do Word mantendo o layout e a formatação originais.")

arquivo_enviado = st.file_uploader(
    "Selecione um documento",
    type=["docx"],
    help="Apenas arquivos .docx são aceitos.",
)

if arquivo_enviado is not None:
    st.success(f"Arquivo carregado: **{arquivo_enviado.name}**")

    if idioma_origem == idioma_destino:
        st.warning("O idioma de origem e o de destino são iguais. Escolha idiomas diferentes.")

    # O botão de tradução agora executa toda a lógica corretamente
    if st.button("Traduzir", type="primary", use_container_width=True):
        if validar_idiomas(idioma_origem, idioma_destino):
            try:
                documento_traduzido = traduzir_documento(
                    arquivo_enviado,
                    idioma_origem,
                    idioma_destino,
                )
            except Exception as erro:
                traceback.print_exc()
                st.error(f"Erro ao processar o documento: {type(erro).__name__}: {erro}")
            else:
                # Salva o resultado no estado da sessão para não perder após o clique do download
                st.session_state["documento_traduzido"] = documento_traduzido.getvalue()
                st.session_state["nome_arquivo"] = f"traduzido_{arquivo_enviado.name}"
                st.success("Tradução concluída.")

    # Se o documento já foi traduzido, exibe o botão de download permanentemente
    if "documento_traduzido" in st.session_state:
        st.download_button(
            label="⬇️ Baixar documento traduzido",
            data=st.session_state["documento_traduzido"],
            file_name=st.session_state["nome_arquivo"],
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
else:
    # Limpa o estado se o usuário remover o arquivo para evitar downloads antigos
    if "documento_traduzido" in st.session_state:
        del st.session_state["documento_traduzido"]
    st.info("Envie um arquivo .docx para começar.")
