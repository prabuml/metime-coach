import streamlit as st
import io, os
import wave
from gtts import gTTS
import speech_recognition as sr
import google.generativeai as genai
import base64

def text_to_speech(text):
  """Converts text to speech using gTTS and returns an audio player."""
  tts = gTTS(text=text, lang='en')
  tts.save("response.mp3")
  audio_file = open('response.mp3', 'rb')
  audio_bytes = audio_file.read()
  st.audio(audio_bytes, format='audio/mp3')



def read_file_to_string(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "The file was not found."
    except IOError:
        return "An error occurred while reading the file."



file_path = 'system_prompt.txt'  # Replace with your file path
classification_system_prompt = read_file_to_string(file_path)

forgive_path = 'forgiveness_system_prompt.txt'
forgive_system_prompt = read_file_to_string(forgive_path)

confidence_path = 'confidence_system_prompt.txt'
confidence_system_prompt = read_file_to_string(confidence_path)

sleep_path = 'sleep_system_prompt.txt'
sleep_system_prompt = read_file_to_string(sleep_path)

dialy_path = 'dialy_planning_system_prompt.txt'
dialy_system_prompt = read_file_to_string(dialy_path)

# Fill google key
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

genai.configure(api_key=GOOGLE_API_KEY)
classification_model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', generation_config={"temperature": 0},
                              system_instruction=classification_system_prompt)

forgiveness_model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', generation_config=generation_config,
                              system_instruction=forgive_system_prompt)

confidence_model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', generation_config=generation_config,
                              system_instruction=confidence_system_prompt)

sleep_model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', generation_config=generation_config,
                              system_instruction=sleep_system_prompt)

dialy_model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest', generation_config=generation_config,
                              system_instruction=dialy_system_prompt)

classification_user_prompt = """
text: {text}  

class: "Unable to Sleep"/"Frustrated towards others"/"Having low confidence"/"Plan your day"/"None of the above"
"""

# Initialize chat history
messages = []
model = None

def save_audio(audio_bytes,file_name):
    audio_buffer = audio_bytes
    # Open a wave file
    with wave.open(audio_buffer, 'rb') as audio_file:
      # Extract audio parameters
      params = audio_file.getparams()
      audio_frames = audio_file.readframes(params.nframes)
  # Save the audio to a .wav file
    with wave.open(file_name, 'wb') as output_file:
      output_file.setparams(params)
      output_file.writeframes(audio_frames)

def transcribe_audio(audio_file):
  """
  Transcribes an audio file using the SpeechRecognition library.

  Args:
    audio_file: Path to the audio file.

  Returns:
    The transcribed text.
  """
  recognizer = sr.Recognizer()
  with sr.AudioFile(audio_file) as source:
    audio = recognizer.record(source)  # read the entire audio file  

  try:
    # Use Google Speech Recognition as the API
    text = recognizer.recognize_google(audio)
    return text
  except sr.UnknownValueError:
    return "Could not understand audio"
  except sr.RequestError as e:
    return f"Could not request results from Google Speech Recognition service; {e}"

loop=0

while audio_value := st.audio_input("Speak",key="key_"+str(loop)):
    save_audio(audio_value,"audio.wav")
    user_text = transcribe_audio("audio.wav")
    messages.append({"role": "user", "parts": [user_text]})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(user_text)

    if model == None:
        user_prompt = classification_user_prompt.format(text=user_text)
        output = classification_model.generate_content(user_prompt).text

        if "Frustrated towards others" in output:
            model = "Forgiveness"
            st.success("I am your Forgiveness coach")
        elif "Having low confidence" in output:
            model = "Confidence"
            st.success("I am your Confidence coach")
        elif "Unable to Sleep" in output:
            model = "Sleep"
            st.success("I am your Sleep coach")
        elif "Plan your day" in output:
            st.success("I am your Daily Planner coach")
            model = "Dialy"
    if model == "Forgiveness":
        convo = forgiveness_model.start_chat(history = messages)

        # Generate and display the model's response
        response = convo.send_message(user_text)
    elif model == "Confidence":
        convo = confidence_model.start_chat(history=messages)

        # Generate and display the model's response
        response = convo.send_message(user_text)
    elif model == "Sleep":
        convo = sleep_model.start_chat(history=messages)

        # Generate and display the model's response
        response = convo.send_message(user_text)
    elif model == "Dialy":
        convo = dialy_model.start_chat(history=messages)
        # Generate and display the model's response
        response = convo.send_message(user_text)

    if model:
        messages.append({"role": "model", "parts": [response.text]})

        with st.chat_message("assistant"):
            st.markdown(response.text)
        text_to_speech(response.text)
    loop = loop + 1


