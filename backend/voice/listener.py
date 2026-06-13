import speech_recognition as sr
import pyttsx3
import webbrowser

engine = pyttsx3.init()

def speak(text):
    print(f"ASTRA: {text}")
    engine.say(text)
    engine.runAndWait()

speak("Hey Sanjeev, I am listening. How can I help you?")

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("Listening...")

    recognizer.adjust_for_ambient_noise(source)

    audio = recognizer.listen(source)

try:
    text = recognizer.recognize_google(audio)

    print(f"You: {text}")

    command = text.lower()

    if "youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")

    else:
        speak(f"You said {text}")

except Exception as e:
    print(e)
    speak("Sorry Sanjeev, I could not understand.")