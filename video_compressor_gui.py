#!/usr/bin/env python3
"""
Video Compressor Tool - GUI Version
A modern graphical interface with explicit processing modes.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import ffmpeg

from video_compressor import convert_video_to_audio, generate_transcript


class VideoCompressorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Processing Tool")
        self.root.geometry("920x900")
        self.root.resizable(True, True)

        self.setup_styling()

        # Core file variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.operation_mode = tk.StringVar(value="compress")

        # Compression variables
        self.crf_value = tk.IntVar(value=28)
        self.preset_value = tk.StringVar(value="fast")
        self.resolution_width = tk.StringVar()
        self.resolution_height = tk.StringVar()
        self.resize_video = tk.BooleanVar(value=False)

        # Audio/transcript variables
        self.audio_codec = tk.StringVar(value="mp3")
        self.audio_bitrate = tk.StringVar(value="128k")
        self.transcript_file = tk.StringVar()
        self.transcript_language = tk.StringVar(value="en-US")

        self.create_widgets()
        self.check_ffmpeg()

    def setup_styling(self):
        """Setup modern styling for the GUI."""
        style = ttk.Style()
        style.theme_use('clam')

        self.root.configure(bg='#f0f0f0')

        style.configure('Title.TLabel', font=('Arial', 18, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'), foreground='#34495e')
        style.configure('Info.TLabel', font=('Arial', 10), foreground='#7f8c8d')
        style.configure('Custom.TCheckbutton', font=('Arial', 11))

    def create_widgets(self):
        """Create all GUI widgets with proper spacing."""
        main_canvas = tk.Canvas(self.root, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        scrollable_frame.columnconfigure(1, weight=1)

        title_label = ttk.Label(scrollable_frame, text="Video Processing Tool", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(20, 30), padx=20)

        self.create_file_section(scrollable_frame, 1)
        self.create_operation_section(scrollable_frame, 4)
        self.create_compression_section(scrollable_frame, 8)
        self.create_resolution_section(scrollable_frame, 12)
        self.create_audio_section(scrollable_frame, 17)
        self.create_transcript_section(scrollable_frame, 21)
        self.create_progress_section(scrollable_frame, 25)
        self.create_control_buttons(scrollable_frame, 30)
        self.create_status_bar(scrollable_frame, 31)

        main_canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.on_operation_change()

    def create_file_section(self, parent, row):
        """Create file selection section."""
        file_header = ttk.Label(parent, text="File Selection", style='Header.TLabel')
        file_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)

        ttk.Label(parent, text="Input Video:", font=('Arial', 11)).grid(
            row=row + 1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 10)
        )
        input_entry = ttk.Entry(parent, textvariable=self.input_file, width=60, font=('Arial', 10))
        input_entry.grid(row=row + 1, column=1, sticky=(tk.W, tk.E), padx=(0, 15), pady=(0, 10))
        ttk.Button(parent, text="Browse", command=self.browse_input_file, width=12).grid(
            row=row + 1, column=2, padx=(0, 20), pady=(0, 10)
        )

        self.output_label = ttk.Label(parent, text="Output Video:", font=('Arial', 11))
        self.output_label.grid(row=row + 2, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 20))
        output_entry = ttk.Entry(parent, textvariable=self.output_file, width=60, font=('Arial', 10))
        output_entry.grid(row=row + 2, column=1, sticky=(tk.W, tk.E), padx=(0, 15), pady=(0, 20))
        self.output_browse_button = ttk.Button(parent, text="Browse", command=self.browse_output_file, width=12)
        self.output_browse_button.grid(row=row + 2, column=2, padx=(0, 20), pady=(0, 20))

    def create_operation_section(self, parent, row):
        """Create operation mode section."""
        op_header = ttk.Label(parent, text="Choose Processing Flow", style='Header.TLabel')
        op_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)

        ttk.Radiobutton(
            parent,
            text="1) Compress the size",
            variable=self.operation_mode,
            value="compress",
            command=self.on_operation_change
        ).grid(row=row + 1, column=0, columnspan=3, sticky=tk.W, padx=(20, 15), pady=(0, 8))

        ttk.Radiobutton(
            parent,
            text="2) Convert Video to Audio",
            variable=self.operation_mode,
            value="audio",
            command=self.on_operation_change
        ).grid(row=row + 2, column=0, columnspan=3, sticky=tk.W, padx=(20, 15), pady=(0, 8))

        ttk.Radiobutton(
            parent,
            text="3) Convert Video to Audio and then Get Transcription",
            variable=self.operation_mode,
            value="audio_transcript",
            command=self.on_operation_change
        ).grid(row=row + 3, column=0, columnspan=3, sticky=tk.W, padx=(20, 15), pady=(0, 20))

    def create_compression_section(self, parent, row):
        """Create compression settings section."""
        self.compression_widgets = []

        comp_header = ttk.Label(parent, text="Compression Settings", style='Header.TLabel')
        comp_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        self.compression_widgets.append(comp_header)

        crf_label_title = ttk.Label(parent, text="Quality (CRF):", font=('Arial', 11))
        crf_label_title.grid(row=row + 1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 10))
        self.compression_widgets.append(crf_label_title)

        crf_frame = ttk.Frame(parent)
        crf_frame.grid(row=row + 1, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 10))
        self.compression_widgets.append(crf_frame)

        crf_scale = ttk.Scale(crf_frame, from_=18, to=30, orient=tk.HORIZONTAL, variable=self.crf_value, length=250)
        crf_scale.pack(side=tk.LEFT)

        self.crf_display_var = tk.StringVar(value="28")
        crf_label = ttk.Label(crf_frame, textvariable=self.crf_display_var, font=('Arial', 11, 'bold'))
        crf_label.pack(side=tk.LEFT, padx=(15, 0))

        def update_crf_label(*args):
            self.crf_display_var.set(str(self.crf_value.get()))

        self.crf_value.trace_add('write', update_crf_label)

        crf_info = ttk.Label(parent, text="18=High Quality, 28=Balanced, 30=High Compression", style='Info.TLabel')
        crf_info.grid(row=row + 1, column=2, sticky=tk.W, padx=(0, 20), pady=(0, 10))
        self.compression_widgets.append(crf_info)

        preset_label = ttk.Label(parent, text="Speed Preset:", font=('Arial', 11))
        preset_label.grid(row=row + 2, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 20))
        self.compression_widgets.append(preset_label)

        preset_combo = ttk.Combobox(
            parent,
            textvariable=self.preset_value,
            values=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'],
            state='readonly',
            width=20,
            font=('Arial', 10)
        )
        preset_combo.grid(row=row + 2, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
        self.compression_widgets.append(preset_combo)

        preset_info = ttk.Label(parent, text="Fast=Quick, Slow=Better Compression", style='Info.TLabel')
        preset_info.grid(row=row + 2, column=2, sticky=tk.W, padx=(0, 20), pady=(0, 20))
        self.compression_widgets.append(preset_info)

    def create_resolution_section(self, parent, row):
        """Create resolution settings section."""
        self.resolution_widgets = []

        res_header = ttk.Label(parent, text="Resolution Settings", style='Header.TLabel')
        res_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        self.resolution_widgets.append(res_header)

        resize_check = ttk.Checkbutton(
            parent,
            text="Resize Video",
            variable=self.resize_video,
            command=self.toggle_resolution_inputs,
            style='Custom.TCheckbutton'
        )
        resize_check.grid(row=row + 1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 15))
        self.resolution_widgets.append(resize_check)

        res_frame = ttk.Frame(parent)
        res_frame.grid(row=row + 2, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 15))
        self.resolution_widgets.append(res_frame)

        ttk.Label(res_frame, text="Width:", font=('Arial', 11)).pack(side=tk.LEFT)
        self.width_entry = ttk.Entry(res_frame, textvariable=self.resolution_width, width=8, font=('Arial', 10))
        self.width_entry.pack(side=tk.LEFT, padx=(8, 15))

        ttk.Label(res_frame, text="Height:", font=('Arial', 11)).pack(side=tk.LEFT)
        self.height_entry = ttk.Entry(res_frame, textvariable=self.resolution_height, width=8, font=('Arial', 10))
        self.height_entry.pack(side=tk.LEFT, padx=(8, 0))

        res_info = ttk.Label(
            parent,
            text="Common: 1920x1080, 1280x720, 854x480",
            style='Info.TLabel'
        )
        res_info.grid(row=row + 3, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
        self.resolution_widgets.append(res_info)

        self.toggle_resolution_inputs()

    def create_audio_section(self, parent, row):
        """Create audio settings section."""
        self.audio_widgets = []

        audio_header = ttk.Label(parent, text="Audio Settings", style='Header.TLabel')
        audio_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        self.audio_widgets.append(audio_header)

        codec_label = ttk.Label(parent, text="Audio Codec:", font=('Arial', 11))
        codec_label.grid(row=row + 1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 10))
        self.audio_widgets.append(codec_label)

        codec_combo = ttk.Combobox(
            parent,
            textvariable=self.audio_codec,
            values=['mp3', 'aac', 'opus', 'vorbis'],
            state='readonly',
            width=20,
            font=('Arial', 10)
        )
        codec_combo.grid(row=row + 1, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 10))
        self.audio_widgets.append(codec_combo)

        bitrate_label = ttk.Label(parent, text="Audio Bitrate:", font=('Arial', 11))
        bitrate_label.grid(row=row + 2, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 20))
        self.audio_widgets.append(bitrate_label)

        bitrate_combo = ttk.Combobox(
            parent,
            textvariable=self.audio_bitrate,
            values=['64k', '96k', '128k', '192k', '256k'],
            state='readonly',
            width=20,
            font=('Arial', 10)
        )
        bitrate_combo.grid(row=row + 2, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
        self.audio_widgets.append(bitrate_combo)

    def create_transcript_section(self, parent, row):
        """Create transcript settings section."""
        self.transcript_widgets = []

        transcript_header = ttk.Label(parent, text="Transcript Settings", style='Header.TLabel')
        transcript_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        self.transcript_widgets.append(transcript_header)

        transcript_label = ttk.Label(parent, text="Transcript File:", font=('Arial', 11))
        transcript_label.grid(row=row + 1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 10))
        self.transcript_widgets.append(transcript_label)

        transcript_entry = ttk.Entry(parent, textvariable=self.transcript_file, width=40, font=('Arial', 10))
        transcript_entry.grid(row=row + 1, column=1, sticky=(tk.W, tk.E), padx=(0, 15), pady=(0, 10))
        self.transcript_widgets.append(transcript_entry)

        transcript_browse = ttk.Button(parent, text="Browse", command=self.browse_transcript_file, width=12)
        transcript_browse.grid(row=row + 1, column=2, padx=(0, 20), pady=(0, 10))
        self.transcript_widgets.append(transcript_browse)

        lang_label = ttk.Label(parent, text="Language:", font=('Arial', 11))
        lang_label.grid(row=row + 2, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 20))
        self.transcript_widgets.append(lang_label)

        language_combo = ttk.Combobox(
            parent,
            textvariable=self.transcript_language,
            values=['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'zh-CN'],
            state='readonly',
            width=20,
            font=('Arial', 10)
        )
        language_combo.grid(row=row + 2, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
        self.transcript_widgets.append(language_combo)

    def create_progress_section(self, parent, row):
        """Create progress and log section."""
        progress_header = ttk.Label(parent, text="Progress & Log", style='Header.TLabel')
        progress_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.grid(row=row + 1, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=20, pady=(0, 15))

        self.log_text = scrolledtext.ScrolledText(parent, height=10, width=80, font=('Consolas', 9))
        self.log_text.grid(row=row + 2, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=20, pady=(0, 15))

        ttk.Button(parent, text="Clear Log", command=self.clear_log, width=12).grid(
            row=row + 3, column=0, sticky=tk.W, padx=20, pady=(0, 20)
        )

    def create_control_buttons(self, parent, row):
        """Create control buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)

        self.process_button = ttk.Button(button_frame, text="Start", command=self.start_processing)
        self.process_button.pack(side=tk.LEFT, padx=(0, 15))

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15))

        reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_form)
        reset_button.pack(side=tk.LEFT)

    def create_status_bar(self, parent, row):
        """Create status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(parent, textvariable=self.status_var, font=('Arial', 10), foreground='#7f8c8d')
        status_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=20, pady=(0, 20))

    def _set_widget_state(self, widgets, enabled):
        """Enable or disable a list of widgets."""
        state = 'normal' if enabled else 'disabled'
        readonly_state = 'readonly' if enabled else 'disabled'

        for widget in widgets:
            try:
                if isinstance(widget, ttk.Combobox):
                    widget.configure(state=readonly_state)
                else:
                    widget.configure(state=state)
            except tk.TclError:
                pass

    def get_default_output_file(self, input_path):
        """Return output file path based on selected processing mode."""
        if not input_path:
            return ""

        base_name = os.path.splitext(input_path)[0]
        mode = self.operation_mode.get()

        if mode == 'compress':
            return f"{base_name}_compressed.mp4"

        extension_by_codec = {
            'mp3': '.mp3',
            'aac': '.aac',
            'opus': '.opus',
            'vorbis': '.ogg'
        }
        ext = extension_by_codec.get(self.audio_codec.get(), '.mp3')
        return f"{base_name}_audio{ext}"

    def set_default_transcript_path(self):
        """Set transcript output path from current output media path."""
        output_path = self.output_file.get()
        if output_path:
            base_name = os.path.splitext(output_path)[0]
            self.transcript_file.set(f"{base_name}_transcript.txt")

    def on_operation_change(self):
        """Handle operation mode changes and update UI state."""
        mode = self.operation_mode.get()

        if mode == 'compress':
            self.output_label.config(text="Output Video:")
            self.process_button.config(text="Start Compression")
            self._set_widget_state(self.compression_widgets, True)
            self._set_widget_state(self.resolution_widgets, True)
            self._set_widget_state(self.transcript_widgets, False)
        elif mode == 'audio':
            self.output_label.config(text="Output Audio:")
            self.process_button.config(text="Convert to Audio")
            self._set_widget_state(self.compression_widgets, False)
            self._set_widget_state(self.resolution_widgets, False)
            self._set_widget_state(self.transcript_widgets, False)
        else:
            self.output_label.config(text="Output Audio:")
            self.process_button.config(text="Audio + Transcription")
            self._set_widget_state(self.compression_widgets, False)
            self._set_widget_state(self.resolution_widgets, False)
            self._set_widget_state(self.transcript_widgets, True)

        current_input = self.input_file.get()
        if current_input:
            self.output_file.set(self.get_default_output_file(current_input))
            if mode == 'audio_transcript':
                self.set_default_transcript_path()
            else:
                self.transcript_file.set("")

        self.toggle_resolution_inputs()

    def toggle_resolution_inputs(self):
        """Enable/disable resolution input fields."""
        if self.operation_mode.get() != 'compress':
            self.width_entry.configure(state='disabled')
            self.height_entry.configure(state='disabled')
            return

        if self.resize_video.get():
            if not self.resolution_width.get():
                self.resolution_width.set("1280")
            if not self.resolution_height.get():
                self.resolution_height.set("720")
            self.width_entry.configure(state='normal')
            self.height_entry.configure(state='normal')
        else:
            self.resolution_width.set("")
            self.resolution_height.set("")
            self.width_entry.configure(state='disabled')
            self.height_entry.configure(state='disabled')

    def browse_input_file(self):
        """Browse for input video file."""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(title="Select Input Video", filetypes=filetypes)
        if filename:
            self.input_file.set(filename)
            self.output_file.set(self.get_default_output_file(filename))
            if self.operation_mode.get() == 'audio_transcript':
                self.set_default_transcript_path()

    def browse_output_file(self):
        """Browse for output file based on selected mode."""
        mode = self.operation_mode.get()

        if mode == 'compress':
            title = "Save Compressed Video As"
            filetypes = [("MP4 files", "*.mp4"), ("All files", "*.*")]
            extension = ".mp4"
        else:
            title = "Save Output Audio As"
            codec = self.audio_codec.get()
            ext_map = {'mp3': '.mp3', 'aac': '.aac', 'opus': '.opus', 'vorbis': '.ogg'}
            extension = ext_map.get(codec, '.mp3')
            filetypes = [
                ("Audio files", "*.mp3 *.aac *.opus *.ogg *.wav"),
                ("All files", "*.*")
            ]

        filename = filedialog.asksaveasfilename(
            title=title,
            filetypes=filetypes,
            defaultextension=extension
        )
        if filename:
            self.output_file.set(filename)
            if mode == 'audio_transcript':
                self.set_default_transcript_path()

    def browse_transcript_file(self):
        """Browse for transcript file location."""
        filename = filedialog.asksaveasfilename(
            title="Save Transcript As",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            defaultextension=".txt"
        )
        if filename:
            self.transcript_file.set(filename)

    def clear_log(self):
        """Clear the log text area."""
        self.log_text.delete(1.0, tk.END)

    def log_message(self, message):
        """Add message to log with timestamp."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
            self.log_message("FFmpeg found and ready")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log_message("FFmpeg not found. Please install FFmpeg and add it to system PATH.")
            messagebox.showerror(
                "FFmpeg Error",
                "FFmpeg not found. Please install FFmpeg and add it to system PATH.\n\n"
                "Download from: https://ffmpeg.org/download.html"
            )

    def start_processing(self):
        """Start selected operation in a separate thread."""
        if not self.input_file.get() or not self.output_file.get():
            messagebox.showerror("Error", "Please select input and output files.")
            return

        if self.operation_mode.get() == 'audio_transcript' and not self.transcript_file.get():
            messagebox.showerror("Error", "Please specify a transcript file location.")
            return

        self.process_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)

        processing_thread = threading.Thread(target=self.process_video)
        processing_thread.daemon = True
        processing_thread.start()

    def stop_processing(self):
        """Stop current operation."""
        self.log_message("Stop functionality is not yet implemented")
        self.reset_controls()

    def process_video(self):
        """Run the selected processing flow."""
        input_file = self.input_file.get()
        output_file = self.output_file.get()
        mode = self.operation_mode.get()

        try:
            if mode == 'compress':
                self.status_var.set("Compressing...")
                self.log_message("Starting video compression...")

                output_options = {
                    'vcodec': 'libx264',
                    'crf': self.crf_value.get(),
                    'preset': self.preset_value.get(),
                    'acodec': self.audio_codec.get(),
                    'ab': self.audio_bitrate.get()
                }

                if self.resize_video.get():
                    width = int(self.resolution_width.get())
                    height = int(self.resolution_height.get())
                    output_options['vf'] = f'scale={width}:{height}'
                    self.log_message(f"Resizing to {width}x{height}")

                (
                    ffmpeg
                    .input(input_file)
                    .output(output_file, **output_options)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )

                self.progress_var.set(100)
                self.log_message("Compression completed successfully")
                self.status_var.set("Compression completed")
                self.show_file_size_comparison(input_file, output_file)
                return

            self.status_var.set("Converting to audio...")
            self.log_message("Starting video to audio conversion...")
            success = convert_video_to_audio(
                input_file=input_file,
                output_file=output_file,
                audio_codec=self.audio_codec.get(),
                audio_bitrate=self.audio_bitrate.get()
            )

            if not success:
                raise RuntimeError("Audio conversion failed")

            self.progress_var.set(70 if mode == 'audio_transcript' else 100)
            self.log_message("Audio conversion completed successfully")
            self.show_file_size_comparison(input_file, output_file)

            if mode == 'audio_transcript':
                self.status_var.set("Generating transcript...")
                self.log_message("Starting transcription from converted audio...")
                transcript_text = generate_transcript(
                    input_file=output_file,
                    output_file=self.transcript_file.get(),
                    language=self.transcript_language.get()
                )

                if not transcript_text:
                    raise RuntimeError("Transcript generation failed")

                self.progress_var.set(100)
                self.log_message("Transcript generation completed successfully")
                self.log_message(f"Transcript preview: {transcript_text[:100]}...")
                self.status_var.set("Audio conversion and transcription completed")
            else:
                self.status_var.set("Audio conversion completed")

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            self.log_message(f"FFmpeg error: {error_msg}")
            self.status_var.set("Processing failed")
            messagebox.showerror("Processing Error", f"FFmpeg error:\n{error_msg}")
        except Exception as e:
            self.log_message(f"Unexpected error: {str(e)}")
            self.status_var.set("Processing failed")
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
        finally:
            self.reset_controls()

    def show_file_size_comparison(self, input_file, output_file):
        """Show file size comparison after processing."""
        try:
            input_size = os.path.getsize(input_file) / (1024 * 1024)
            output_size = os.path.getsize(output_file) / (1024 * 1024)
            reduction = (1 - output_size / input_size) * 100

            self.log_message("File Size Comparison:")
            self.log_message(f"   Original: {input_size:.1f} MB")
            self.log_message(f"   Output: {output_size:.1f} MB")
            self.log_message(f"   Reduction: {reduction:.1f}%")

        except Exception as e:
            self.log_message(f"Could not calculate file sizes: {str(e)}")

    def reset_controls(self):
        """Reset control buttons to initial state."""
        self.process_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def reset_form(self):
        """Reset all form fields to default values."""
        self.input_file.set("")
        self.output_file.set("")
        self.operation_mode.set("compress")

        self.crf_value.set(28)
        self.preset_value.set("fast")
        self.resize_video.set(False)
        self.resolution_width.set("")
        self.resolution_height.set("")

        self.audio_codec.set("mp3")
        self.audio_bitrate.set("128k")
        self.transcript_file.set("")
        self.transcript_language.set("en-US")

        self.progress_var.set(0)
        self.clear_log()
        self.status_var.set("Ready")

        self.on_operation_change()


def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = VideoCompressorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
