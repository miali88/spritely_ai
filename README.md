# Spritely AI 🧚🏼‍♀️ ✨ 🎙️
> Free humanity from the keyboard - Your AI-powered voice companion

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

Spritely AI is a powerful desktop application that enables real-time audio transcription with AI analysis. It combines local audio processing with cloud-based AI to provide a seamless voice-to-text experience.

![Spritely AI App UI](https://spritelyai.com/app_ui.png)

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


### 🗺️ Roadmap
- Always-on listening mode with wake word detection. See local STT. 
- Create a md file for database. Use an LLM instead of vector similarity search. Code example:
[text](https://small-limit-60e.notion.site/Using-an-LLM-agent-instead-of-vector-search-for-IR-18353e390487801cb447cb2eb111a18f)
- Add meeting summaries to md file.
- Polish the tkinter UI, i.e for meeting summary and transcription.
- Add Greptile API to tools.


### Bug Fixes
- Spritely's spoken output cuts off without completing the LLMs entire response

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- MacOS (Windows support coming soon)
- API keys for the following services
  - Elevenlabs account
  - Deepgram
  - Groq
  - Anthropic
- You will need to give keystroke permissions to the app for the shortcuts


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

This project is licensed under the AGPL-3.0 for non-commercial use.

Commercial Use
For commercial use or deployments requiring a setup fee, please contact us for a commercial license at michael@flowon.ai.

By using this software, you agree to the terms of the license.

## 🙏 Acknowledgments

- [Deepgram](https://deepgram.com/) for real-time transcription
- [Cartesia](https://cartesia.io/) for voice synthesis
- All our contributors and supporters
