import tkinter as tk
from tkinter import ttk
from utils.audio_utils import select_microphone, check_permissions
import os
from datetime import datetime
from tkinter import scrolledtext

class SpritelyGUI:
    def __init__(self, transcriber, field_transcriber, meeting_transcriber):
        self.root = tk.Tk()
        self.root.title("Spritely")
        self.root.geometry("400x500")
        
        # Make window transparent
        self.root.attributes('-alpha', 0.95)  # 95% opacity
        
        # Style configuration
        style = ttk.Style()
        
        # Configure modern theme if available
        try:
            self.root.tk.call('source', 'azure.tcl')  # You'll need to download azure theme
            style.theme_use('azure')
        except:
            print("Azure theme not found, using default theme")
        
        # Custom styles with modern colors
        style.configure("Record.TButton", 
                       foreground="#2ecc71",
                       padding=10,
                       font=("Helvetica", 10, "bold"))
        
        style.configure("Stop.TButton",
                       foreground="#e74c3c",
                       padding=10,
                       font=("Helvetica", 10, "bold"))
        
        style.configure("TLabelframe",
                       background="#ffffff",
                       relief="flat",
                       borderwidth=0)
        
        style.configure("TLabelframe.Label",
                       font=("Helvetica", 11, "bold"),
                       foreground="#2c3e50")
        
        # Main container with glossy background
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill="both", expand=True)
        
        # Add subtle background
        bg_color = "#f8f9fa"
        self.root.configure(bg=bg_color)
        main_container.configure(style="Main.TFrame")
        style.configure("Main.TFrame", background=bg_color)
        
        self.transcriber = transcriber
        self.field_transcriber = field_transcriber
        self.meeting_transcriber = meeting_transcriber
        
        # Status frame
        status_frame = ttk.LabelFrame(main_container, text="Status", padding="10")
        status_frame.pack(fill="x", pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready", font=("Helvetica", 12))
        self.status_label.pack()
        
        # Recording controls frame
        recording_frame = ttk.LabelFrame(main_container, text="Recording Controls", padding="10")
        recording_frame.pack(fill="x", pady=(0, 10))
        
        # AI Transcription controls
        ai_frame = ttk.Frame(recording_frame)
        ai_frame.pack(fill="x", pady=5)
        
        ttk.Label(ai_frame, text="Spawn Spritely 🧚🏼‍♀️✨", font=("Helvetica", 11, "bold")).pack(side="top")
        
        ai_buttons = ttk.Frame(ai_frame)
        ai_buttons.pack(pady=5)
        
        self.ai_record_btn = ttk.Button(ai_buttons, text="Start Recording", 
                                      style="Record.TButton",
                                      command=self.toggle_ai_recording)
        self.ai_record_btn.pack(side="left", padx=5)
        
        # Field Transcription controls
        field_frame = ttk.Frame(recording_frame)
        field_frame.pack(fill="x", pady=5)
        
        ttk.Label(field_frame, text="Field Transcription", font=("Helvetica", 11, "bold")).pack(side="top")
        
        field_buttons = ttk.Frame(field_frame)
        field_buttons.pack(pady=5)
        
        self.field_record_btn = ttk.Button(field_buttons, text="Start Recording",
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
            self.transcriber.start_recording()
            self.ai_record_btn.configure(text="Stop Recording", style="Stop.TButton")
            self.update_status("AI Transcription Active", True)
        else:
            self.transcriber.stop_recording()
            self.ai_record_btn.configure(text="Start Recording", style="Record.TButton")
            self.update_status("Ready", False)

    def toggle_field_recording(self):
        if not self.field_transcriber.is_recording:
            self.field_transcriber.start_recording()
            self.field_record_btn.configure(text="Stop Recording", style="Stop.TButton")
            self.update_status("Field Transcription Active", True)
        else:
            self.field_transcriber.stop_recording()
            self.field_record_btn.configure(text="Start Recording", style="Record.TButton")
            self.update_status("Ready", False)

    def toggle_meeting_recording(self):
        if not self.meeting_active:
            print("Starting meeting recording...")
            self.meeting_active = True
            self.meeting_transcript = []
            self.meeting_transcriber.start_recording()
            self.meeting_record_btn.configure(text="End Meeting", style="Stop.TButton")
            self.update_status("Meeting Recording Active", True)
        else:
            print("Ending meeting recording...")
            self.meeting_active = False
            self.meeting_transcriber.stop_recording()
            self.meeting_record_btn.configure(text="Start Meeting", style="Record.TButton")
            self.update_status("Ready", False)
            self.convert_json_to_text()

    def show_transcript(self, filename):
        """Open a new window to display the transcript"""
        # Create new window
        self.transcript_window = tk.Toplevel(self.root)
        self.transcript_window.title("Meeting Transcript")
        self.transcript_window.geometry("600x800")
        
        # Make transcript window also transparent
        self.transcript_window.attributes('-alpha', 0.95)
        self.transcript_window.configure(bg="#f8f9fa")
        
        text_area = scrolledtext.ScrolledText(
            self.transcript_window,
            wrap=tk.WORD,
            width=60,
            height=40,
            font=("Helvetica", 11),
            bg="#ffffff",
            relief="flat"
        )
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Read and display the transcript
        try:
            with open(filename, 'r') as f:
                content = f.read()
                text_area.insert(tk.END, content)
                text_area.configure(state='disabled')  # Make read-only
        except Exception as e:
            text_area.insert(tk.END, f"Error loading transcript: {str(e)}")
            text_area.configure(state='disabled')

    def convert_json_to_text(self):
        """Convert the JSON transcriptions to a readable text format and save"""
        try:
            if not self.meeting_transcriber.transcriptions:
                print("No transcript to save!")
                return

            # Create meetings directory if it doesn't exist
            current_dir = os.path.abspath(os.path.dirname(__file__))
            meetings_dir = os.path.join(current_dir, "meetings")
            os.makedirs(meetings_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(meetings_dir, f"meeting_{timestamp}.txt")
            
            print(f"Saving to: {filename}")

            with open(filename, "w") as f:
                f.write("Meeting Transcript\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n\n")
                
                # Write each transcription entry
                for entry in self.meeting_transcriber.transcriptions:
                    timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
                    transcript = entry['transcript']
                    
                    # Check if there are words with speaker information
                    if entry.get('words') and hasattr(entry['words'][0], 'speaker'):
                        speaker = f"Speaker {entry['words'][0].speaker}"
                        f.write(f"[{timestamp}] {speaker}: {transcript}\n")
                    else:
                        f.write(f"[{timestamp}] {transcript}\n")

            print(f"Successfully saved transcript to {filename}")
            self.status_label.config(text=f"Meeting saved to {filename}")
            
            # Show the transcript in a new window
            self.show_transcript(filename)
            
        except Exception as e:
            print(f"Error saving transcript: {e}")
            self.status_label.config(text=f"Error saving transcript: {str(e)}")
    
    def update_status(self, message, is_recording=False):
        self.status_label.config(text=message)
        if is_recording:
            self.recording_status.config(text="Recording", foreground="green")
        else:
            self.recording_status.config(text="Not Recording", foreground="red")
    
    def check_permissions_gui(self):
        if check_permissions():
            self.status_label.config(text="All permissions granted!")
        else:
            self.status_label.config(text="Missing permissions. Check console for details.")
    
    def run(self):
        self.root.mainloop() 