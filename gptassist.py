import openai
import speech_recognition as sr
import pyttsx3
import playsound
import pyautogui
import rumps
import spacy


nlp = spacy.load("en_core_web_sm")

# Create context list
context = []

# Set up OpenAI API
openai.api_key = "YOUR_API_KEY"

# Initialize speech recognition
r = sr.Recognizer()

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Function to convert text to speech
def speak(text):
    engine.say(text)
    engine.runAndWait()


# Capture screenshot
def capture_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png")


# Analyze screenshot using OpenAI Vision
def analyze_screenshot():
    with open("screenshot.png", "rb") as file:
        image_data = file.read()
    response = openai.Vision.create(images=[image_data], model="davinci")
    analysis = response["images"][0]["objects"]
    return analysis

def get_intent(user_input):
    doc = nlp(user_input)
    intent = ""
    for token in doc:
        if token.pos_ == "VERB":
            intent = token.lemma_
            break
    return intent


# Collect user input
def get_user_input():
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = r.listen(source)
            text = r.recognize_google(audio)
            print("User: " + text)
            return text
        except sr.RequestError:
            speak("Sorry, I could not connect to the speech recognition service.")
            return ""
        except sr.UnknownValueError:
            speak("Sorry, I could not understand what you said.")
            return ""



# Send user input to OpenAI and get response
def get_assistant_response(user_input, analysis,intent):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input},
            {"role": "assistant", "context": analysis},
            {"role": "assistant", "context": intent}
        ],
    )
    assistant_response = response["choices"][0]["message"]["content"]
    return assistant_response


# Create rumps app
class MyApp(rumps.App):
    def __init__(self):
        super().__init__("My App")
        self.menu = [
            rumps.MenuItem("Ask", callback=self.capture_screenshot),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit),
        ]

    def capture_screenshot(self):
        capture_screenshot()
        analysis = analyze_screenshot()
        user_input = get_user_input()
        intent = get_intent(user_input)
        assistant_response = get_assistant_response(user_input, analysis,intent)
        speak(assistant_response)
        rumps.alert("Assistant: " + assistant_response)

    def quit(self, sender):
        rumps.quit_application()


if __name__ == "__main__":
    MyApp().run()
