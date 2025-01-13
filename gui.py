import tkinter as tk
from tkinter import ttk
from utils.audio_utils import select_microphone, check_permissions

class SpritelyGUI:
    def __init__(self, transcriber, field_transcriber):
        self.root = tk.Tk()
        self.root.title("Spritely")
        self.root.geometry("400x500")
        
        self.transcriber = transcriber
        self.field_transcriber = field_transcriber
        
        # Style configuration
        style = ttk.Style()
        style.configure("Record.TButton", foreground="green", padding=10)
        style.configure("Stop.TButton", foreground="red", padding=10)
        
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill="both", expand=True)
        
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
        
        ttk.Label(ai_frame, text="AI Transcription", font=("Helvetica", 11, "bold")).pack(side="top")
        
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