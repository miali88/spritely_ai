# Spritely AI 🎙️✨
> Free humanity from the keyboard - Your AI-powered voice companion

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)

Spritely AI is a powerful desktop + web application that enables real-time audio transcription with AI analysis. It combines local audio processing with cloud-based AI to provide a seamless voice-to-text experience.

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

### Web App
- User authentication and account management
- Transcription history and analysis
- AI-powered insights and suggestions
- Cross-device synchronization
- Usage analytics and reporting

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- pnpm (recommended) or npm
- MacOS (Windows support coming soon)

### Desktop App Setup

.......


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

### Web App Stack
- Frontend: Next.js 14
- Authentication: Clerk
- Styling: Tailwind CSS
- Analytics: Vercel Analytics

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
- [Next.js](https://nextjs.org/) team for the web framework
- All our contributors and supporters
