#!/usr/bin/env python3
"""
Video Compressor Tool - GUI Version
A modern graphical interface for the video compression tool with robust transcript generation.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import ffmpeg
import speech_recognition as sr
import tempfile


class VideoCompressorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video Compressor Tool")
        self.root.geometry("900x900")
        self.root.resizable(True, True)
        
        # Set theme and styling
        self.setup_styling()
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.crf_value = tk.IntVar(value=28)
        self.preset_value = tk.StringVar(value="fast")
        self.resolution_width = tk.StringVar()
        self.resolution_height = tk.StringVar()
        self.audio_codec = tk.StringVar(value="aac")
        self.audio_bitrate = tk.StringVar(value="128k")
        self.resize_video = tk.BooleanVar(value=False)
        
        # Transcript variables
        self.generate_transcript = tk.BooleanVar(value=False)
        self.transcript_file = tk.StringVar()
        self.transcript_language = tk.StringVar(value="en-US")
        
        # Create GUI
        self.create_widgets()
        
        # Check FFmpeg
        self.check_ffmpeg()
    
    def setup_styling(self):
        """Setup modern styling for the GUI."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        self.root.configure(bg='#f0f0f0')
        
        # Configure styles
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'), foreground='#34495e')
        style.configure('Info.TLabel', font=('Arial', 10), foreground='#7f8c8d')
        
        # Configure button styles
        style.configure('Primary.TButton', 
                       background='#3498db', 
                       foreground='white',
                       font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', 
                       background='#27ae60', 
                       foreground='white',
                       font=('Arial', 10, 'bold'))
        style.configure('Warning.TButton', 
                       background='#f39c12', 
                       foreground='white',
                       font=('Arial', 10, 'bold'))
        
        # Configure checkbutton style
        style.configure('Custom.TCheckbutton', font=('Arial', 11))
    
    def create_widgets(self):
        """Create all GUI widgets with proper spacing."""
        # Main container with scrollbar
        main_canvas = tk.Canvas(self.root, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        scrollable_frame.columnconfigure(1, weight=1)
        
        # Title - Row 0
        title_label = ttk.Label(scrollable_frame, text="🎬 Video Compressor Tool", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(20, 30), padx=20)
        
        # File Selection Section - Rows 1-3
        self.create_file_section(scrollable_frame, 1)
        
        # Compression Settings Section - Rows 4-7
        self.create_compression_section(scrollable_frame, 4)
        
        # Resolution Section - Rows 8-12
        self.create_resolution_section(scrollable_frame, 8)
        
        # Audio Settings Section - Rows 13-16
        self.create_audio_section(scrollable_frame, 13)
        
        # Transcript Section - Rows 17-20
        self.create_transcript_section(scrollable_frame, 17)
        
        # Progress and Log Section - Rows 21-25
        self.create_progress_section(scrollable_frame, 21)
        
        # Control Buttons - Row 26
        self.create_control_buttons(scrollable_frame, 26)
        
        # Status Bar - Row 27
        self.create_status_bar(scrollable_frame, 27)
        
        # Pack the canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def create_file_section(self, parent, row):
        """Create file selection section."""
        # Section header - Row 1
        file_header = ttk.Label(parent, text="📁 File Selection", style='Header.TLabel')
        file_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        
        # Input file - Row 2
        ttk.Label(parent, text="Input Video:", font=('Arial', 11)).grid(
            row=row+1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 10))
        input_entry = ttk.Entry(parent, textvariable=self.input_file, width=60, font=('Arial', 10))
        input_entry.grid(row=row+1, column=1, sticky=(tk.W, tk.E), padx=(0, 15), pady=(0, 10))
        ttk.Button(parent, text="Browse", command=self.browse_input_file, width=12).grid(
            row=row+1, column=2, padx=(0, 20), pady=(0, 10))
        
        # Output file - Row 3
        ttk.Label(parent, text="Output File:", font=('Arial', 11)).grid(
            row=row+2, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 20))
        output_entry = ttk.Entry(parent, textvariable=self.output_file, width=60, font=('Arial', 10))
        output_entry.grid(row=row+2, column=1, sticky=(tk.W, tk.E), padx=(0, 15), pady=(0, 20))
        ttk.Button(parent, text="Browse", command=self.browse_output_file, width=12).grid(
            row=row+2, column=2, padx=(0, 20), pady=(0, 20))
    
    def create_compression_section(self, parent, row):
        """Create compression settings section."""
        # Section header - Row 4
        comp_header = ttk.Label(parent, text="⚙️ Compression Settings", style='Header.TLabel')
        comp_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        
        # CRF value - Row 5
        ttk.Label(parent, text="Quality (CRF):", font=('Arial', 11)).grid(
            row=row+1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 10))
        
        crf_frame = ttk.Frame(parent)
        crf_frame.grid(row=row+1, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 10))
        
        crf_scale = ttk.Scale(crf_frame, from_=18, to=30, orient=tk.HORIZONTAL, 
                              variable=self.crf_value, length=250)
        crf_scale.pack(side=tk.LEFT)
        
        crf_label = ttk.Label(crf_frame, textvariable=tk.StringVar(value="28"), 
                              font=('Arial', 11, 'bold'))
        crf_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # Update CRF label when scale changes
        def update_crf_label(*args):
            crf_label.config(text=str(self.crf_value.get()))
        self.crf_value.trace('w', update_crf_label)
        
        # CRF info - Row 5 (right side)
        crf_info = ttk.Label(parent, text="18=High Quality, 28=Balanced, 30=High Compression", 
                             style='Info.TLabel')
        crf_info.grid(row=row+1, column=2, sticky=tk.W, padx=(0, 20), pady=(0, 10))
        
        # Preset - Row 6
        ttk.Label(parent, text="Speed Preset:", font=('Arial', 11)).grid(
            row=row+2, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 20))
        preset_combo = ttk.Combobox(parent, textvariable=self.preset_value, 
                                   values=['ultrafast', 'superfast', 'veryfast', 'faster', 
                                          'fast', 'medium', 'slow', 'slower', 'veryslow'],
                                   state='readonly', width=20, font=('Arial', 10))
        preset_combo.grid(row=row+2, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
        
        preset_info = ttk.Label(parent, text="Fast=Quick, Slow=Better Compression", 
                               style='Info.TLabel')
        preset_info.grid(row=row+2, column=2, sticky=tk.W, padx=(0, 20), pady=(0, 20))
    
    def create_resolution_section(self, parent, row):
        """Create resolution settings section."""
        # Section header - Row 8
        res_header = ttk.Label(parent, text="📐 Resolution Settings", style='Header.TLabel')
        res_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        
        # Resize checkbox - Row 9
        resize_check = ttk.Checkbutton(parent, text="Resize Video", 
                                      variable=self.resize_video,
                                      command=self.toggle_resolution_inputs,
                                      style='Custom.TCheckbutton')
        resize_check.grid(row=row+1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 15))
        
        # Resolution inputs - Row 10
        res_frame = ttk.Frame(parent)
        res_frame.grid(row=row+2, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 15))
        
        ttk.Label(res_frame, text="Width:", font=('Arial', 11)).pack(side=tk.LEFT)
        width_entry = ttk.Entry(res_frame, textvariable=self.resolution_width, width=8, font=('Arial', 10))
        width_entry.pack(side=tk.LEFT, padx=(8, 15))
        
        ttk.Label(res_frame, text="Height:", font=('Arial', 11)).pack(side=tk.LEFT)
        height_entry = ttk.Entry(res_frame, textvariable=self.resolution_height, width=8, font=('Arial', 10))
        height_entry.pack(side=tk.LEFT, padx=(8, 0))
        
        # Resolution info - Row 11
        res_info = ttk.Label(parent, text="Common: 1920x1080 (1080p), 1280x720 (720p), 854x480 (480p)", 
                            style='Info.TLabel')
        res_info.grid(row=row+3, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
        
        # Initially disable resolution inputs
        self.toggle_resolution_inputs()
    
    def create_audio_section(self, parent, row):
        """Create audio settings section."""
        # Section header - Row 13
        audio_header = ttk.Label(parent, text="🔊 Audio Settings", style='Header.TLabel')
        audio_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        
        # Audio codec - Row 14
        ttk.Label(parent, text="Audio Codec:", font=('Arial', 11)).grid(
            row=row+1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 10))
        codec_combo = ttk.Combobox(parent, textvariable=self.audio_codec, 
                                   values=['aac', 'mp3', 'opus', 'vorbis'],
                                   state='readonly', width=20, font=('Arial', 10))
        codec_combo.grid(row=row+1, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 10))
        
        # Audio bitrate - Row 15
        ttk.Label(parent, text="Audio Bitrate:", font=('Arial', 11)).grid(
            row=row+2, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 20))
        bitrate_combo = ttk.Combobox(parent, textvariable=self.audio_bitrate, 
                                     values=['64k', '96k', '128k', '192k', '256k'],
                                     state='readonly', width=20, font=('Arial', 10))
        bitrate_combo.grid(row=row+2, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
    
    def create_transcript_section(self, parent, row):
        """Create transcript settings section."""
        # Section header - Row 17
        transcript_header = ttk.Label(parent, text="🗣️ Transcript Settings", style='Header.TLabel')
        transcript_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        
        # Transcript checkbox - Row 18
        transcript_check = ttk.Checkbutton(parent, text="Generate Transcript", 
                                          variable=self.generate_transcript,
                                          command=self.toggle_transcript_inputs,
                                          style='Custom.TCheckbutton')
        transcript_check.grid(row=row+1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 15))
        
        # Transcript file - Row 19
        ttk.Label(parent, text="Transcript File:", font=('Arial', 11)).grid(
            row=row+2, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 10))
        transcript_entry = ttk.Entry(parent, textvariable=self.transcript_file, width=40, font=('Arial', 10))
        transcript_entry.grid(row=row+2, column=1, sticky=(tk.W, tk.E), padx=(0, 15), pady=(0, 10))
        ttk.Button(parent, text="Browse", command=self.browse_transcript_file, width=12).grid(
            row=row+2, column=2, padx=(0, 20), pady=(0, 10))
        
        # Language selection - Row 20
        ttk.Label(parent, text="Language:", font=('Arial', 11)).grid(
            row=row+3, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 20))
        language_combo = ttk.Combobox(parent, textvariable=self.transcript_language,
                                     values=['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'zh-CN'],
                                     state='readonly', width=20, font=('Arial', 10))
        language_combo.grid(row=row+3, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
        
        # Initially disable transcript inputs
        self.toggle_transcript_inputs()
    
    def create_progress_section(self, parent, row):
        """Create progress and log section."""
        # Section header - Row 21
        progress_header = ttk.Label(parent, text="📊 Progress & Log", style='Header.TLabel')
        progress_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        
        # Progress bar - Row 22
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=row+1, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                              padx=20, pady=(0, 15))
        
        # Log text area - Row 23
        self.log_text = scrolledtext.ScrolledText(parent, height=10, width=80, font=('Consolas', 9))
        self.log_text.grid(row=row+2, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                          padx=20, pady=(0, 15))
        
        # Clear log button - Row 24
        ttk.Button(parent, text="Clear Log", command=self.clear_log, width=12).grid(
            row=row+3, column=0, sticky=tk.W, padx=20, pady=(0, 20))
    
    def create_control_buttons(self, parent, row):
        """Create control buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        self.compress_button = ttk.Button(button_frame, text="🚀 Start Compression", 
                                         command=self.start_compression, style='Primary.TButton')
        self.compress_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop", 
                                     command=self.stop_compression, style='Warning.TButton', state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15))
        
        reset_button = ttk.Button(button_frame, text="🔄 Reset", 
                                 command=self.reset_form, style='Success.TButton')
        reset_button.pack(side=tk.LEFT)
    
    def create_status_bar(self, parent, row):
        """Create status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(parent, textvariable=self.status_var, 
                                font=('Arial', 10), foreground='#7f8c8d')
        status_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=20, pady=(0, 20))
    
    def toggle_resolution_inputs(self):
        """Enable/disable resolution input fields."""
        if self.resize_video.get():
            self.resolution_width.set("1280")
            self.resolution_height.set("720")
        else:
            self.resolution_width.set("")
            self.resolution_height.set("")
    
    def toggle_transcript_inputs(self):
        """Enable/disable transcript input fields."""
        if self.generate_transcript.get():
            # Auto-generate transcript filename based on output video
            output_file = self.output_file.get()
            if output_file:
                base_name = os.path.splitext(output_file)[0]
                self.transcript_file.set(f"{base_name}_transcript.txt")
        else:
            self.transcript_file.set("")
    
    def browse_input_file(self):
        """Browse for input video file."""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(title="Select Input Video", filetypes=filetypes)
        if filename:
            self.input_file.set(filename)
            # Auto-generate output filename
            base_name = os.path.splitext(filename)[0]
            self.output_file.set(f"{base_name}_compressed.mp4")
            # Auto-generate transcript filename if enabled
            if self.generate_transcript.get():
                self.transcript_file.set(f"{base_name}_transcript.txt")
    
    def browse_output_file(self):
        """Browse for output video file."""
        filetypes = [
            ("MP4 files", "*.mp4"),
            ("All files", "*.*")
        ]
        filename = filedialog.asksaveasfilename(title="Save Compressed Video As", 
                                              filetypes=filetypes, defaultextension=".mp4")
        if filename:
            self.output_file.set(filename)
            # Auto-generate transcript filename if enabled
            if self.generate_transcript.get():
                base_name = os.path.splitext(filename)[0]
                self.transcript_file.set(f"{base_name}_transcript.txt")
    
    def browse_transcript_file(self):
        """Browse for transcript file location."""
        filetypes = [
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        filename = filedialog.asksaveasfilename(title="Save Transcript As", 
                                              filetypes=filetypes, defaultextension=".txt")
        if filename:
            self.transcript_file.set(filename)
    
    def clear_log(self):
        """Clear the log text area."""
        self.log_text.delete(1.0, tk.END)
    
    def log_message(self, message):
        """Add message to log with timestamp."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, check=True)
            self.log_message("✅ FFmpeg found and ready")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log_message("❌ FFmpeg not found! Please install FFmpeg and add it to your system PATH.")
            messagebox.showerror("FFmpeg Error", 
                               "FFmpeg not found! Please install FFmpeg and add it to your system PATH.\n\n"
                               "Download from: https://ffmpeg.org/download.html")
    
    def start_compression(self):
        """Start video compression in a separate thread."""
        if not self.input_file.get() or not self.output_file.get():
            messagebox.showerror("Error", "Please select input and output files.")
            return
        
        # Validate transcript settings
        if self.generate_transcript.get() and not self.transcript_file.get():
            messagebox.showerror("Error", "Please specify a transcript file location.")
            return
        
        # Start compression in separate thread
        self.compress_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        
        compression_thread = threading.Thread(target=self.compress_video)
        compression_thread.daemon = True
        compression_thread.start()
    
    def stop_compression(self):
        """Stop video compression."""
        # This would need to be implemented with FFmpeg process management
        self.log_message("⚠️ Stop functionality not yet implemented")
        self.reset_controls()
    
    def create_transcript_from_video(self, input_file, output_file, language='en-US'):
        """
        Generate transcript from video file using speech recognition with robust error handling.
        
        Args:
            input_file (str): Path to input video file
            output_file (str): Path to output transcript file
            language (str): Language code for speech recognition
        
        Returns:
            str: Generated transcript text or None if failed
        """
        
        if not os.path.exists(input_file):
            self.log_message(f"❌ Input file not found: {input_file}")
            return None
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        try:
            self.log_message(f"🎵 Extracting audio from video...")
            
            # Extract audio using FFmpeg with multiple format attempts
            audio_formats = [
                # Format 1: Standard WAV with optimal speech recognition parameters
                {
                    'acodec': 'pcm_s16le',
                    'ar': 16000,
                    'ac': 1,
                    'f': 'wav',
                    'loglevel': 'error'
                },
                # Format 2: Alternative WAV with different parameters
                {
                    'acodec': 'pcm_s16le',
                    'ar': 22050,
                    'ac': 1,
                    'f': 'wav',
                    'loglevel': 'error'
                },
                # Format 3: FLAC format (lossless, often better for recognition)
                {
                    'acodec': 'flac',
                    'ar': 16000,
                    'ac': 1,
                    'f': 'flac',
                    'loglevel': 'error'
                }
            ]
            
            transcript = None
            successful_format = None
            
            for i, format_params in enumerate(audio_formats):
                try:
                    self.log_message(f"🎵 Trying audio format {i+1}...")
                    
                    # Extract audio with current format
                    (
                        ffmpeg.input(input_file)
                        .output(temp_audio_path, **format_params)
                        .overwrite_output()
                        .run(capture_stdout=True, capture_stderr=True, quiet=True)
                    )
                    
                    # Try to recognize speech with this audio format
                    transcript = self._recognize_speech(temp_audio_path, language, recognizer)
                    
                    if transcript:
                        successful_format = i + 1
                        self.log_message(f"✅ Success with audio format {successful_format}")
                        break
                    else:
                        self.log_message(f"⚠️ Audio format {i+1} failed, trying next...")
                        
                except Exception as e:
                    self.log_message(f"⚠️ Audio format {i+1} extraction failed: {e}")
                    continue
            
            if not transcript:
                self.log_message("❌ All audio formats failed")
                return None
            
            # Save transcript to file
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            self.log_message(f"📝 Transcript saved to: {output_file}")
            return transcript
            
        except Exception as e:
            self.log_message(f"❌ Error during transcript generation: {str(e)}")
            return None
        finally:
            # Clean up temporary audio file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
    
    def _recognize_speech(self, audio_path, language, recognizer):
        """
        Attempt speech recognition with multiple strategies.
        
        Args:
            audio_path (str): Path to audio file
            language (str): Language code
            recognizer: Speech recognition recognizer instance
        
        Returns:
            str: Recognized text or None if failed
        """
        
        try:
            self.log_message(f"🎤 Processing audio for speech recognition...")
            
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Record audio
                audio = recognizer.record(source)
            
            self.log_message(f"🔍 Converting speech to text...")
            
            # Strategy 1: Try with original language code
            try:
                transcript = recognizer.recognize_google(audio, language=language)
                self.log_message("✅ Speech recognition successful with original language code")
                return transcript
            except sr.RequestError as e:
                self.log_message(f"⚠️ First attempt failed: {e}")
            
            # Strategy 2: Try with simplified language code
            try:
                if language == 'en-US':
                    self.log_message("🔄 Retrying with 'en' language code...")
                    transcript = recognizer.recognize_google(audio, language='en')
                elif language.startswith('en'):
                    self.log_message("🔄 Retrying with 'en' language code...")
                    transcript = recognizer.recognize_google(audio, language='en')
                else:
                    base_lang = language.split('-')[0]
                    self.log_message(f"🔄 Retrying with '{base_lang}' language code...")
                    transcript = recognizer.recognize_google(audio, language=base_lang)
                
                if transcript:
                    self.log_message("✅ Speech recognition successful with simplified language code")
                    return transcript
                    
            except sr.RequestError as e2:
                self.log_message(f"⚠️ Second attempt failed: {e2}")
            
            # Strategy 3: Try without specifying language (auto-detect)
            try:
                self.log_message("🔄 Retrying with auto-language detection...")
                transcript = recognizer.recognize_google(audio)
                if transcript:
                    self.log_message("✅ Speech recognition successful with auto-detection")
                    return transcript
            except sr.RequestError as e3:
                self.log_message(f"⚠️ Third attempt failed: {e3}")
            
            # Strategy 4: Try with different audio parameters
            try:
                self.log_message("🔄 Retrying with adjusted audio parameters...")
                # Adjust recognition parameters
                recognizer.energy_threshold = 300
                recognizer.dynamic_energy_threshold = True
                recognizer.pause_threshold = 0.8
                
                transcript = recognizer.recognize_google(audio, language='en')
                if transcript:
                    self.log_message("✅ Speech recognition successful with adjusted parameters")
                    return transcript
            except sr.RequestError as e4:
                self.log_message(f"⚠️ Fourth attempt failed: {e4}")
            
            # Strategy 5: Try chunking the audio for better recognition
            try:
                self.log_message("🔄 Retrying with audio chunking...")
                transcript = self._recognize_chunked_audio(audio_path, language, recognizer)
                if transcript:
                    self.log_message("✅ Speech recognition successful with audio chunking")
                    return transcript
            except Exception as e5:
                self.log_message(f"⚠️ Fifth attempt (chunking) failed: {e5}")
            
            self.log_message("❌ All recognition strategies failed")
            return None
            
        except sr.UnknownValueError:
            self.log_message("❌ Speech recognition could not understand the audio")
            return None
        except Exception as e:
            self.log_message(f"❌ Error during speech recognition: {str(e)}")
            return None
    
    def _recognize_chunked_audio(self, audio_path, language, recognizer):
        """
        Attempt recognition by splitting audio into smaller chunks.
        
        Args:
            audio_path (str): Path to audio file
            language (str): Language code
            recognizer: Speech recognition recognizer instance
        
        Returns:
            str: Recognized text or None if failed
        """
        
        try:
            # Create a new temporary file for chunked audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as chunked_audio:
                chunked_audio_path = chunked_audio.name
            
            try:
                # Extract audio in smaller chunks (30 seconds each)
                (
                    ffmpeg.input(audio_path)
                    .output(chunked_audio_path, 
                           acodec='pcm_s16le',
                           ar=16000,
                           ac=1,
                           f='wav',
                           segment_time=30,
                           segment_format='wav',
                           reset_timestamps=1)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )
                
                # Try to recognize the chunked audio
                with sr.AudioFile(chunked_audio_path) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.record(source)
                
                transcript = recognizer.recognize_google(audio, language='en')
                return transcript
                
            finally:
                # Clean up chunked audio file
                if os.path.exists(chunked_audio_path):
                    os.unlink(chunked_audio_path)
                    
        except Exception as e:
            self.log_message(f"❌ Audio chunking failed: {e}")
            return None
    
    def compress_video(self):
        """Compress video using FFmpeg."""
        try:
            self.log_message("🚀 Starting video compression...")
            self.status_var.set("Compressing...")
            
            # Get settings
            input_file = self.input_file.get()
            output_file = self.output_file.get()
            crf = self.crf_value.get()
            preset = self.preset_value.get()
            audio_codec = self.audio_codec.get()
            audio_bitrate = self.audio_bitrate.get()
            
            # Build FFmpeg command
            input_stream = ffmpeg.input(input_file)
            
            output_options = {
                'vcodec': 'libx264',
                'crf': crf,
                'preset': preset,
                'acodec': audio_codec,
                'ab': audio_bitrate
            }
            
            # Add resolution scaling if specified
            if self.resize_video.get():
                width = int(self.resolution_width.get())
                height = int(self.resolution_height.get())
                output_options['vf'] = f'scale={width}:{height}'
                self.log_message(f"📐 Resizing to {width}x{height}")
            
            self.log_message(f"⚙️ Settings: CRF={crf}, Preset={preset}")
            self.log_message(f"🔊 Audio: {audio_codec} @ {audio_bitrate}")
            
            # Run FFmpeg
            (
                input_stream
                .output(output_file, **output_options)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # Success
            self.progress_var.set(100)
            self.log_message("✅ Compression completed successfully!")
            self.status_var.set("Compression completed successfully!")
            
            # Show file size comparison
            self.show_file_size_comparison(input_file, output_file)
            
            # Generate transcript if requested
            if self.generate_transcript.get():
                self.log_message("📝 Starting transcript generation...")
                transcript_file = self.transcript_file.get()
                language = self.transcript_language.get()
                
                transcript = self.create_transcript_from_video(input_file, transcript_file, language)
                
                if transcript:
                    self.log_message("✅ Transcript generation completed successfully!")
                    self.log_message(f"Transcript preview: {transcript[:100]}...")
                else:
                    self.log_message("❌ Transcript generation failed!")
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            self.log_message(f"❌ FFmpeg error: {error_msg}")
            self.status_var.set("Compression failed")
            messagebox.showerror("Compression Error", f"FFmpeg error:\n{error_msg}")
        except Exception as e:
            self.log_message(f"❌ Unexpected error: {str(e)}")
            self.status_var.set("Compression failed")
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
        finally:
            self.reset_controls()
    
    def show_file_size_comparison(self, input_file, output_file):
        """Show file size comparison after compression."""
        try:
            input_size = os.path.getsize(input_file) / (1024 * 1024)  # MB
            output_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            reduction = (1 - output_size / input_size) * 100
            
            self.log_message(f"📊 File Size Comparison:")
            self.log_message(f"   Original: {input_size:.1f} MB")
            self.log_message(f"   Compressed: {output_size:.1f} MB")
            self.log_message(f"   Reduction: {reduction:.1f}%")
            
        except Exception as e:
            self.log_message(f"⚠️ Could not calculate file sizes: {str(e)}")
    
    def reset_controls(self):
        """Reset control buttons to initial state."""
        self.compress_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def reset_form(self):
        """Reset all form fields to default values."""
        self.input_file.set("")
        self.output_file.set("")
        self.crf_value.set(28)
        self.preset_value.set("fast")
        self.resize_video.set(False)
        self.resolution_width.set("")
        self.resolution_height.set("")
        self.audio_codec.set("aac")
        self.audio_bitrate.set("128k")
        self.generate_transcript.set(False)
        self.transcript_file.set("")
        self.transcript_language.set("en-US")
        self.progress_var.set(0)
        self.clear_log()
        self.status_var.set("Ready")
        self.toggle_resolution_inputs()
        self.toggle_transcript_inputs()


def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = VideoCompressorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
