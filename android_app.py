from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivy.storage.jsonstore import JsonStore
import asyncio
import edge_tts
import os
import tempfile
from datetime import datetime
import threading

class TextToSpeechScreen(MDScreen):
    text_input = StringProperty("")
    is_converting = BooleanProperty(False)
    audio_file = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.voices = {
            "Aria (US)": "en-US-AriaNeural",
            "Jenny (US)": "en-US-JennyNeural", 
            "Guy (US)": "en-US-GuyNeural",
            "Emma (UK)": "en-GB-EmmaNeural",
            "Ryan (UK)": "en-GB-RyanNeural",
            "Sonia (Canada)": "en-CA-SoniaNeural",
            "Tony (Canada)": "en-CA-TonyNeural"
        }
        self.selected_voice = "en-US-AriaNeural"
        self.sound = None
        self.is_playing = False
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        main_layout = MDBoxLayout(
            orientation='vertical',
            spacing=20,
            padding=20
        )
        
        # Title
        title = MDLabel(
            text="Text to Speech",
            halign="center",
            theme_text_color="Primary",
            font_style="H4",
            size_hint_y=None,
            height=60
        )
        main_layout.add_widget(title)
        
        # Voice selection card
        voice_card = MDCard(
            size_hint_y=None,
            height=80,
            padding=15
        )
        
        voice_layout = MDBoxLayout(orientation='horizontal', spacing=10)
        voice_label = MDLabel(
            text="Voice:",
            theme_text_color="Secondary",
            size_hint_x=0.3
        )
        voice_layout.add_widget(voice_label)
        
        self.voice_button = MDRaisedButton(
            text="Aria (US)",
            on_release=self.show_voice_menu,
            size_hint_x=0.7
        )
        voice_layout.add_widget(self.voice_button)
        voice_card.add_widget(voice_layout)
        main_layout.add_widget(voice_card)
        
        # Text input card
        text_card = MDCard(
            size_hint_y=None,
            height=200,
            padding=15
        )
        
        text_layout = MDBoxLayout(orientation='vertical', spacing=10)
        text_label = MDLabel(
            text="Enter your text:",
            theme_text_color="Secondary"
        )
        text_layout.add_widget(text_label)
        
        self.text_field = MDTextField(
            multiline=True,
            hint_text="Type or paste your text here...",
            mode="rectangle",
            size_hint_y=None,
            height=120
        )
        text_layout.add_widget(self.text_field)
        text_card.add_widget(text_layout)
        main_layout.add_widget(text_card)
        
        # Convert button
        self.convert_button = MDRaisedButton(
            text="Convert to Speech",
            on_release=self.convert_text,
            size_hint_x=0.8,
            pos_hint={'center_x': 0.5}
        )
        main_layout.add_widget(self.convert_button)
        
        # Progress bar
        self.progress_bar = MDProgressBar(
            type="indeterminate",
            size_hint_x=0.8,
            pos_hint={'center_x': 0.5}
        )
        main_layout.add_widget(self.progress_bar)
        self.progress_bar.opacity = 0
        
        # Audio controls card
        self.audio_card = MDCard(
            size_hint_y=None,
            height=120,
            padding=15
        )
        
        audio_layout = MDBoxLayout(orientation='vertical', spacing=10)
        audio_label = MDLabel(
            text="Generated Audio:",
            theme_text_color="Secondary"
        )
        audio_layout.add_widget(audio_label)
        
        controls_layout = MDBoxLayout(orientation='horizontal', spacing=10)
        
        self.play_button = MDIconButton(
            icon="play",
            on_release=self.play_audio,
            theme_icon_color="Custom",
            icon_color=(0.2, 0.8, 0.2, 1)
        )
        controls_layout.add_widget(self.play_button)
        
        self.stop_button = MDIconButton(
            icon="stop",
            on_release=self.stop_audio,
            theme_icon_color="Custom",
            icon_color=(0.8, 0.2, 0.2, 1)
        )
        controls_layout.add_widget(self.stop_button)
        
        self.save_button = MDIconButton(
            icon="content-save",
            on_release=self.save_audio,
            theme_icon_color="Custom",
            icon_color=(0.9, 0.6, 0.1, 1)
        )
        controls_layout.add_widget(self.save_button)
        
        audio_layout.add_widget(controls_layout)
        self.audio_card.add_widget(audio_layout)
        main_layout.add_widget(self.audio_card)
        self.audio_card.opacity = 0
        
        # Add spacer
        spacer = MDBoxLayout()
        main_layout.add_widget(spacer)
        
        self.add_widget(main_layout)
        
    def show_voice_menu(self, instance):
        menu_items = [
            {
                "text": voice_name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=voice_name: self.select_voice(x),
            }
            for voice_name in self.voices.keys()
        ]
        
        self.voice_menu = MDDropdownMenu(
            caller=instance,
            items=menu_items,
            position="bottom",
            width_mult=2,
        )
        self.voice_menu.open()
        
    def select_voice(self, voice_name):
        self.selected_voice = self.voices[voice_name]
        self.voice_button.text = voice_name
        self.voice_menu.dismiss()
        
    def convert_text(self, instance):
        text = self.text_field.text.strip()
        if not text:
            self.show_dialog("Warning", "Please enter some text to convert.")
            return
            
        self.is_converting = True
        self.convert_button.disabled = True
        self.progress_bar.opacity = 1
        self.progress_bar.start()
        
        # Run conversion in separate thread
        thread = threading.Thread(target=self._convert_async, args=(text,))
        thread.daemon = True
        thread.start()
        
    def _convert_async(self, text):
        try:
            # Create temp file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_dir = tempfile.gettempdir()
            self.audio_file = os.path.join(temp_dir, f"tts_output_{timestamp}.mp3")
            
            # Run async conversion
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._generate_speech(text))
            loop.close()
            
            # Update UI in main thread
            Clock.schedule_once(lambda dt: self._conversion_complete())
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._conversion_error(str(e)))
            
    async def _generate_speech(self, text):
        communicate = edge_tts.Communicate(text, self.selected_voice)
        await communicate.save(self.audio_file)
        
    def _conversion_complete(self):
        self.is_converting = False
        self.convert_button.disabled = False
        self.progress_bar.opacity = 0
        self.progress_bar.stop()
        
        # Show audio controls
        self.audio_card.opacity = 1
        
        self.show_dialog("Success", "Text converted to speech successfully!")
        
    def _conversion_error(self, error_msg):
        self.is_converting = False
        self.convert_button.disabled = False
        self.progress_bar.opacity = 0
        self.progress_bar.stop()
        
        self.show_dialog("Error", f"Failed to convert text: {error_msg}")
        
    def play_audio(self, instance):
        if self.audio_file and os.path.exists(self.audio_file):
            try:
                if self.sound:
                    self.sound.stop()
                    self.sound.unload()
                    
                self.sound = SoundLoader.load(self.audio_file)
                if self.sound:
                    self.sound.play()
                    self.is_playing = True
                    self.play_button.icon = "pause"
            except Exception as e:
                self.show_dialog("Error", f"Failed to play audio: {str(e)}")
                
    def stop_audio(self, instance):
        if self.sound and self.is_playing:
            self.sound.stop()
            self.is_playing = False
            self.play_button.icon = "play"
            
    def save_audio(self, instance):
        if self.audio_file and os.path.exists(self.audio_file):
            # On Android, save to Downloads folder
            downloads_path = "/storage/emulated/0/Download"
            if not os.path.exists(downloads_path):
                downloads_path = tempfile.gettempdir()
                
            filename = f"tts_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            save_path = os.path.join(downloads_path, filename)
            
            try:
                import shutil
                shutil.copy2(self.audio_file, save_path)
                self.show_dialog("Success", f"Audio saved to: {save_path}")
            except Exception as e:
                self.show_dialog("Error", f"Failed to save audio: {str(e)}")
                
    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

class TextToSpeechApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        return TextToSpeechScreen()

if __name__ == "__main__":
    TextToSpeechApp().run() 