import streamlit as st
import openai
import pytesseract
from PIL import Image
import pdfplumber
import requests
from bs4 import BeautifulSoup
import urllib.parse
import io
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Keys
openai.api_key = "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"

pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

st.set_page_config(page_title="GenAI Search", layout="wide")

# App Title
st.title("🔎 GenAI Search — Smart Info Finder from Text, Links, Images & PDFs")
st.markdown("Get intelligent summaries and related links from any kind of input.")

# Session state
for key in ["history", "favorites"]:
    if key not in st.session_state:
        st.session_state[key] = []

# Sidebar Controls
with st.sidebar:
    st.header("🔍 Input Settings")
    input_type = st.selectbox("Input Type", ["Text", "Link", "Image", "PDF"])
    search_engine = st.selectbox("Search Engine", ["DuckDuckGo", "Google (Mock)"])
    temperature = st.slider("AI Creativity (Temperature)", 0.0, 1.0, 0.7)
    show_summary = st.checkbox("Summarize Response", value=True)
    st.markdown("### 🌐 Translation")
    translate = st.checkbox("Translate Output")
    if translate:
        target_language = st.selectbox("Select Language", ["Hindi", "French", "Tamil", "Spanish", "German"])
    st.markdown("---")
    if st.button("Clear Session"):
        st.session_state.history.clear()
        st.session_state.favorites.clear()
        st.experimental_rerun()

# Text Extraction
def extract_text_from_image(img):
    return pytesseract.image_to_string(img)

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Search Results
def get_search_links(query, max_results=3):
    if search_engine == "DuckDuckGo":
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
        return [(a.text.strip(), a.get("href")) for a in soup.find_all("a", class_="result__a", limit=max_results)]
    else:
        # Mock Google-style results
        return [
            (f"Google Result 1 for {query}", "https://example.com/1"),
            (f"Google Result 2 for {query}", "https://example.com/2"),
            (f"Google Result 3 for {query}", "https://example.com/3"),
        ]

# Summarize

def summarize_output(text):
    prompt = f"Summarize the following in bullet points:\n\n{text}"
    summary = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return summary.choices[0].message.content

# Translate Output

def translate_output(text, language):
    prompt = f"Translate the following into {language}:\n\n{text}"
    translation = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return translation.choices[0].message.content

# Word Cloud

def display_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)

# Input Handling
user_input = ""
if input_type == "Text":
    user_input = st.text_area("Enter your query")
elif input_type == "Link":
    user_input = st.text_input("Paste a link")
elif input_type == "Image":
    img_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if img_file:
        img = Image.open(img_file)
        st.image(img, width=300)
        user_input = extract_text_from_image(img)
elif input_type == "PDF":
    pdf_file = st.file_uploader("Upload PDF", type="pdf")
    if pdf_file:
        user_input = extract_text_from_pdf(pdf_file)

# Run GenAI
if st.button("🚀 Run GenAI") and user_input.strip():
    with st.spinner("Thinking..."):
        prompt = f"Act as an intelligent search engine. Provide helpful and organized info about: {user_input}"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            output = response.choices[0].message.content
            st.subheader("🧠 GenAI Output")
            st.write(output)

            # Summary (optional)
            if show_summary:
                st.markdown("### 📝 Summary")
                summary_text = summarize_output(output)
                st.write(summary_text)

                # Word Cloud
                st.markdown("### 📊 Visual Summary (Word Cloud)")
                display_wordcloud(summary_text)

                # Translation
                if translate:
                    st.markdown(f"### 🌐 Translated Summary ({target_language})")
                    translated_summary = translate_output(summary_text, target_language)
                    st.write(translated_summary)

            # Save to history
            st.session_state.history.append(("Search", user_input, output))

            # Related Links
            st.markdown("### 🔗 Related Links")
            for title, link in get_search_links(user_input):
                st.markdown(f"- [{title}]({link})")

            # Download
            buffer = io.StringIO()
            buffer.write(output)
            st.download_button("📥 Download Result", buffer.getvalue(), file_name="genai_output.txt")

            # Favorite
            if st.button("⭐ Save to Favorites"):
                st.session_state.favorites.append(("Search", user_input, output))
                st.success("Saved to favorites!")

        except Exception as e:
            st.error(f"Error: {e}")

# Show History
if st.session_state.history:
    st.markdown("---")
    st.subheader("📜 Search History")
    for m, q, o in reversed(st.session_state.history[-5:]):
        with st.expander(f"{m}: {q[:40]}..."):
            st.write(o)

# Favorites
if st.session_state.favorites:
    st.markdown("---")
    st.subheader("📌 Favorites")
    for i, (m, q, o) in enumerate(st.session_state.favorites):
        with st.expander(f"{i+1}. {m}: {q[:40]}..."):
            st.write(o)
