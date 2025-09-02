#!/usr/bin/env python3
"""
Video Compressor Tool - GUI Version
A modern graphical interface for the video compression tool.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import ffmpeg


class VideoCompressorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video Compressor Tool")
        self.root.geometry("900x800")
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
        
        # Progress and Log Section - Rows 17-21
        self.create_progress_section(scrollable_frame, 17)
        
        # Control Buttons - Row 22
        self.create_control_buttons(scrollable_frame, 22)
        
        # Status Bar - Row 23
        self.create_status_bar(scrollable_frame, 23)
        
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
        width_entry = ttk.Entry(res_frame, textvariable=self.resolution_width, width=10, font=('Arial', 10))
        width_entry.pack(side=tk.LEFT, padx=(8, 15))
        
        ttk.Label(res_frame, text="Height:", font=('Arial', 11)).pack(side=tk.LEFT)
        height_entry = ttk.Entry(res_frame, textvariable=self.resolution_height, width=10, font=('Arial', 10))
        height_entry.pack(side=tk.LEFT, padx=(8, 0))
        
        # Common resolutions - Row 11
        res_buttons_frame = ttk.Frame(parent)
        res_buttons_frame.grid(row=row+3, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
        
        ttk.Button(res_buttons_frame, text="720p", width=8,
                  command=lambda: self.set_resolution(1280, 720)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(res_buttons_frame, text="480p", width=8,
                  command=lambda: self.set_resolution(854, 480)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(res_buttons_frame, text="360p", width=8,
                  command=lambda: self.set_resolution(640, 360)).pack(side=tk.LEFT)
        
        # Initially disable resolution inputs
        self.toggle_resolution_inputs()
    
    def create_audio_section(self, parent, row):
        """Create audio settings section."""
        # Section header - Row 13
        audio_header = ttk.Label(parent, text="🔊 Audio Settings", style='Header.TLabel')
        audio_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        
        # Audio codec - Row 14
        ttk.Label(parent, text="Audio Codec:", font=('Arial', 11)).grid(
            row=row+1, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 15))
        codec_combo = ttk.Combobox(parent, textvariable=self.audio_codec,
                                   values=['aac', 'mp3', 'opus', 'vorbis'],
                                   state='readonly', width=20, font=('Arial', 10))
        codec_combo.grid(row=row+1, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 15))
        
        # Audio bitrate - Row 15
        ttk.Label(parent, text="Audio Bitrate:", font=('Arial', 11)).grid(
            row=row+2, column=0, sticky=tk.W, padx=(20, 15), pady=(0, 20))
        bitrate_combo = ttk.Combobox(parent, textvariable=self.audio_bitrate,
                                     values=['64k', '96k', '128k', '192k', '256k'],
                                     state='readonly', width=20, font=('Arial', 10))
        bitrate_combo.grid(row=row+2, column=1, sticky=tk.W, padx=(0, 15), pady=(0, 20))
    
    def create_progress_section(self, parent, row):
        """Create progress and log section."""
        # Section header - Row 17
        progress_header = ttk.Label(parent, text="📊 Progress & Log", style='Header.TLabel')
        progress_header.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 15), padx=20)
        
        # Progress bar - Row 18
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, 
                                           maximum=100, length=500)
        self.progress_bar.grid(row=row+1, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                              padx=20, pady=(0, 15))
        
        # Log text area - Row 19
        self.log_text = scrolledtext.ScrolledText(parent, height=10, width=80, font=('Consolas', 9))
        self.log_text.grid(row=row+2, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                          padx=20, pady=(0, 15))
        
        # Clear log button - Row 20
        ttk.Button(parent, text="Clear Log", command=self.clear_log, width=12).grid(
            row=row+3, column=0, sticky=tk.W, padx=20, pady=(0, 20))
    
    def create_control_buttons(self, parent, row):
        """Create control buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        # Compress button
        self.compress_button = ttk.Button(button_frame, text="🚀 Start Compression", 
                                         style='Success.TButton',
                                         command=self.start_compression,
                                         width=20)
        self.compress_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # Stop button
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop", 
                                     style='Warning.TButton',
                                     command=self.stop_compression,
                                     state=tk.DISABLED,
                                     width=15)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # Reset button
        ttk.Button(button_frame, text="🔄 Reset", command=self.reset_form, width=15).pack(side=tk.LEFT)
    
    def create_status_bar(self, parent, row):
        """Create status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 10))
        status_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                       padx=20, pady=(20, 0))
    
    def browse_input_file(self):
        """Browse for input video file."""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.wmv *.flv *.mkv *.webm *.m4v *.3gp *.mpg *.mpeg"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(title="Select Input Video", filetypes=filetypes)
        if filename:
            self.input_file.set(filename)
            # Auto-generate output filename
            self.auto_generate_output_name(filename)
    
    def browse_output_file(self):
        """Browse for output file location."""
        filetypes = [
            ("MP4 files", "*.mp4"),
            ("All files", "*.*")
        ]
        filename = filedialog.asksaveasfilename(title="Save Compressed Video As", 
                                              filetypes=filetypes, defaultextension=".mp4")
        if filename:
            self.output_file.set(filename)
    
    def auto_generate_output_name(self, input_path):
        """Auto-generate output filename based on input."""
        input_path = Path(input_path)
        output_name = f"{input_path.stem}_compressed{input_path.suffix}"
        output_path = input_path.parent / output_name
        self.output_file.set(str(output_path))
    
    def toggle_resolution_inputs(self):
        """Enable/disable resolution input fields."""
        if self.resize_video.get():
            self.resolution_width.set("1280")
            self.resolution_height.set("720")
        else:
            self.resolution_width.set("")
            self.resolution_height.set("")
    
    def set_resolution(self, width, height):
        """Set resolution values."""
        self.resize_video.set(True)
        self.resolution_width.set(str(width))
        self.resolution_height.set(str(height))
    
    def clear_log(self):
        """Clear the log text area."""
        self.log_text.delete(1.0, tk.END)
    
    def log_message(self, message):
        """Add message to log."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, check=True)
            self.status_var.set("FFmpeg: ✅ Available")
            self.log_message("✅ FFmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.status_var.set("FFmpeg: ❌ Not Found")
            self.log_message("❌ FFmpeg not found! Please install FFmpeg first.")
            messagebox.showerror("FFmpeg Not Found", 
                               "FFmpeg is not installed or not in PATH.\n\n"
                               "Please install FFmpeg from https://ffmpeg.org/download.html\n"
                               "and add it to your system PATH.")
    
    def validate_inputs(self):
        """Validate all input fields."""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input video file.")
            return False
        
        if not self.output_file.get():
            messagebox.showerror("Error", "Please specify an output file.")
            return False
        
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("Error", "Input file does not exist.")
            return False
        
        if self.resize_video.get():
            try:
                width = int(self.resolution_width.get())
                height = int(self.resolution_height.get())
                if width <= 0 or height <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter valid resolution dimensions.")
                return False
        
        return True
    
    def start_compression(self):
        """Start video compression in a separate thread."""
        if not self.validate_inputs():
            return
        
        # Disable controls
        self.compress_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        
        # Start compression thread
        self.compression_thread = threading.Thread(target=self.compress_video)
        self.compression_thread.daemon = True
        self.compression_thread.start()
    
    def stop_compression(self):
        """Stop video compression."""
        # This would need to be implemented with FFmpeg process management
        self.log_message("⚠️ Stop functionality not yet implemented")
        self.reset_controls()
    
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
        self.progress_var.set(0)
        self.clear_log()
        self.status_var.set("Ready")
        self.toggle_resolution_inputs()


def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = VideoCompressorGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()
