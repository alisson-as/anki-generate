import pandas as pd
from gtts import gTTS
import genanki
import os
import random
import streamlit as st

def generate_audio(text, lang, output_file):
    """Gera um arquivo de áudio para um texto."""
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_file)


def create_anki_card(english_text, portuguese_text, english_audio, model_id):
    """Cria um card do Anki com texto em português no verso e áudio em inglês."""
    my_model = genanki.Model(
        model_id,
        "Simple English-Portuguese with Audio",
        fields=[
            {"name": "English"},
            {"name": "Portuguese"},
            {"name": "English Audio"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{English}}<br>{{English Audio}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Portuguese}}",
            },
        ],
    )

    note = genanki.Note(
        model=my_model,
        fields=[
            english_text,
            portuguese_text,
            f"[sound:{english_audio}]",
        ],
    )
    return note


def create_anki_package(cards, output_apkg, media_files):
    """Cria um pacote do Anki (.apkg)."""
    my_deck = genanki.Deck(
        deck_id=random.randrange(1 << 30, 1 << 31), name="English-Portuguese Vocabulary"
    )
    for card in cards:
        my_deck.add_note(card)

    package = genanki.Package(my_deck, media_files=media_files)
    package.write_to_file(output_apkg)


def process_excel_and_create_apkg(excel_file):
    """Processa o arquivo Excel e gera o arquivo .apkg."""
    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{excel_file.name}' não foi encontrado.")
        return None

    # Verifica se a coluna necessária existe no arquivo
    if "English" not in df.columns or "Portuguese" not in df.columns:
        st.error(
            "Erro: O arquivo Excel deve conter as colunas 'English' e 'Portuguese'."
        )
        return None

    cards = []
    media_files = []
    audio_files_to_remove = []  # Lista para armazenar os nomes dos arquivos a serem removidos
    for index, row in df.iterrows():
        english_text = row["English"]
        portuguese_text = row["Portuguese"]
        english_audio_file = f"english_{index}_{english_text.replace(' ', '_')}.mp3"
        
        # Gerar arquivos de audio
        generate_audio(english_text, "en", english_audio_file)
            
        # Obter o caminho completo do arquivo
        full_audio_path = os.path.abspath(english_audio_file)

        # Adicionar os arquivos a lista de mídia com caminho absoluto
        media_files.append(full_audio_path)
        audio_files_to_remove.append(english_audio_file)
       
        # Criar o card
        model_id = random.randrange(1 << 30, 1 << 31)
        card = create_anki_card(
            english_text, portuguese_text, english_audio_file, model_id
        )
        cards.append(card)
        

    # Gerar nome do arquivo .apkg
    file_name_without_extension = os.path.splitext(excel_file.name)[0]
    output_apkg = f"{file_name_without_extension}.apkg"

    # Criar pacote do Anki
    create_anki_package(cards, output_apkg, media_files)

    # Remover arquivos de audio temporarios após criar o pacote
    for audio_file in audio_files_to_remove:
         if os.path.exists(audio_file):
             os.remove(audio_file)
             
    return output_apkg


if __name__ == "__main__":
    st.title("Anki Card Generator from Excel")

    uploaded_file = st.file_uploader("Carregue o seu arquivo Excel", type=["xlsx"])

    if uploaded_file is not None:
        if st.button("Gerar Arquivo .apkg"):
            with st.spinner("Processando..."):
                apkg_file = process_excel_and_create_apkg(uploaded_file)

            if apkg_file:
                st.success("Arquivo .apkg criado com sucesso!")

                with open(apkg_file, "rb") as f:
                    st.download_button(
                        label="Download .apkg",
                        data=f,
                        file_name=apkg_file,
                        mime="application/octet-stream",
                    )
            else:
                st.error(
                    "Ocorreu um erro durante o processamento. Verifique o arquivo excel."
                )