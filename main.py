from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

class ParrotApp(App):
    def build(self):
        self.title = "Умный Попугай"
        
        # Экран телефона
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        # Текст, который покажет, что понял телефон
        self.label = Label(
            text="Нажми кнопку и говори!", 
            font_size='22sp',
            text_size=(400, None),
            halign='center',
            size_hint_y=0.6
        )
        layout.add(self.label)
        
        # Кнопка включения микрофона
        self.btn = Button(
            text="Включить микрофон", 
            background_color=(0.2, 0.8, 0.2, 1), # Зелёная кнопка
            font_size='24sp',
            size_hint_y=0.4
        )
        self.btn.bind(on_press=self.start_listening)
        layout.add(self.btn)
        
        # Инициализируем Android-инструменты речи
        self.speech_recognizer = None
        self.tts = None
        Clock.schedule_once(self.init_android_services, 1)
            
        return layout

    def init_android_services(self, dt):
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            
            # Настройка TTS (вывод речи)
            Locale = autoclass('java.util.Locale')
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            self.tts = TextToSpeech(App.get_running_app().activity, None)
            self.tts.setLanguage(Locale("ru"))
            
            # Настройка распознавания речи (ввод речи)
            Intent = autoclass('android.content.Intent')
            RecognizerIntent = autoclass('android.speech.RecognizerIntent')
            SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
            
            self.recognizer_intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            self.recognizer_intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            self.recognizer_intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ru-RU")
            
            # Создаем слушатель для Android
            class SpeechListener(PythonJavaClass):
                __javainterfaces__ = ['android/speech/RecognitionListener']
                
                def __init__(self, app_instance):
                    super(SpeechListener, self).__init__()
                    self.app = app_instance
                    
                @java_method('([Ljava/lang/String;)v')
                def onResults(self, results):
                    matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    if matches and matches.size() > 0:
                        text = matches.get(0)
                        self.app.process_speech(text)
                        
                @java_method('(I)v')
                def onError(self, error):
                    self.app.label.text = "Не расслышал, попробуй ещё раз..."
                    
                # Пустые обязательные методы интерфейса Android
                @java_method('()v')
                def onReadyForSpeech(self): pass
                @java_method('()v')
                def onBeginningOfSpeech(self): pass
                @java_method('(F)v')
                def onRmsChanged(self, rmsdB): pass
                @java_method('([B)v')
                def onBufferReceived(self, buffer): pass
                @java_method('()v')
                def onEndOfSpeech(self): pass
                @java_method('(ILandroid/os/Bundle;)v')
                def onPartialResults(self, partialResults): pass
                @java_method('(ILandroid/os/Bundle;)v')
                def onEvent(self, eventType, params): pass

            self.recognizer = SpeechRecognizer.createSpeechRecognizer(App.get_running_app().activity)
            self.recognizer.setRecognitionListener(SpeechListener(self))
            
        except Exception as e:
            print("Сервисы Android недоступны на ПК:", e)

    def start_listening(self, instance):
        if hasattr(self, 'recognizer') and self.recognizer:
            self.label.text = "Слушаю тебя..."
            self.recognizer.startListening(self.recognizer_intent)
        else:
            self.label.text = "На ПК микрофон не запустится.\nСобери APK для телефона!"

    def process_speech(self, text):
        # Показываем текст на экране телефона
        self.label.text = f"Ты сказала:\n\"{text}\""
        # Телефон повторяет этот текст вслух голосом
        if self.tts:
            self.tts.speak(text, 0, None, None)

if __name__ == '__main__':
    ParrotApp().run()