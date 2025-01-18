import pyaudio
from pynput import keyboard
import subprocess
import os

from src.spritely.utils.user_settings import settings, save_settings
from src.spritely.utils.logging import setup_logging

# Initialize logger
logger = setup_logging(__name__)

# Audio constants
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024

def open_accessibility_settings():
    subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'])
    print("Please enable accessibility permissions for your application")

def select_microphone():
    """Allow user to select microphone and save preference"""
    audio = pyaudio.PyAudio()
    
    # Get all input devices
    input_devices = []
    print("\n🎤 Available Input Devices:")
    for i in range(audio.get_device_count()):
        dev_info = audio.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:  # Only show input devices
            input_devices.append((i, dev_info))
            print(f"{len(input_devices)}. {dev_info['name']}")
            print(f"    Channels: {dev_info['maxInputChannels']}")
            print(f"    Sample Rate: {dev_info['defaultSampleRate']}")
    
    # Get default device info
    default_device = audio.get_default_input_device_info()
    print(f"\n🎯 Default Device: {default_device['name']}")
    
    # Show current setting if exists
    if settings['microphone_index'] is not None:
        try:
            current_device = audio.get_device_info_by_index(settings['microphone_index'])
            print(f"📌 Current Setting: {current_device['name']}")
        except:
            print("⚠️ Previously saved device not found")
    
    # Get user selection
    while True:
        choice = input("\nSelect microphone (0 for default, or number from list above): ")
        if choice.strip() == "0":
            settings['microphone_index'] = None
            break
        try:
            index = int(choice) - 1
            if 0 <= index < len(input_devices):
                settings['microphone_index'] = input_devices[index][0]
                break
            else:
                print("❌ Invalid selection. Please try again.")
        except ValueError:
            print("❌ Please enter a number.")
    
    # Save selection
    save_settings()
    audio.terminate()
    return settings['microphone_index']

def check_permissions():
    logger.info("Checking permissions...")
    # Check microphone
    try:
        audio = pyaudio.PyAudio()
        
        # Allow user to select microphone
        mic_index = select_microphone()
        
        # Test selected microphone
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=mic_index,
            frames_per_buffer=CHUNK
        )
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("✅ Microphone permission granted")
    except Exception as e:
        print("❌ Microphone permission error:", e)
        return False
    
    # Check Deepgram API key
    if not os.getenv('DEEPGRAM_API_KEY'):
        print("❌ Deepgram API key not found in .env file")
        return False
    print("✅ Deepgram API key found")

    # Check accessibility (will raise exception if not granted)
    try:
        with keyboard.Listener(on_press=lambda k: None) as listener:
            listener.stop()
        print("✅ Accessibility permission granted")
    except Exception as e:
        print("❌ Accessibility permission error:", e)
        print("Please enable accessibility permissions for your terminal/Python")
        open_accessibility_settings()
        return False

    return True 