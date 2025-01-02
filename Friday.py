import sys
import pyttsx3
import webbrowser
import cv2
import datetime
import requests
import speech_recognition as sr
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QWidget, QComboBox, QHBoxLayout, QScrollArea, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Thread for text-to-speech
class SpeakThread(QThread):
    finished = pyqtSignal()

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        engine = pyttsx3.init()
        engine.say(self.text)
        engine.runAndWait()
        self.finished.emit()

# Helper method for speech
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Helper function to get weather information
def get_weather(city):
    try:
        # Query the wttr.in service with the desired city
        url = f"https://wttr.in/{city}?format=%C+%t"
        response = requests.get(url)
        
        if response.status_code == 200:
            weather_info = response.text.strip()
            return f"The weather in {city} is {weather_info}."
        else:
            return "Could not retrieve weather information. Please try again."
    except requests.RequestException as e:
        return "I'm sorry, I couldn't fetch the weather data."

# Lists of movies, series, and anime by genre
MOVIES = {
    "action": ["Mad Max: Fury Road", "Die Hard", "The Dark Knight", "John Wick", "Gladiator"],
    "comedy": ["The Hangover", "Superbad", "Step Brothers", "Dumb and Dumber", "Anchorman"],
    "thriller": ["Inception", "The Sixth Sense", "Shutter Island", "Se7en", "Gone Girl"],
    "romance": ["The Notebook", "Titanic", "La La Land", "A Walk to Remember", "Pride and Prejudice"],
    "horror": ["The Conjuring", "It", "A Quiet Place", "The Shining", "Hereditary"]
}

SERIES = {
    "action": ["24", "Arrow", "The Witcher", "Stranger Things", "Prison Break"],
    "comedy": ["Friends", "The Office", "Parks and Recreation", "Brooklyn Nine-Nine", "How I Met Your Mother"],
    "thriller": ["Breaking Bad", "Mindhunter", "The Haunting of Hill House", "True Detective", "Narcos"],
    "romance": ["The Bachelor", "Bridgerton", "Outlander", "Grey's Anatomy", "Glee"],
    "horror": ["The Walking Dead", "American Horror Story", "Castle Rock", "The Strain", "Bates Motel"]
}

ANIME = {
    "action": ["Naruto", "Attack on Titan", "One Punch Man", "My Hero Academia", "Bleach"],
    "comedy": ["One Punch Man", "Gintama", "KonoSuba", "Saiki K", "Ouran High School Host Club"],
    "thriller": ["Death Note", "Tokyo Ghoul", "Steins;Gate", "Psycho-Pass", "Monster"],
    "romance": ["Your Name", "Toradora!", "Clannad", "Fruits Basket", "Kimi ni Todoke"],
    "horror": ["Tokyo Ghoul", "Another", "Higurashi", "Elfen Lied", "The Promised Neverland"]
}

class ChatBotUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

        # To-Do List
        self.todo_list = []
        self.dark_mode = True
        self.speak_thread = None  # Store the SpeakThread instance

    def init_ui(self):
        # Main window settings
        self.setWindowTitle("Friday Interactive Chatbot")
        self.setStyleSheet("background-color: #1A1A2E; color: #FFFFFF;")

        # Main layout
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        # Top left corner title
        title_label = QLabel("Friday Interactive Chatbot")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.main_layout.addWidget(title_label)

        # Chat area with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

        # To-Do List section
        self.todo_widget = QListWidget()
        self.todo_widget.setStyleSheet("background-color: #2C2C54; color: #FFFFFF; border-radius: 8px;")
        self.todo_widget.setFixedHeight(100)  # Adjusted height to make it smaller
        self.todo_widget.setFixedWidth(200)   # Adjusted width to make it smaller
        self.main_layout.addWidget(QLabel("To-Do List:"))
        self.main_layout.addWidget(self.todo_widget)


        # User input area and theme toggle button at the bottom
        input_layout = QHBoxLayout()
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here or type 'help' to see commands...")
        self.text_input.setFixedHeight(50)
        self.text_input.setStyleSheet("background-color: #2C2C54; color: #FFFFFF; border-radius: 8px;")

        send_button = QPushButton("Send")
        send_button.setStyleSheet("background-color: #6C5CE7; color: white; padding: 10px; border-radius: 8px;")
        send_button.clicked.connect(self.handle_message)

        voice_button = QPushButton("Voice Input")
        voice_button.setStyleSheet("background-color: #0984E3; color: white; padding: 10px; border-radius: 8px;")
        voice_button.clicked.connect(self.voice_input)

        theme_button = QPushButton("Toggle Theme")
        theme_button.setStyleSheet("background-color: #FF7675; color: white;padding: 10px; border-radius: 15px;")
        theme_button.clicked.connect(self.toggle_theme)

        input_layout.addWidget(self.text_input)
        input_layout.addWidget(send_button)
        input_layout.addWidget(voice_button)
        input_layout.addWidget(theme_button)

        self.main_layout.addLayout(input_layout)

        # Welcome message
        self.add_message("ChatBot", "Hello! How can I assist you today? type 'help' to see a list of commands.", bot=True)
        QTimer.singleShot(500, lambda: speak("Hello! How can I assist you today? type 'help' to see a list of commands."))

        # Make the window fullscreen
        self.showFullScreen()  # This will make the window open in fullscreen mode

    def add_message(self, sender, message, bot=False):
        msg_label = QLabel(f"{sender}: {message}")
        msg_label.setWordWrap(True)
        msg_label.setFont(QFont("Arial", 12))
        msg_label.setStyleSheet(f"background-color: {'#6C5CE7' if bot else '#00CEC9'}; color: white; padding: 20px; border-radius: 20px;")
        msg_label.setAlignment(Qt.AlignLeft if bot else Qt.AlignRight)
        self.scroll_layout.addWidget(msg_label)
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def handle_message(self):
        user_message = self.text_input.toPlainText().strip()
        if not user_message:
            return
        self.add_message("You", user_message)
        self.text_input.clear()
        response = self.process_command(user_message)
        self.add_message("ChatBot", response, bot=True)
        self.speak_in_thread(response)

    def process_command(self, message):
        message_lower = message.lower()
        try:
            if "suggest" in message_lower:
                # Get the genre from the user message
                genre = message_lower.split("suggest")[-1].strip()
                return self.suggest_media(genre)
            elif "time" in message_lower:
                now = datetime.datetime.now()
                return f"The current time is {now.strftime('%H:%M:%S')}."
            elif "date" in message_lower:
                today = datetime.date.today()
                return f"Today's date is {today.strftime('%B %d, %Y')}."
            elif "weather" in message_lower:
                city = message_lower.replace("weather in", "").strip()
                if city:
                    return get_weather(city)
                return "Please specify a city to get the weather."
            elif "calculate" in message_lower:
                return self.calculate(message_lower)
            elif "add task" in message_lower:
                task = message_lower.replace("add task", "").strip()
                if task:
                    self.todo_list.append(task)
                    self.todo_widget.addItem(QListWidgetItem(task))
                    return f"Task '{task}' added to your To-Do list."
                return "Please specify a task to add."
            elif "open camera" in message_lower:
                self.open_camera()
                return "Camera is now open. Press 'Q' to close."
            elif "search" in message_lower:
                query = message_lower.split("search")[-1].strip()
                if query:
                    webbrowser.open(f"https://www.google.com/search?q={query}")
                    return f"Searching Google for '{query}'."
                return "Please specify what to search for."
            elif "help" in message_lower:
                return "Here are some commands you can use:\n1. 'time' - to get the current time\n2. 'date' - to get today's date\n3. 'calculate [expression]' - to perform a calculation\n4. 'add task [task]' - to add a task to your To-Do list\n5. 'open camera' - to open the camera\n6. 'search [query]' - to search Google\n7. 'weather in [city]' - to get the weather in a specific city\n8. 'suggest [genre]' - to get media suggestions by genre."
            elif "exit" in message_lower:
                QApplication.quit()
                return "Goodbye!"
            return "I'm sorry, I didn't understand that. Please try again."
        except Exception as e:
            return f"An error occurred: {e}"

    def suggest_media(self, genre):
        genre = genre.lower()
        if genre in MOVIES:
            suggestions = MOVIES[genre] + SERIES.get(genre, []) + ANIME.get(genre, [])
            return f"Here are some suggestions for {genre}:\n" + "\n".join(suggestions)
        else:
            return "Sorry, I don't have suggestions for that genre."

    def calculate(self, message):
        try:
            expression = message.replace("calculate", "").strip()
            result = eval(expression)
            return f"The result is {result}."
        except Exception:
            return "Invalid calculation. Please try again."

    def voice_input(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.add_message("ChatBot", "Listening...", bot=True)
            try:
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio)
                self.add_message("You", text)
                response = self.process_command(text)
                self.add_message("ChatBot", response, bot=True)
                self.speak_in_thread(response)
            except sr.UnknownValueError:
                self.add_message("ChatBot", "Sorry, I could not understand that.", bot=True)
            except sr.RequestError:
                self.add_message("ChatBot", "Speech recognition service is unavailable.", bot=True)

    def open_camera(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow('Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("background-color: #1A1A2E; color: #FFFFFF;")
        else:
            self.setStyleSheet("background-color: #FFFFFF; color: #000000;")

    def speak_in_thread(self, text):
        if self.speak_thread and self.speak_thread.isRunning():
            self.speak_thread.terminate()
        self.speak_thread = SpeakThread(text)
        self.speak_thread.finished.connect(self.speak_thread_finished)
        self.speak_thread.start()

    def speak_thread_finished(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatBotUI()
    window.show()
    sys.exit(app.exec_())
