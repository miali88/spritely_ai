# Spritely AI 🧚🏼‍♀️ ✨ 🎙️
> Free humanity from the keyboard - Your AI-powered voice companion

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

Spritely AI is a powerful desktop application that enables real-time audio transcription with AI analysis. It combines local audio processing with cloud-based AI to provide a seamless voice-to-text experience.

This repository is the desktop app and the web app is available at [https://spritelyai.com]
## 🌟 Features

### Desktop App
- Real-time audio transcription using Deepgram's Nova-2 model
- Multiple transcription modes:
  - Direct field input (Cmd+Alt+L)
  - AI-analyzed input (Cmd+Alt+K)
- Speaker diarization support
- System-wide keyboard shortcuts
- Local audio processing for privacy
- Automatic microphone selection and configuration

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- MacOS (Windows support coming soon)

### Desktop App Setup

1. Clone the repository:
```bash
git clone https://github.com/spritelyai/spritely-ai.git
```

2. Install dependencies:
```bash
cd spritely-ai
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
touch .env
# add your api keys to .env
```

3. Run the app:
```bash
python main.py
```


## 🎯 Usage

### Desktop Shortcuts
- `Cmd+Alt+K`: Start/stop AI-analyzed transcription
- `Cmd+Alt+L`: Start/stop direct field transcription
- `ESC`: Stop current transcription

### Permissions
The app requires:
- Microphone access
- Accessibility permissions (for keyboard shortcuts)
- Internet connection (for AI analysis)

## 🏗️ Architecture

### Desktop App Components
- Audio Capture: PyAudio
- Transcription: Deepgram SDK
- Voice Synthesis: Cartesia
- Keyboard Control: pynput

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Deepgram](https://deepgram.com/) for real-time transcription
- [Cartesia](https://cartesia.io/) for voice synthesis
- All our contributors and supporters
