#!/usr/bin/env python3
"""
Video Processor Tool - GUI Version
A polished graphical interface for audio extraction, transcription, and AI summaries.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from video_compressor import (
    convert_video_to_audio,
    generate_transcript,
    load_dotenv_file,
    merge_videos,
    save_text_output,
    summarize_transcript_with_azure_openai,
)


class VideoCompressorGUI:
    def __init__(self, root):
        load_dotenv_file()
        self.root = root
        self.root.title("Studio Video Processor")
        self.root.geometry("1120x920")
        self.root.minsize(980, 760)
        self.root.resizable(True, True)
        try:
            self.root.state('zoomed')
        except tk.TclError:
            self.root.attributes('-zoomed', True)

        self.colors = {
            'page_bg': '#f4efe8',
            'card_bg': '#fffdf8',
            'card_border': '#dfd5c7',
            'card_muted': '#f7f1e8',
            'text': '#1f2937',
            'muted_text': '#6b7280',
            'heading': '#16324f',
            'accent': '#cc6b49',
            'accent_dark': '#a95032',
            'accent_soft': '#f6d9cf',
            'danger': '#c53030',
            'navy_soft': '#e6edf5',
        }

        self.input_files = []  # ordered list of file paths
        self.output_file = tk.StringVar()
        self.transcript_file = tk.StringVar()
        self.summary_file = tk.StringVar()
        self.operation_mode = tk.StringVar(value="audio")

        self.audio_codec = tk.StringVar(value="mp3")
        self.audio_bitrate = tk.StringVar(value="128k")
        self.transcript_language = tk.StringVar(value="en-US")

        self.azure_endpoint = tk.StringVar(value=os.getenv('AZURE_OPENAI_ENDPOINT', ''))
        self.azure_deployment = tk.StringVar(value=os.getenv('AZURE_OPENAI_DEPLOYMENT', ''))
        self.azure_model_name = tk.StringVar(value=os.getenv('AZURE_OPENAI_MODEL_NAME', ''))
        self.azure_api_version = tk.StringVar(value=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'))
        self.azure_api_key = tk.StringVar(value=os.getenv('AZURE_OPENAI_API_KEY', ''))

        self.summary_title_var = tk.StringVar(value="Convert video into an audio-only file")
        self.summary_detail_var = tk.StringVar(value="Creates an audio-only file using your selected codec and bitrate.")
        self.status_var = tk.StringVar(value="Ready")

        self.operation_cards = {}
        self.audio_widgets = []
        self.transcript_widgets = []
        self.summary_widgets = []

        self.setup_styling()
        self.create_widgets()
        self.bind_variable_updates()
        self.check_ffmpeg()

    def setup_styling(self):
        """Configure ttk styles for a refined interface."""
        self.root.configure(bg=self.colors['page_bg'])

        style = ttk.Style()
        style.theme_use('clam')

        base_font = ('Segoe UI', 10)
        header_font = ('Segoe UI Semibold', 12)
        button_font = ('Segoe UI Semibold', 10)

        style.configure('.', font=base_font)
        style.configure('Card.TFrame', background=self.colors['card_bg'])
        style.configure('CardBody.TFrame', background=self.colors['card_bg'])
        style.configure('CardMuted.TFrame', background=self.colors['card_muted'])
        style.configure('HeroTitle.TLabel', background=self.colors['heading'], foreground='white', font=('Segoe UI Semibold', 26))
        style.configure('HeroText.TLabel', background=self.colors['heading'], foreground='#d9e4f1', font=('Segoe UI', 11))
        style.configure('CardTitle.TLabel', background=self.colors['card_bg'], foreground=self.colors['heading'], font=header_font)
        style.configure('Body.TLabel', background=self.colors['card_bg'], foreground=self.colors['text'], font=('Segoe UI', 10))
        style.configure('Muted.TLabel', background=self.colors['card_bg'], foreground=self.colors['muted_text'], font=('Segoe UI', 9))
        style.configure('SummaryTitle.TLabel', background=self.colors['navy_soft'], foreground=self.colors['heading'], font=('Segoe UI Semibold', 13))
        style.configure('SummaryText.TLabel', background=self.colors['navy_soft'], foreground=self.colors['text'], font=('Segoe UI', 10))
        style.configure('Accent.TButton', background=self.colors['accent'], foreground='white', borderwidth=0, padding=(14, 10), font=button_font)
        style.map('Accent.TButton', background=[('active', self.colors['accent_dark']), ('disabled', '#ccb7ae')])
        style.configure('Secondary.TButton', background=self.colors['navy_soft'], foreground=self.colors['heading'], borderwidth=0, padding=(12, 10), font=button_font)
        style.map('Secondary.TButton', background=[('active', '#d8e4f1'), ('disabled', '#ece7df')])
        style.configure('Danger.TButton', background='#f2ddd7', foreground=self.colors['danger'], borderwidth=0, padding=(12, 10), font=button_font)
        style.map('Danger.TButton', background=[('active', '#ebc8bf'), ('disabled', '#ece7df')])
        style.configure('Modern.TEntry', fieldbackground='white', foreground=self.colors['text'], bordercolor=self.colors['card_border'], lightcolor=self.colors['card_border'], darkcolor=self.colors['card_border'], padding=8)
        style.configure('Modern.TCombobox', fieldbackground='white', foreground=self.colors['text'], bordercolor=self.colors['card_border'], lightcolor=self.colors['card_border'], darkcolor=self.colors['card_border'], padding=6)
        style.configure('Modern.Horizontal.TProgressbar', troughcolor='#eadfce', background=self.colors['accent'], bordercolor='#eadfce', lightcolor=self.colors['accent'], darkcolor=self.colors['accent'])

    def bind_variable_updates(self):
        """Keep derived UI state in sync with user input."""
        self.operation_mode.trace_add('write', self.on_operation_var_change)
        self.audio_codec.trace_add('write', self.on_audio_setting_change)

    def create_widgets(self):
        """Create the full UI."""
        main_canvas = tk.Canvas(self.root, bg=self.colors['page_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient='vertical', command=main_canvas.yview)
        content = tk.Frame(main_canvas, bg=self.colors['page_bg'])

        content.bind('<Configure>', lambda e: main_canvas.configure(scrollregion=main_canvas.bbox('all')))
        canvas_window = main_canvas.create_window((0, 0), window=content, anchor='nw')
        main_canvas.configure(yscrollcommand=scrollbar.set)
        main_canvas.bind('<Configure>', lambda e: main_canvas.itemconfig(canvas_window, width=e.width))

        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        self.create_hero(content)

        left_column = tk.Frame(content, bg=self.colors['page_bg'])
        right_column = tk.Frame(content, bg=self.colors['page_bg'])
        left_column.grid(row=1, column=0, sticky='nsew', padx=(24, 12), pady=(0, 24))
        right_column.grid(row=1, column=1, sticky='nsew', padx=(12, 24), pady=(0, 24))
        left_column.columnconfigure(0, weight=1)
        right_column.columnconfigure(0, weight=1)

        self.create_file_section(left_column, 0)
        self.create_operation_section(left_column, 1)
        self.create_output_section(left_column, 2)
        self.create_audio_section(left_column, 3)

        self.create_summary_card(right_column, 0)
        self.create_transcript_section(right_column, 1)
        self.create_ai_result_section(right_column, 2)
        self.create_progress_section(right_column, 3)
        self.create_control_buttons(right_column, 4)
        self.create_status_bar(right_column, 5)

        main_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y', padx=(0, 10), pady=10)

        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

        main_canvas.bind_all('<MouseWheel>', _on_mousewheel)
        self.on_operation_change()

    def create_hero(self, parent):
        hero = tk.Frame(parent, bg=self.colors['heading'], padx=28, pady=24)
        hero.grid(row=0, column=0, columnspan=2, sticky='ew', padx=24, pady=(24, 20))
        hero.columnconfigure(0, weight=1)

        ttk.Label(hero, text='Studio Video Processor', style='HeroTitle.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(
            hero,
            text='Extract audio, generate transcripts directly from video, or create transcript summaries with Azure OpenAI.',
            style='HeroText.TLabel'
        ).grid(row=1, column=0, sticky='w', pady=(8, 0))

        badge = tk.Label(
            hero,
            text='3 transcription workflows',
            bg='#f6d9cf',
            fg='#a95032',
            font=('Segoe UI Semibold', 10),
            padx=14,
            pady=8,
        )
        badge.grid(row=0, column=1, rowspan=2, sticky='e')

    def create_card(self, parent, row, title, subtitle=None, body_style='CardBody.TFrame'):
        outer = tk.Frame(parent, bg=self.colors['card_border'], padx=1, pady=1)
        outer.grid(row=row, column=0, sticky='ew', pady=(0, 18))
        outer.columnconfigure(0, weight=1)

        inner = ttk.Frame(outer, style='Card.TFrame', padding=18)
        inner.grid(row=0, column=0, sticky='ew')
        inner.columnconfigure(1, weight=1)

        ttk.Label(inner, text=title, style='CardTitle.TLabel').grid(row=0, column=0, sticky='w')
        if subtitle:
            ttk.Label(inner, text=subtitle, style='Muted.TLabel').grid(row=1, column=0, columnspan=2, sticky='w', pady=(4, 12))
            body_row = 2
        else:
            body_row = 1

        body = ttk.Frame(inner, style=body_style)
        body.grid(row=body_row, column=0, columnspan=2, sticky='ew')
        body.columnconfigure(1, weight=1)
        return body, inner

    def create_file_section(self, parent, row):
        body, _ = self.create_card(
            parent, row,
            'Source Videos',
            'Add one or more video parts. Multiple files are merged in listed order before processing.',
        )
        body.columnconfigure(0, weight=1)

        # File list with scrollbar
        list_frame = tk.Frame(body, bg=self.colors['card_bg'])
        list_frame.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        list_frame.columnconfigure(0, weight=1)

        self.files_listbox = tk.Listbox(
            list_frame,
            height=4,
            selectmode=tk.SINGLE,
            bg='#fffaf3',
            fg=self.colors['text'],
            selectbackground=self.colors['accent_soft'],
            selectforeground=self.colors['heading'],
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['card_border'],
            activestyle='none',
        )
        list_sb = ttk.Scrollbar(list_frame, orient='vertical', command=self.files_listbox.yview)
        self.files_listbox.configure(yscrollcommand=list_sb.set)
        self.files_listbox.grid(row=0, column=0, sticky='ew')
        list_sb.grid(row=0, column=1, sticky='ns')

        btn_row = ttk.Frame(body, style='CardBody.TFrame')
        btn_row.grid(row=1, column=0, sticky='w', pady=(4, 0))
        ttk.Button(btn_row, text='Add Files', style='Secondary.TButton', command=self.add_input_files).pack(side=tk.LEFT)
        ttk.Button(btn_row, text='Remove Selected', style='Secondary.TButton', command=self.remove_selected_file).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(btn_row, text='Move Up', style='Secondary.TButton', command=self.move_file_up).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(btn_row, text='Move Down', style='Secondary.TButton', command=self.move_file_down).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(btn_row, text='Clear All', style='Danger.TButton', command=self.clear_all_files).pack(side=tk.LEFT, padx=(8, 0))

        self.merge_note = ttk.Label(body, text='No files added.', style='Muted.TLabel')
        self.merge_note.grid(row=2, column=0, sticky='w', pady=(6, 0))

    def create_operation_section(self, parent, row):
        body, _ = self.create_card(parent, row, 'Workflow', 'Choose how the uploaded video should be processed.')
        body.columnconfigure(0, weight=1)

        options = [
            ('audio', 'Convert Video to Audio', 'Create an audio-only file from the uploaded video.'),
            ('transcript', 'Transcribe Video', 'Generate transcript text directly from the uploaded video.'),
            ('transcript_summary', 'Transcribe and Summarize with AI', 'Create a transcript first, then generate an AI summary using Azure OpenAI.'),
        ]

        for index, (value, title, description) in enumerate(options):
            card = tk.Frame(body, bg=self.colors['card_muted'], padx=14, pady=12)
            card.grid(row=index, column=0, sticky='ew', pady=(0, 10))
            card.columnconfigure(1, weight=1)
            self.operation_cards[value] = {'frame': card}

            radio = tk.Radiobutton(
                card,
                text='',
                variable=self.operation_mode,
                value=value,
                command=self.on_operation_change,
                bg=self.colors['card_muted'],
                activebackground=self.colors['card_muted'],
                highlightthickness=0,
                bd=0,
            )
            radio.grid(row=0, column=0, rowspan=2, sticky='n', padx=(0, 10))

            title_label = tk.Label(card, text=title, bg=self.colors['card_muted'], fg=self.colors['heading'], font=('Segoe UI Semibold', 11))
            title_label.grid(row=0, column=1, sticky='w')
            desc_label = tk.Label(card, text=description, bg=self.colors['card_muted'], fg=self.colors['muted_text'], font=('Segoe UI', 9), anchor='w', justify='left')
            desc_label.grid(row=1, column=1, sticky='w', pady=(4, 0))

            self.operation_cards[value]['radio'] = radio
            self.operation_cards[value]['title'] = title_label
            self.operation_cards[value]['description'] = desc_label

    def create_output_section(self, parent, row):
        body, _ = self.create_card(parent, row, 'Output Files', 'Only the outputs required by the selected workflow are enabled.')

        self.output_audio_label = ttk.Label(body, text='Audio file', style='Body.TLabel')
        self.output_audio_label.grid(row=0, column=0, sticky='w', pady=(0, 10), padx=(0, 12))
        self.audio_output_entry = ttk.Entry(body, textvariable=self.output_file, style='Modern.TEntry')
        self.audio_output_entry.grid(row=0, column=1, sticky='ew', pady=(0, 10), padx=(0, 12))
        self.audio_output_button = ttk.Button(body, text='Save As', style='Secondary.TButton', command=self.browse_output_file)
        self.audio_output_button.grid(row=0, column=2, sticky='ew', pady=(0, 10))
        self.audio_widgets.extend([self.output_audio_label, self.audio_output_entry, self.audio_output_button])

        transcript_label = ttk.Label(body, text='Transcript file', style='Body.TLabel')
        transcript_label.grid(row=1, column=0, sticky='w', pady=(0, 10), padx=(0, 12))
        transcript_entry = ttk.Entry(body, textvariable=self.transcript_file, style='Modern.TEntry')
        transcript_entry.grid(row=1, column=1, sticky='ew', pady=(0, 10), padx=(0, 12))
        transcript_button = ttk.Button(body, text='Save As', style='Secondary.TButton', command=self.browse_transcript_file)
        transcript_button.grid(row=1, column=2, sticky='ew', pady=(0, 10))
        self.transcript_widgets.extend([transcript_label, transcript_entry, transcript_button])

        summary_label = ttk.Label(body, text='Summary file', style='Body.TLabel')
        summary_label.grid(row=2, column=0, sticky='w', pady=(0, 10), padx=(0, 12))
        summary_entry = ttk.Entry(body, textvariable=self.summary_file, style='Modern.TEntry')
        summary_entry.grid(row=2, column=1, sticky='ew', pady=(0, 10), padx=(0, 12))
        summary_button = ttk.Button(body, text='Save As', style='Secondary.TButton', command=self.browse_summary_file)
        summary_button.grid(row=2, column=2, sticky='ew', pady=(0, 10))
        self.summary_widgets.extend([summary_label, summary_entry, summary_button])

    def create_audio_section(self, parent, row):
        body, _ = self.create_card(parent, row, 'Audio Export Settings', 'Used only when audio output is requested.')

        codec_label = ttk.Label(body, text='Audio codec', style='Body.TLabel')
        codec_label.grid(row=0, column=0, sticky='w', pady=(0, 10), padx=(0, 12))
        codec_combo = ttk.Combobox(body, textvariable=self.audio_codec, values=['mp3', 'aac', 'opus', 'vorbis'], state='readonly', style='Modern.TCombobox')
        codec_combo.grid(row=0, column=1, sticky='w', pady=(0, 10))
        bitrate_label = ttk.Label(body, text='Audio bitrate', style='Body.TLabel')
        bitrate_label.grid(row=1, column=0, sticky='w', pady=(0, 10), padx=(0, 12))
        bitrate_combo = ttk.Combobox(body, textvariable=self.audio_bitrate, values=['64k', '96k', '128k', '192k', '256k'], state='readonly', style='Modern.TCombobox')
        bitrate_combo.grid(row=1, column=1, sticky='w', pady=(0, 10))
        note = ttk.Label(body, text='MP3 at 128k is a practical default for speech-heavy videos.', style='Muted.TLabel')
        note.grid(row=2, column=0, columnspan=2, sticky='w')
        self.audio_widgets.extend([codec_label, codec_combo, bitrate_label, bitrate_combo, note])

    def create_summary_card(self, parent, row):
        body, _ = self.create_card(parent, row, 'Selected Workflow', body_style='CardMuted.TFrame')
        body.columnconfigure(0, weight=1)
        ttk.Label(body, textvariable=self.summary_title_var, style='SummaryTitle.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(body, textvariable=self.summary_detail_var, style='SummaryText.TLabel', wraplength=420, justify='left').grid(row=1, column=0, sticky='w', pady=(8, 0))

    def create_transcript_section(self, parent, row):
        body, _ = self.create_card(parent, row, 'Transcription Settings', 'Configure transcript language for transcript-based workflows.')

        language_label = ttk.Label(body, text='Language', style='Body.TLabel')
        language_label.grid(row=0, column=0, sticky='w', padx=(0, 12))
        language_combo = ttk.Combobox(
            body,
            textvariable=self.transcript_language,
            values=['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'zh-CN'],
            state='readonly',
            style='Modern.TCombobox',
        )
        language_combo.grid(row=0, column=1, sticky='w')
        note = ttk.Label(body, text='The app extracts audio from video and transcribes it in fixed chunks for better reliability on long files.', style='Muted.TLabel', wraplength=420, justify='left')
        note.grid(row=1, column=0, columnspan=2, sticky='w', pady=(10, 0))
        self.transcript_widgets.extend([language_label, language_combo, note])

    def create_ai_result_section(self, parent, row):
        body, _ = self.create_card(parent, row, 'AI Refined Transcription', 'When you run the AI workflow, the generated refined text appears here and can be copied.')
        body.columnconfigure(0, weight=1)

        self.ai_result_text = scrolledtext.ScrolledText(
            body,
            height=14,
            wrap=tk.WORD,
            bg='#fffaf3',
            fg=self.colors['text'],
            insertbackground=self.colors['heading'],
            relief=tk.FLAT,
            borderwidth=0,
            font=('Consolas', 9),
            padx=10,
            pady=10,
        )
        self.ai_result_text.grid(row=0, column=0, sticky='nsew')
        self.ai_result_text.insert('1.0', 'AI-generated refined transcription will appear here after running the summarize workflow.')

        button_row = ttk.Frame(body, style='CardBody.TFrame')
        button_row.grid(row=1, column=0, sticky='w', pady=(10, 0))
        ttk.Button(button_row, text='Copy Text', style='Secondary.TButton', command=self.copy_ai_result).pack(side=tk.LEFT)
        ttk.Button(button_row, text='Clear', style='Secondary.TButton', command=self.clear_ai_result).pack(side=tk.LEFT, padx=(10, 0))

    def create_progress_section(self, parent, row):
        body, _ = self.create_card(parent, row, 'Activity', 'Live processing status and event log.')
        body.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(body, variable=self.progress_var, maximum=100, style='Modern.Horizontal.TProgressbar')
        self.progress_bar.grid(row=0, column=0, sticky='ew', pady=(0, 12))

        self.log_text = scrolledtext.ScrolledText(
            body,
            height=13,
            wrap=tk.WORD,
            bg='#fffaf3',
            fg=self.colors['text'],
            insertbackground=self.colors['heading'],
            relief=tk.FLAT,
            borderwidth=0,
            font=('Consolas', 9),
            padx=10,
            pady=10,
        )
        self.log_text.grid(row=1, column=0, sticky='nsew')

    def create_control_buttons(self, parent, row):
        body, _ = self.create_card(parent, row, 'Actions')

        self.process_button = ttk.Button(body, text='Convert to Audio', style='Accent.TButton', command=self.start_processing)
        self.process_button.grid(row=0, column=0, sticky='w', padx=(0, 12))
        self.stop_button = ttk.Button(body, text='Stop', style='Danger.TButton', command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, sticky='w', padx=(0, 12))
        ttk.Button(body, text='Clear Log', style='Secondary.TButton', command=self.clear_log).grid(row=0, column=2, sticky='w', padx=(0, 12))
        ttk.Button(body, text='Reset Form', style='Secondary.TButton', command=self.reset_form).grid(row=0, column=3, sticky='w')

    def create_status_bar(self, parent, row):
        body, _ = self.create_card(parent, row, 'Status')
        ttk.Label(body, textvariable=self.status_var, style='Body.TLabel').grid(row=0, column=0, sticky='w')

    @property
    def _primary_input(self):
        return self.input_files[0] if self.input_files else ''

    def add_input_files(self):
        filetypes = [
            ('Video files', '*.mp4 *.avi *.mov *.mkv *.wmv *.flv'),
            ('All files', '*.*'),
        ]
        filenames = filedialog.askopenfilenames(title='Add Video Files', filetypes=filetypes)
        if filenames:
            for f in filenames:
                if f not in self.input_files:
                    self.input_files.append(f)
                    self.files_listbox.insert(tk.END, os.path.basename(f))
                    self.log_message(f'Added: {f}')
            self._update_merge_note()
            self.refresh_default_outputs()

    def remove_selected_file(self):
        selection = self.files_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        removed = self.input_files.pop(index)
        self.files_listbox.delete(index)
        self.log_message(f'Removed: {removed}')
        self._update_merge_note()
        self.refresh_default_outputs()

    def move_file_up(self):
        selection = self.files_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        idx = selection[0]
        self.input_files[idx - 1], self.input_files[idx] = self.input_files[idx], self.input_files[idx - 1]
        self._reload_listbox()
        self.files_listbox.selection_set(idx - 1)

    def move_file_down(self):
        selection = self.files_listbox.curselection()
        if not selection or selection[0] >= len(self.input_files) - 1:
            return
        idx = selection[0]
        self.input_files[idx], self.input_files[idx + 1] = self.input_files[idx + 1], self.input_files[idx]
        self._reload_listbox()
        self.files_listbox.selection_set(idx + 1)

    def clear_all_files(self):
        self.input_files.clear()
        self._reload_listbox()
        self._update_merge_note()
        self.refresh_default_outputs()

    def _reload_listbox(self):
        self.files_listbox.delete(0, tk.END)
        for f in self.input_files:
            self.files_listbox.insert(tk.END, os.path.basename(f))

    def _update_merge_note(self):
        count = len(self.input_files)
        if count == 0:
            self.merge_note.configure(text='No files added.')
        elif count == 1:
            self.merge_note.configure(text='1 file added. Processing will start directly.')
        else:
            self.merge_note.configure(
                text=f'{count} files added — they will be merged in the listed order before processing.'
            )

    def on_audio_setting_change(self, *args):
        current_input = self._primary_input
        if current_input and self.operation_mode.get() == 'audio':
            self.output_file.set(self.get_default_audio_file(current_input))

    def on_operation_var_change(self, *args):
        self.on_operation_change()

    def _set_widget_state(self, widgets, enabled):
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

    def update_operation_cards(self):
        for mode, card_widgets in self.operation_cards.items():
            active = mode == self.operation_mode.get()
            background = self.colors['accent_soft'] if active else self.colors['card_muted']
            card_widgets['frame'].configure(bg=background)
            card_widgets['radio'].configure(bg=background, activebackground=background)
            card_widgets['title'].configure(bg=background, fg=self.colors['heading'])
            card_widgets['description'].configure(bg=background, fg=self.colors['heading'] if active else self.colors['muted_text'])

    def update_summary(self):
        mode = self.operation_mode.get()
        if mode == 'audio':
            self.summary_title_var.set('Convert video into an audio-only file')
            self.summary_detail_var.set('Useful for extracting speech, interviews, lectures, or any audio content from a video source.')
        elif mode == 'transcript':
            self.summary_title_var.set('Generate a transcript directly from video')
            self.summary_detail_var.set('The app extracts audio from the video and writes the recognized speech to a transcript text file.')
        else:
            self.summary_title_var.set('Generate transcript, then summarize with Azure OpenAI')
            self.summary_detail_var.set('The app first creates a transcript from video, then sends that transcript to your Azure OpenAI deployment for a structured AI summary.')

    def get_default_audio_file(self, input_path):
        base_name = os.path.splitext(input_path)[0]
        extension_by_codec = {
            'mp3': '.mp3',
            'aac': '.aac',
            'opus': '.opus',
            'vorbis': '.ogg',
        }
        extension = extension_by_codec.get(self.audio_codec.get(), '.mp3')
        return f'{base_name}_audio{extension}'

    def get_default_transcript_file(self, input_path):
        base_name = os.path.splitext(input_path)[0]
        return f'{base_name}_transcript.txt'

    def get_default_summary_file(self, input_path):
        base_name = os.path.splitext(input_path)[0]
        return f'{base_name}_summary.txt'

    def refresh_default_outputs(self):
        input_path = self._primary_input
        if not input_path:
            return

        mode = self.operation_mode.get()
        if mode == 'audio':
            self.output_file.set(self.get_default_audio_file(input_path))
        elif mode == 'transcript':
            self.transcript_file.set(self.get_default_transcript_file(input_path))
            self.summary_file.set('')
        else:
            self.transcript_file.set(self.get_default_transcript_file(input_path))
            self.summary_file.set(self.get_default_summary_file(input_path))

    def on_operation_change(self):
        mode = self.operation_mode.get()

        if mode == 'audio':
            self.process_button.config(text='Convert to Audio')
            self._set_widget_state(self.audio_widgets, True)
            self._set_widget_state(self.transcript_widgets, False)
            self._set_widget_state(self.summary_widgets, False)
        elif mode == 'transcript':
            self.process_button.config(text='Generate Transcript')
            self._set_widget_state(self.audio_widgets, False)
            self._set_widget_state(self.transcript_widgets, True)
            self._set_widget_state(self.summary_widgets, False)
        else:
            self.process_button.config(text='Transcribe + Summarize')
            self._set_widget_state(self.audio_widgets, False)
            self._set_widget_state(self.transcript_widgets, True)
            self._set_widget_state(self.summary_widgets, True)

        self.refresh_default_outputs()
        self.update_summary()
        self.update_operation_cards()

    def browse_input_file(self):
        filetypes = [
            ('Video files', '*.mp4 *.avi *.mov *.mkv *.wmv *.flv'),
            ('All files', '*.*'),
        ]
        filename = filedialog.askopenfilename(title='Select Input Video', filetypes=filetypes)
        if filename:
            self.input_file.set(filename)
            self.refresh_default_outputs()
            self.log_message(f'Selected input file: {filename}')

    def browse_output_file(self):
        codec = self.audio_codec.get()
        ext_map = {'mp3': '.mp3', 'aac': '.aac', 'opus': '.opus', 'vorbis': '.ogg'}
        extension = ext_map.get(codec, '.mp3')
        filename = filedialog.asksaveasfilename(
            title='Save Output Audio As',
            filetypes=[('Audio files', '*.mp3 *.aac *.opus *.ogg *.wav'), ('All files', '*.*')],
            defaultextension=extension,
        )
        if filename:
            self.output_file.set(filename)

    def browse_transcript_file(self):
        filename = filedialog.asksaveasfilename(
            title='Save Transcript As',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')],
            defaultextension='.txt',
        )
        if filename:
            self.transcript_file.set(filename)

    def browse_summary_file(self):
        filename = filedialog.asksaveasfilename(
            title='Save AI Summary As',
            filetypes=[('Text files', '*.txt'), ('Markdown files', '*.md'), ('All files', '*.*')],
            defaultextension='.txt',
        )
        if filename:
            self.summary_file.set(filename)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def log_message(self, message):
        import datetime

        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f'[{timestamp}] {message}\n')
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def check_ffmpeg(self):
        try:
            import subprocess

            subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
            self.log_message('FFmpeg found and ready')
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log_message('FFmpeg not found. Please install FFmpeg and add it to system PATH.')
            messagebox.showerror(
                'FFmpeg Error',
                'FFmpeg not found. Please install FFmpeg and add it to system PATH.\n\n'
                'Download from: https://ffmpeg.org/download.html',
            )

    def validate_inputs(self):
        mode = self.operation_mode.get()
        if not self.input_files:
            return 'Please add at least one input video file.'

        if mode == 'audio' and not self.output_file.get():
            return 'Please select an output audio file.'

        if mode in {'transcript', 'transcript_summary'} and not self.transcript_file.get():
            return 'Please select a transcript output file.'

        if mode == 'transcript_summary':
            if not self.summary_file.get():
                return 'Please select a summary output file.'
            if not self.azure_endpoint.get().strip():
                return 'Missing AZURE_OPENAI_ENDPOINT in environment or .env.'
            if not self.azure_deployment.get().strip():
                return 'Missing AZURE_OPENAI_DEPLOYMENT in environment or .env.'
            if not self.azure_api_key.get().strip():
                return 'Missing AZURE_OPENAI_API_KEY in environment or .env.'

        return None

    def start_processing(self):
        validation_error = self.validate_inputs()
        if validation_error:
            messagebox.showerror('Error', validation_error)
            return

        self.process_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(8)
        self.status_var.set('Preparing task...')
        if self.operation_mode.get() == 'transcript_summary':
            self.clear_ai_result()

        processing_thread = threading.Thread(target=self.process_video)
        processing_thread.daemon = True
        processing_thread.start()

    def stop_processing(self):
        self.log_message('Stop functionality is not yet implemented')
        self.reset_controls()

    def process_video(self):
        input_files = self.input_files[:]
        mode = self.operation_mode.get()
        merged_temp = None

        try:
            if len(input_files) > 1:
                import tempfile as _tempfile
                self.status_var.set('Merging video parts...')
                self.log_message(f'Merging {len(input_files)} video parts in listed order...')
                self.progress_var.set(12)
                suffix = os.path.splitext(input_files[0])[1] or '.mp4'
                merged_fd, merged_temp = _tempfile.mkstemp(suffix=suffix)
                os.close(merged_fd)
                success = merge_videos(input_files, merged_temp)
                if not success:
                    raise RuntimeError(
                        'Video merge failed. Ensure all parts share the same codec and resolution.'
                    )
                self.log_message('Merge complete — processing merged file')
                input_file = merged_temp
            else:
                input_file = input_files[0]

            if mode == 'audio':
                self.status_var.set('Converting video to audio...')
                self.log_message('Starting video to audio conversion...')
                self.progress_var.set(35)

                success = convert_video_to_audio(
                    input_file=input_file,
                    output_file=self.output_file.get(),
                    audio_codec=self.audio_codec.get(),
                    audio_bitrate=self.audio_bitrate.get(),
                )
                if not success:
                    raise RuntimeError('Audio conversion failed')

                self.progress_var.set(100)
                self.status_var.set('Audio conversion completed')
                self.log_message('Audio conversion completed successfully')
                self.log_output_file('Audio file', self.output_file.get())
                return

            self.status_var.set('Generating transcript...')
            self.log_message('Starting transcription from video...')
            self.progress_var.set(40)

            transcript_text = generate_transcript(
                input_file=input_file,
                output_file=self.transcript_file.get(),
                language=self.transcript_language.get(),
            )
            if not transcript_text:
                raise RuntimeError('Transcript generation failed')

            self.log_message('Transcript generation completed successfully')
            self.log_output_file('Transcript file', self.transcript_file.get())

            if mode == 'transcript':
                self.progress_var.set(100)
                self.status_var.set('Transcription completed')
                return

            self.status_var.set('Summarizing transcript with Azure OpenAI...')
            self.progress_var.set(72)
            self.log_message('Submitting transcript to Azure OpenAI for summary...')

            summary_text = summarize_transcript_with_azure_openai(
                transcript_text=transcript_text,
                endpoint=self.azure_endpoint.get().strip(),
                deployment=self.azure_deployment.get().strip(),
                api_key=self.azure_api_key.get().strip(),
                api_version=self.azure_api_version.get().strip() or '2024-02-15-preview',
            )
            save_text_output(self.summary_file.get(), summary_text)
            self.set_ai_result(summary_text)

            self.progress_var.set(100)
            self.status_var.set('Transcription and AI summary completed')
            self.log_message('AI summary created successfully')
            if self.azure_model_name.get().strip():
                self.log_message(f"Model reference: {self.azure_model_name.get().strip()}")
            self.log_output_file('Summary file', self.summary_file.get())
            self.log_message(f'Summary preview: {summary_text[:140]}...')

        except Exception as exc:
            self.log_message(f'Unexpected error: {str(exc)}')
            self.status_var.set('Processing failed')
            messagebox.showerror('Error', f'Unexpected error:\n{str(exc)}')
        finally:
            if merged_temp and os.path.exists(merged_temp):
                try:
                    os.unlink(merged_temp)
                except OSError:
                    pass
            self.reset_controls()

    def log_output_file(self, label, file_path):
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.log_message(f'{label}: {file_path} ({size_mb:.2f} MB)')
        except OSError:
            self.log_message(f'{label}: {file_path}')

    def reset_controls(self):
        self.process_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def set_ai_result(self, text):
        self.ai_result_text.delete('1.0', tk.END)
        self.ai_result_text.insert('1.0', text)

    def clear_ai_result(self):
        self.ai_result_text.delete('1.0', tk.END)
        self.ai_result_text.insert('1.0', 'AI-generated refined transcription will appear here after running the summarize workflow.')

    def copy_ai_result(self):
        text = self.ai_result_text.get('1.0', tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log_message('AI refined transcription copied to clipboard')

    def reset_form(self):
        self.input_files.clear()
        self._reload_listbox()
        self._update_merge_note()
        self.output_file.set('')
        self.transcript_file.set('')
        self.summary_file.set('')
        self.operation_mode.set('audio')
        self.audio_codec.set('mp3')
        self.audio_bitrate.set('128k')
        self.transcript_language.set('en-US')
        self.azure_endpoint.set(os.getenv('AZURE_OPENAI_ENDPOINT', ''))
        self.azure_deployment.set(os.getenv('AZURE_OPENAI_DEPLOYMENT', ''))
        self.azure_model_name.set(os.getenv('AZURE_OPENAI_MODEL_NAME', ''))
        self.azure_api_version.set(os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'))
        self.azure_api_key.set(os.getenv('AZURE_OPENAI_API_KEY', ''))
        self.progress_var.set(0)
        self.clear_log()
        self.clear_ai_result()
        self.status_var.set('Ready')
        self.on_operation_change()
        self.log_message('Form reset to defaults')


def main():
    root = tk.Tk()
    app = VideoCompressorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
