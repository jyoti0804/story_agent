import streamlit as st
from groq import Groq
import tempfile
from gtts import gTTS
import os
from dotenv import load_dotenv
import httpx

# --- Load .env ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found in .env file.")
    st.stop()

# --- Streamlit setup ---
st.set_page_config(page_title="🎭 FairyTale Live", page_icon="🧚")
st.title("🧚 FairyTale Live — Streaming Story with Audio")
st.write("✨ Watch your story appear paragraph by paragraph, then listen to the full story!")

# --- User Inputs ---
col1, col2 = st.columns(2)
with col1:
    characters_input = st.text_input("Characters (comma separated)", "Luna, Theo")
with col2:
    setting = st.text_input("Setting", "Enchanted Forest")

style = st.selectbox("Story Style", ["Magical", "Funny", "Dramatic", "Adventure"])

# --- Groq streaming function with timeout & error handling ---
def stream_story(prompt: str):
    client = Groq(api_key=GROQ_API_KEY, timeout=60)  # increase timeout to 60s
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.9,
            stream=True,
        )

        story_so_far = ""
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and getattr(delta, "content", None):
                story_so_far += delta.content
                yield story_so_far

    except httpx.ReadTimeout:
        yield "\n⚠️ Story generation timed out. Try a shorter prompt or increase timeout."

# --- gTTS audio function ---
def generate_audio(text: str):
    tts = gTTS(text=text, lang="en")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts.save(tmp.name)
        return tmp.name

# --- Generate Button ---
if st.button("✨ Generate Story"):
    with st.spinner("🧠 Groq is crafting your fairy tale..."):
        character_list = [c.strip() for c in characters_input.split(",") if c.strip()]
        prompt = f"""
        Create a short 5-minute fairy tale with:
        - Characters: {', '.join(character_list)}
        - Setting: {setting}
        - Style: {style}
        - Use dialogues with character names (e.g., Luna: "Hello!") 
        - Include magical sound cues like [forest sounds], [magic sparkle].
        Narrate in story style, paragraph by paragraph.
        """

        # Stream text live
        story_placeholder = st.empty()
        full_story = ""
        for partial_story in stream_story(prompt):
            story_placeholder.markdown(partial_story)
            full_story = partial_story  # keep latest

    # --- Generate audio for full story ---
    if full_story.strip():
        with st.spinner("🎙 Generating audio for full story..."):
            audio_path = generate_audio(full_story)
            st.subheader("🎧 Listen to the Story")
            st.audio(audio_path, format="audio/mp3")
