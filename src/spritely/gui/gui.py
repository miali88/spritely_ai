import tkinter as tk
from tkinter import ttk
import os
import logging
from datetime import datetime
from tkinter import scrolledtext
    
from src.spritely.utils.audio_utils import select_microphone, check_permissions
from src.spritely.core.ai_summarise import ai_summary

# Set up logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class SpritelyGUI:
    def __init__(self, transcriber, field_transcriber, meeting_transcriber):
        logger.info("Initializing SpritelyGUI")
        self.root = tk.Tk()
        self.root.title("Spritely AI")
        self.root.geometry("400x500")
        
        # Make window transparent
        self.root.attributes('-alpha', 0.95)  # 95% opacity
        
        # Style configuration
        style = ttk.Style()
        
        # Custom styles with modern colors
        bg_color = "#000000"  # Black background
        fg_color = "#ffffff"  # White text
        
        # Remove Azure theme attempt and configure basic styles
        style.configure(".", background=bg_color, foreground=fg_color)
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("Main.TFrame", background=bg_color)
        
        # Configure labelframe styles
        style.configure("TLabelframe",
                       background=bg_color,
                       relief="flat",
                       borderwidth=0)
        
        style.configure("TLabelframe.Label",
                       font=("Helvetica", 11, "bold"),
                       foreground=fg_color,
                       background=bg_color)
        
        # Configure button styles
        style.configure("Record.TButton", 
                       foreground="#2ecc71",
                       background=bg_color,
                       padding=10,
                       font=("Helvetica", 10, "bold"))
        
        style.configure("Stop.TButton",
                       foreground="#e74c3c",
                       background=bg_color,
                       padding=10,
                       font=("Helvetica", 10, "bold"))
        
        # Main container
        main_container = ttk.Frame(self.root, padding="20", style="Main.TFrame")
        main_container.pack(fill="both", expand=True)
        
        # Configure root background
        self.root.configure(bg=bg_color)

        self.transcriber = transcriber
        self.field_transcriber = field_transcriber
        self.meeting_transcriber = meeting_transcriber
        
        # Status frame
        status_frame = ttk.LabelFrame(main_container, text="Status", padding="10")
        status_frame.pack(fill="x", pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready", font=("Helvetica", 12))
        self.status_label.pack()
        
        # Add microphone status label
        self.mic_label = ttk.Label(status_frame, text="", font=("Helvetica", 10, "italic"))
        self.mic_label.pack()
        
        # Recording controls frame
        recording_frame = ttk.LabelFrame(main_container, text="Recording Controls", padding="10")
        recording_frame.pack(fill="x", pady=(0, 10))
        
        # AI Transcription controls
        ai_frame = ttk.Frame(recording_frame)
        ai_frame.pack(fill="x", pady=5)
        
        ttk.Label(ai_frame, text="Spawn Spritely 🧚🏼‍♀️✨", font=("Helvetica", 11, "bold")).pack(side="top")
        
        ai_buttons = ttk.Frame(ai_frame)
        ai_buttons.pack(pady=5)
        
        self.ai_record_btn = ttk.Button(ai_buttons, text="Spawn", 
                                      style="Record.TButton",
                                      command=self.toggle_ai_recording)
        self.ai_record_btn.pack(side="left", padx=5)
        
        # Field Transcription controls
        field_frame = ttk.Frame(recording_frame)
        field_frame.pack(fill="x", pady=5)
        
        ttk.Label(field_frame, text="Field Transcription", font=("Helvetica", 11, "bold")).pack(side="top")
        
        field_buttons = ttk.Frame(field_frame)
        field_buttons.pack(pady=5)
        
        self.field_record_btn = ttk.Button(field_buttons, text="Spawn",
                                         style="Record.TButton",
                                         command=self.toggle_field_recording)
        self.field_record_btn.pack(side="left", padx=5)
        
        # Meeting Transcription controls
        meeting_frame = ttk.Frame(recording_frame)
        meeting_frame.pack(fill="x", pady=5)
        
        ttk.Label(meeting_frame, text="Meeting Transcription 📝", font=("Helvetica", 11, "bold")).pack(side="top")
        
        meeting_buttons = ttk.Frame(meeting_frame)
        meeting_buttons.pack(pady=5)
        
        self.meeting_record_btn = ttk.Button(meeting_buttons, text="Start Meeting",
                                         style="Record.TButton",
                                         command=self.toggle_meeting_recording)
        self.meeting_record_btn.pack(side="left", padx=5)

        # Initialize meeting state
        self.meeting_active = False
        self.meeting_transcript = []

        # Shortcuts frame
        shortcuts_frame = ttk.LabelFrame(main_container, text="Keyboard Shortcuts", padding="10")
        shortcuts_frame.pack(fill="x", pady=(0, 10))
        
        shortcuts_text = (
            "⌘ + ⌥ + K: Start/Stop AI Transcription\n"
            "⌘ + ⌥ + L: Start/Stop Field Transcription\n"
            "ESC: Stop All Recording"
        )
        shortcuts_label = ttk.Label(shortcuts_frame, text=shortcuts_text, justify="left")
        shortcuts_label.pack(pady=5)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_container, text="Settings", padding="10")
        settings_frame.pack(fill="x")
        
        ttk.Button(settings_frame, text="Select Microphone", 
                  command=select_microphone).pack(pady=5, fill="x")
        
        ttk.Button(settings_frame, text="Check Permissions", 
                  command=self.check_permissions_gui).pack(pady=5, fill="x")
        
        # Recording status indicator
        self.recording_status = ttk.Label(main_container, text="Not Recording", 
                                        foreground="red", font=("Helvetica", 12, "bold"))
        self.recording_status.pack(pady=10)

        # Add transcript viewer window attribute
        self.transcript_window = None

    def toggle_ai_recording(self):
        if not self.transcriber.is_recording:
            logger.info("Starting AI transcription")
            self.transcriber.start_recording()
            self.ai_record_btn.configure(text="Sleep", style="Stop.TButton")
            self.update_status("AI Transcription Active", True)
        else:
            logger.info("Stopping AI transcription")
            self.transcriber.stop_recording()
            self.ai_record_btn.configure(text="Spawn", style="Record.TButton")
            self.update_status("Ready", False)

    def toggle_field_recording(self):
        if not self.field_transcriber.is_recording:
            logger.info("Starting field transcription")
            self.field_transcriber.start_recording()
            self.field_record_btn.configure(text="Sleep", style="Stop.TButton")
            self.update_status("Field Transcription Active", True)
        else:
            logger.info("Stopping field transcription")
            self.field_transcriber.stop_recording()
            self.field_record_btn.configure(text="Start Recording", style="Record.TButton")
            self.update_status("Ready", False)

    def toggle_meeting_recording(self):
        if not self.meeting_active:
            logger.info("Starting meeting recording")
            self.meeting_active = True
            self.meeting_transcript = []
            self.meeting_transcriber.start_recording()
            self.meeting_record_btn.configure(text="End Meeting", style="Stop.TButton")
            self.update_status("Meeting Recording Active", True)
        else:
            logger.info("Ending meeting recording")
            self.meeting_active = False
            self.meeting_transcriber.stop_recording()
            self.meeting_record_btn.configure(text="Start Meeting", style="Record.TButton")
            self.update_status("Ready", False)
            self.convert_json_to_text()

    def show_transcript(self, filename):
        logger.info(f"Opening transcript window for {filename}")
        """Open a new window to display the transcript"""
        # Create new window
        self.transcript_window = tk.Toplevel(self.root)
        self.transcript_window.title("Meeting Transcript")
        self.transcript_window.geometry("600x800")
        
        # Style the transcript window
        bg_color = "#e0e0e0"  # Match main window background
        self.transcript_window.attributes('-alpha', 0.95)
        self.transcript_window.configure(bg=bg_color)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.transcript_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create Transcript tab
        transcript_frame = ttk.Frame(notebook, style="Main.TFrame")
        notebook.add(transcript_frame, text="Transcript")
        
        # Create Summary tab
        summary_frame = ttk.Frame(notebook, style="Main.TFrame")
        notebook.add(summary_frame, text="AI Summary")
        
        # Add transcript text area
        transcript_text = scrolledtext.ScrolledText(
            transcript_frame,
            wrap=tk.WORD,
            width=60,
            height=40,
            font=("Helvetica", 11),
            bg=bg_color,
            fg="#2c3e50",
            relief="flat"
        )
        transcript_text.pack(fill=tk.BOTH, expand=True)
        
        # Add summary text area (placeholder for now)
        summary_text = scrolledtext.ScrolledText(
            summary_frame,
            wrap=tk.WORD,
            width=60,
            height=40,
            font=("Helvetica", 11),
            bg=bg_color,
            fg="#2c3e50",
            relief="flat"
        )
        summary_text.pack(fill=tk.BOTH, expand=True)
        summary_text.insert(tk.END, "AI Summary coming soon...")
        summary_text.configure(state='disabled')

        # Read and display the transcript
        try:
            with open(filename, 'r') as f:
                content = f.read()
                transcript_text.insert(tk.END, content)
                transcript_text.configure(state='disabled')
                
                # Generate and display AI summary
                logger.debug("Generating AI summary")
                summary = ai_summary(meeting_transcript=content)
                summary_text.configure(state='normal')
                summary_text.delete(1.0, tk.END)
                summary_text.insert(tk.END, summary)
                summary_text.configure(state='disabled')
        except Exception as e:
            logger.error(f"Error displaying transcript: {str(e)}")
            transcript_text.insert(tk.END, f"Error loading transcript: {str(e)}")
            transcript_text.configure(state='disabled')
            summary_text.configure(state='normal')
            summary_text.delete(1.0, tk.END)
            summary_text.insert(tk.END, f"Error generating summary: {str(e)}")
            summary_text.configure(state='disabled')

    def convert_json_to_text(self):
        if not self.meeting_transcriber.transcriptions:
            logger.warning("No transcript to save - empty transcription")
            return

        try:
            # Create meetings directory if it doesn't exist
            current_dir = os.path.abspath(os.path.dirname(__file__))
            meetings_dir = os.path.join(current_dir, "meetings")
            os.makedirs(meetings_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(meetings_dir, f"meeting_{timestamp}.txt")
            
            logger.info(f"Saving transcript to: {filename}")

            with open(filename, "w") as f:
                f.write("Meeting Transcript\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n\n")
                
                # Write each transcription entry
                for entry in self.meeting_transcriber.transcriptions:
                    timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
                    transcript = entry['transcript']
                    
                    if entry.get('words') and hasattr(entry['words'][0], 'speaker'):
                        speaker = f"Speaker {entry['words'][0].speaker}"
                        f.write(f"[{timestamp}] {speaker}: {transcript}\n")
                    else:
                        f.write(f"[{timestamp}] {transcript}\n")

            logger.info("Successfully saved transcript")
            self.status_label.config(text=f"Meeting saved to {filename}")
            
            # Show the transcript in a new window
            self.show_transcript(filename)
            
        except Exception as e:
            logger.error(f"Error saving transcript: {str(e)}")
            self.status_label.config(text=f"Error saving transcript: {str(e)}")
    
    def update_status(self, message, is_recording=False):
        logger.debug(f"Updating status: {message} (recording: {is_recording})")
        self.status_label.config(text=message)
        # Try to get microphone info safely
        try:
            import sounddevice as sd
            device_info = sd.query_devices(kind='input')
            current_mic = device_info['name']
            self.mic_label.config(text=f"Using: {current_mic}")
            logger.debug(f"Current microphone: {current_mic}")
        except Exception as e:
            logger.warning(f"Could not get microphone info: {e}")
            self.mic_label.config(text="Microphone info unavailable")
            
        if is_recording:
            self.recording_status.config(text="Recording", foreground="green")
        else:
            self.recording_status.config(text="Not Recording", foreground="red")
    
    def check_permissions_gui(self):
        logger.info("Checking microphone permissions")
        if check_permissions():
            logger.info("All permissions granted")
            self.status_label.config(text="All permissions granted!")
        else:
            logger.warning("Missing microphone permissions")
            self.status_label.config(text="Missing permissions. Check console for details.")
    
    def run(self):
        logger.info("Starting Spritely GUI")
        self.root.mainloop() 