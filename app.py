import streamlit as st
import whisper
import asyncio
import edge_tts
import os

# Voice map
voice_map = {
    "English": {
        "Female": "en-US-JennyNeural",
        "Male": "en-US-GuyNeural"
    },
    "Hindi": {
        "Female": "hi-IN-SwaraNeural",
        "Male": "hi-IN-MadhurNeural"
    }
}

style_options = ["Default", "cheerful", "sad", "angry"]

# Load Whisper
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

try:
    model = load_whisper_model()
    model_loaded = True
except Exception as e:
    st.error(f"Error loading Whisper model: {e}")
    model_loaded = False

# UI
st.title("🎙️ Emotion-Based Voice Generator")

uploaded_audio = st.file_uploader("Upload your voice file", type=["wav", "mp3"])

col1, col2 = st.columns(2)
with col1:
    lang = st.selectbox("Select Language", list(voice_map.keys()))
    gender = st.radio("Select Gender", ["Male", "Female"])
    style = st.selectbox("Select Emotion", style_options)

with col2:
    # Add voice fine-tuning controls
    rate = st.slider("Speech Rate", min_value=-50, max_value=50, value=0, 
                     help="Control how fast the speech is (negative: slower, positive: faster)")
    pitch = st.slider("Pitch", min_value=-50, max_value=50, value=0,
                     help="Control voice pitch (negative: lower, positive: higher)")
    volume = st.slider("Volume", min_value=-50, max_value=50, value=0,
                      help="Control volume (negative: quieter, positive: louder)")

# Format the values for edge-tts
rate_value = f"{rate}%" if rate >= 0 else f"{rate}%"
pitch_value = f"+{pitch}%" if pitch >= 0 else f"{pitch}%"
volume_value = f"+{volume}%" if volume >= 0 else f"{volume}%"

voice = voice_map[lang][gender]

if uploaded_audio is not None and model_loaded:
    with st.spinner("Processing audio..."):
        # Save uploaded file
        with open("input.wav", "wb") as f:
            f.write(uploaded_audio.read())

        st.audio("input.wav", format="audio/wav")

        # Transcribe the audio
        with st.spinner("Transcribing..."):
            result = model.transcribe("input.wav", language=lang[:2].lower())
            st.success("Transcription complete!")
            
            # Display transcribed text with editing option
            transcribed_text = result['text']
            edited_text = st.text_area("Edit transcribed text if needed:", transcribed_text, height=150)

    if st.button("Generate Emotional Speech"):
        output_file = "output.mp3"

        async def speak():
            try:
                # Create communicate object with the voice
                communicate = edge_tts.Communicate(edited_text, voice)
                
                # Apply fine-tuning parameters
                if rate != 0:
                    communicate.rate = rate_value
                if pitch != 0:
                    communicate.pitch = pitch_value
                if volume != 0:
                    communicate.volume = volume_value
                
                # Apply style if not default
                if style != "Default":
                    communicate.style = style
                    
                # Generate and save speech
                await communicate.save(output_file)
                return True
            except Exception as e:
                st.error(f"Error generating speech: {e}")
                return False

        with st.spinner("Generating emotional speech..."):
            success = asyncio.run(speak())
            
            if success:
                st.success("Speech generated successfully!")
                st.audio(output_file, format="audio/mp3")
                
                # Add download button
                with open(output_file, "rb") as file:
                    btn = st.download_button(
                        label="Download Audio",
                        data=file,
                        file_name="emotional_speech.mp3",
                        mime="audio/mp3"
                    )
            else:
                st.error("Failed to generate speech. Try different settings.")

# Display help information
with st.expander("Help & Information"):
    st.markdown("""
    ### How to use this app:
    1. Upload an audio file (WAV or MP3)
    2. Select the language and gender for the output voice
    3. Choose an emotion style
    4. Adjust fine-tuning settings:
       - **Rate**: Controls speech speed
       - **Pitch**: Adjusts voice pitch
       - **Volume**: Controls loudness
    5. Click "Generate Emotional Speech"
    
    ### Notes:
    - Not all voices support all emotion styles
    - Transcription quality depends on audio clarity
    - You can edit the transcribed text before generating speech
    """)