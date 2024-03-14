# author:nerako
# This program is used to synthesize speech
# -----------------------2024.2.16-------------------------

import pyttsx3
import multiprocessing
import keyboard


class TTS:
    def __init__(self):
        self.engine = pyttsx3.init()
        # base set
        rate = self.engine.getProperty('rate')
        self.engine.setProperty('rate', 150)

        volume = self.engine.getProperty('volume')
        self.engine.setProperty('volume', 1.0)

        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)
        print("TTS engine is ready!")

    def speak(self,text):
        a = self.engine.say(text)
        self.engine.runAndWait()
        self.engine.stop()

    def sayFunc(self, phrase):
        #engine = pyttsx3.init()
        #self.engine.setProperty('rate', 160)
        self.engine.say(phrase)
        self.engine.runAndWait()

    def say_words(self, phrase):
        #if __name__ == "__main__":
        print('did it work?')
        p = multiprocessing.Process(target=self.sayFunc, args=(phrase,))
        p.start()
        while p.is_alive():
            print('while activated')
            if keyboard.is_pressed('q'):
                p.terminate()
            else:
                continue
        p.join()
        #self.engine.stop()

    def save(self):
        self.engine.save_to_file('words', filename='filename', name='name')
        self.engine.runAndWait()

# if __name__ == '__main__':
#     NEW_TTS = TTS()
#     NEW_TTS.speak("Conversational Agents and Spoken Language Processing")