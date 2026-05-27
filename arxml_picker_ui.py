from __future__ import annotations

import os
from pathlib import Path
from xml.parsers.expat import ExpatError

import tkinter as tk
from tkinter import filedialog, ttk

from arxml_parsey import NoExtractableNodesError, UnsupportedInputFormatError, input_to_markdown


TRANSLATIONS = {
    "English": {
        "window_title": "ARXML/DBC File Picker",
        "title": "ARXML/DBC to Markdown",
        "subtitle": "Choose an ARXML or DBC file and generate a markmap-ready Markdown outline.",
        "language_label": "Language:",
        "preview_title": "File preview",
        "input_file_label": "Input file:",
        "output_file_label": "Output file:",
        "arxml_path_label": "ARXML/DBC file path:",
        "output_path_label": "Output Markdown path:",
        "browse": "Browse...",
        "choose_output": "Browse...",
        "generate": "Generate",
        "open_output": "Open output folder",
        "browse_title": "Select an ARXML or DBC file",
        "save_title": "Select output Markdown file",
        "arxml_files": "ARXML files",
        "dbc_files": "DBC files",
        "supported_files": "Supported files",
        "markdown_files": "Markdown files",
        "all_files": "All files",
        "file_selected": "File selected. Click Generate to create Markdown.",
        "select_first": "Please select an ARXML or DBC file first.",
        "input_missing": "Input file does not exist.",
        "parse_failed": "Failed to parse the input file. Please check the file format.",
        "unsupported_format": "Unsupported file format. Please select a .arxml or .dbc file.",
        "no_nodes": "No extractable hierarchy nodes were found in the input file, so Markdown cannot be generated.",
        "read_write_error": "File read/write error: {error}",
        "success": "Markdown generated successfully.",
        "open_output_missing": "Generate a file first, then open the output folder.",
    },
    "中文": {
        "window_title": "ARXML/DBC 文件选择器",
        "title": "ARXML/DBC 转 Markdown",
        "subtitle": "选择 ARXML 或 DBC 文件并生成可直接用于 markmap 的 Markdown 大纲。",
        "language_label": "语言：",
        "preview_title": "文件预览",
        "input_file_label": "输入文件：",
        "output_file_label": "输出文件：",
        "arxml_path_label": "ARXML/DBC 文件路径：",
        "output_path_label": "输出 Markdown 路径：",
        "browse": "浏览...",
        "choose_output": "浏览...",
        "generate": "生成",
        "open_output": "打开输出文件夹",
        "browse_title": "选择 ARXML 或 DBC 文件",
        "save_title": "选择输出 Markdown 文件",
        "arxml_files": "ARXML 文件",
        "dbc_files": "DBC 文件",
        "supported_files": "支持的文件",
        "markdown_files": "Markdown 文件",
        "all_files": "所有文件",
        "file_selected": "已选择文件，点击生成即可生成 Markdown。",
        "select_first": "请先选择 ARXML 或 DBC 文件。",
        "input_missing": "输入文件不存在。",
        "parse_failed": "输入文件解析失败，请检查文件格式。",
        "unsupported_format": "不支持的文件格式，请选择 .arxml 或 .dbc 文件。",
        "no_nodes": "未在输入文件中找到可提取的层级节点，无法生成 Markdown。",
        "read_write_error": "文件读写失败：{error}",
        "success": "Markdown 生成成功。",
        "open_output_missing": "请先生成文件，再打开输出文件夹。",
    },
}


class ArxmlPickerUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.language_var = tk.StringVar(value="English")
        self.root.geometry("900x440")
        self.root.minsize(900, 440)
        self.root.resizable(False, False)

        self.path_var = tk.StringVar(value="")
        self.output_var = tk.StringVar(value="")
        self.input_name_var = tk.StringVar(value="—")
        self.output_name_var = tk.StringVar(value="—")
        self.status_var = tk.StringVar(value="")
        self.title_var = tk.StringVar(value="")
        self.subtitle_var = tk.StringVar(value="")
        self.language_label_var = tk.StringVar(value="")
        self.preview_title_var = tk.StringVar(value="")
        self.input_file_label_var = tk.StringVar(value="")
        self.output_file_label_var = tk.StringVar(value="")
        self.path_label_var = tk.StringVar(value="")
        self.output_label_var = tk.StringVar(value="")
        self.browse_button_var = tk.StringVar(value="")
        self.choose_output_button_var = tk.StringVar(value="")
        self.generate_button_var = tk.StringVar(value="")
        self.open_output_var = tk.StringVar(value="")
        self.language_choice_en = "English"
        self.language_choice_zh = "中文"
        self.status_key = "select_first"
        self.status_kwargs: dict[str, object] = {}
        self.browse_button: ttk.Button | None = None
        self.choose_output_button: ttk.Button | None = None
        self.generate_button: ttk.Button | None = None
        self.open_button: ttk.Button | None = None

        self._configure_styles()
        self._init_icon()
        self._build_layout()
        self._apply_language()
        self.update_previews()
        self._center_window()

    def _init_icon(self) -> None:
        icon = tk.PhotoImage(width=32, height=32)
        icon.put("#1d4ed8", to=(0, 0, 31, 31))
        icon.put("#3b82f6", to=(2, 2, 29, 29))
        icon.put("#ffffff", to=(8, 7, 24, 8))
        icon.put("#ffffff", to=(8, 13, 22, 14))
        icon.put("#ffffff", to=(8, 19, 20, 20))
        icon.put("#bfdbfe", to=(20, 4, 27, 11))
        self.app_icon = icon
        self.root.iconphoto(True, self.app_icon)

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        self.root.configure(bg="#f5f7fb")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("TLabel", background="#f5f7fb", foreground="#0f172a")
        style.configure("Header.TLabel", background="#f5f7fb", foreground="#0f172a", font=("Segoe UI", 16, "bold"))
        style.configure("SubHeader.TLabel", background="#f5f7fb", foreground="#64748b", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#f5f7fb", foreground="#0f172a", font=("Segoe UI", 10, "bold"))
        style.configure("Status.TLabel", background="#f5f7fb", foreground="#2563eb", font=("Segoe UI", 9))
        style.configure("Accent.TButton", background="#2563eb", foreground="#ffffff", padding=(12, 6))
        style.map("Accent.TButton", background=[("active", "#1d4ed8"), ("disabled", "#93c5fd")])
        style.configure("Soft.TButton", padding=(10, 6))
        style.map("Soft.TButton", background=[("active", "#e2e8f0")])

    def _center_window(self) -> None:
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max((screen_width - width) // 2, 0)
        y = max((screen_height - height) // 2, 0)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_layout(self) -> None:
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill=tk.BOTH, expand=True)

        header_row = ttk.Frame(frame)
        header_row.grid(row=0, column=0, sticky="we")
        header_row.columnconfigure(1, weight=1)

        tk.Label(header_row, image=self.app_icon, bg="#f5f7fb", bd=0, highlightthickness=0).grid(row=0, column=0, padx=(0, 12), sticky="w")
        ttk.Label(header_row, textvariable=self.title_var, style="Header.TLabel").grid(row=0, column=1, sticky="w")

        ttk.Label(header_row, textvariable=self.language_label_var).grid(row=0, column=2, padx=(16, 6), sticky="e")
        language_combo = ttk.Combobox(
            header_row,
            values=[self.language_choice_en, self.language_choice_zh],
            textvariable=self.language_var,
            state="readonly",
            width=12,
        )
        language_combo.grid(row=0, column=3, sticky="e")
        language_combo.bind("<<ComboboxSelected>>", self.on_language_change)

        ttk.Label(frame, textvariable=self.subtitle_var, style="SubHeader.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 14))

        preview_card = ttk.Frame(frame)
        preview_card.grid(row=2, column=0, sticky="we", pady=(0, 14))
        preview_card.columnconfigure(1, weight=1)
        ttk.Label(preview_card, textvariable=self.preview_title_var, style="CardTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(preview_card, textvariable=self.input_file_label_var).grid(row=1, column=0, sticky="w", padx=(0, 10))
        ttk.Label(preview_card, textvariable=self.input_name_var, style="SubHeader.TLabel").grid(row=1, column=1, sticky="w")
        ttk.Label(preview_card, textvariable=self.output_file_label_var).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=(4, 0))
        ttk.Label(preview_card, textvariable=self.output_name_var, style="SubHeader.TLabel").grid(row=2, column=1, sticky="w", pady=(4, 0))

        input_title = ttk.Label(frame, textvariable=self.path_label_var, style="CardTitle.TLabel")
        input_title.grid(row=3, column=0, sticky="w", pady=(0, 4))

        input_group = ttk.Frame(frame)
        input_group.grid(row=4, column=0, sticky="we", pady=(0, 12))
        input_group.columnconfigure(0, weight=1)

        path_entry = ttk.Entry(input_group, textvariable=self.path_var, state="readonly")
        path_entry.grid(row=0, column=0, padx=(0, 8), sticky="we")

        self.browse_button = ttk.Button(input_group, textvariable=self.browse_button_var, command=self.browse_file, style="Soft.TButton")
        self.browse_button.grid(row=0, column=1, sticky="e")

        output_title = ttk.Label(frame, textvariable=self.output_label_var, style="CardTitle.TLabel")
        output_title.grid(row=5, column=0, sticky="w", pady=(0, 4))

        output_group = ttk.Frame(frame)
        output_group.grid(row=6, column=0, sticky="we", pady=(0, 12))
        output_group.columnconfigure(0, weight=1)

        output_entry = ttk.Entry(output_group, textvariable=self.output_var, state="readonly")
        output_entry.grid(row=0, column=0, padx=(0, 8), sticky="we")

        self.choose_output_button = ttk.Button(output_group, textvariable=self.choose_output_button_var, command=self.choose_output_file, style="Soft.TButton")
        self.choose_output_button.grid(row=0, column=1, padx=(0, 0), sticky="e")

        footer = ttk.Frame(frame)
        footer.grid(row=7, column=0, sticky="we", pady=(4, 10))
        footer.columnconfigure(0, weight=1)

        ttk.Separator(footer, orient="horizontal").grid(row=0, column=0, columnspan=3, sticky="we", pady=(0, 10))
        self.open_button = ttk.Button(footer, textvariable=self.open_output_var, command=self.open_output_folder, style="Soft.TButton")
        self.open_button.grid(row=1, column=0, sticky="w")
        self.generate_button = ttk.Button(footer, textvariable=self.generate_button_var, command=self.generate_markdown, style="Accent.TButton")
        self.generate_button.grid(row=1, column=2, sticky="e")

        status_row = ttk.Frame(frame)
        status_row.grid(row=8, column=0, sticky="we")
        status_row.columnconfigure(0, weight=1)
        ttk.Label(status_row, textvariable=self.status_var, style="Status.TLabel", wraplength=820).grid(row=0, column=0, sticky="w")

        frame.columnconfigure(0, weight=1)

    def current_language(self) -> str:
        language = self.language_var.get()
        if language in TRANSLATIONS:
            return language
        return "English"

    def tr(self, key: str, **kwargs: object) -> str:
        text = TRANSLATIONS[self.current_language()][key]
        if kwargs:
            return text.format(**kwargs)
        return text

    def _apply_language(self) -> None:
        language = self.current_language()
        self.root.title(TRANSLATIONS[language]["window_title"])
        self.title_var.set(TRANSLATIONS[language]["title"])
        self.subtitle_var.set(TRANSLATIONS[language]["subtitle"])
        self.language_label_var.set(TRANSLATIONS[language]["language_label"])
        self.preview_title_var.set(TRANSLATIONS[language]["preview_title"])
        self.input_file_label_var.set(TRANSLATIONS[language]["input_file_label"])
        self.output_file_label_var.set(TRANSLATIONS[language]["output_file_label"])
        self.path_label_var.set(TRANSLATIONS[language]["arxml_path_label"])
        self.output_label_var.set(TRANSLATIONS[language]["output_path_label"])
        self.browse_button_var.set(TRANSLATIONS[language]["browse"])
        self.choose_output_button_var.set(TRANSLATIONS[language]["choose_output"])
        self.generate_button_var.set(TRANSLATIONS[language]["generate"])
        self.open_output_var.set(TRANSLATIONS[language]["open_output"])
        self._refresh_status()

    def set_status(self, key: str, **kwargs: object) -> None:
        self.status_key = key
        self.status_kwargs = kwargs
        self._refresh_status()

    def _refresh_status(self) -> None:
        self.status_var.set(self.tr(self.status_key, **self.status_kwargs))

    def on_language_change(self, _event: object) -> None:
        self._apply_language()
        self.update_actions()

    def has_input(self) -> bool:
        return bool(self.path_var.get().strip())

    def has_output(self) -> bool:
        return bool(self.output_var.get().strip())

    def update_actions(self) -> None:
        if self.generate_button is not None:
            self.generate_button.configure(state=tk.NORMAL if self.has_input() else tk.DISABLED)
        if self.open_button is not None:
            self.open_button.configure(state=tk.NORMAL if self.has_output() else tk.DISABLED)
        if self.choose_output_button is not None:
            self.choose_output_button.configure(state=tk.NORMAL if self.has_input() else tk.DISABLED)

    def update_previews(self) -> None:
        input_path = self.path_var.get().strip()
        output_path = self.output_var.get().strip()
        self.input_name_var.set(Path(input_path).name if input_path else "—")
        self.output_name_var.set(Path(output_path).name if output_path else "—")

    def browse_file(self) -> None:
        selected_path = filedialog.askopenfilename(
            title=self.tr("browse_title"),
            filetypes=[
                (self.tr("supported_files"), "*.arxml *.dbc"),
                (self.tr("arxml_files"), "*.arxml"),
                (self.tr("dbc_files"), "*.dbc"),
                (self.tr("all_files"), "*.*"),
            ],
        )
        if not selected_path:
            return

        input_path = Path(selected_path).resolve()
        output_path = input_path.with_suffix(".md")
        self.path_var.set(str(input_path))
        self.output_var.set(str(output_path))
        self.update_previews()
        self.set_status("file_selected")
        self.update_actions()

    def choose_output_file(self) -> None:
        input_raw = self.path_var.get().strip()
        initial_file = Path(input_raw).with_suffix(".md").name if input_raw else "output.md"
        selected_output = filedialog.asksaveasfilename(
            title=self.tr("save_title"),
            defaultextension=".md",
            initialfile=initial_file,
            filetypes=[(self.tr("markdown_files"), "*.md"), (self.tr("all_files"), "*.*")],
        )
        if not selected_output:
            return

        output_path = Path(selected_output).resolve()
        self.output_var.set(str(output_path))
        self.update_previews()
        self.set_status("file_selected" if self.has_input() else "select_first")
        self.update_actions()

    def generate_markdown(self) -> None:
        input_raw = self.path_var.get().strip()
        if not input_raw:
            self.set_status("select_first")
            return

        input_path = Path(input_raw)
        output_raw = self.output_var.get().strip()
        output_path = Path(output_raw) if output_raw else input_path.with_suffix(".md")

        try:
            input_to_markdown(input_path, output_path)
        except FileNotFoundError:
            self.set_status("input_missing")
            return
        except UnsupportedInputFormatError:
            self.set_status("unsupported_format")
            return
        except ExpatError:
            self.set_status("parse_failed")
            return
        except NoExtractableNodesError:
            self.set_status("no_nodes")
            return
        except OSError as exc:
            self.set_status("read_write_error", error=exc)
            return

        self.output_var.set(str(output_path.resolve()))
        self.update_previews()
        self.set_status("success")
        self.update_actions()

    def open_output_folder(self) -> None:
        output_raw = self.output_var.get().strip()
        if not output_raw:
            self.set_status("open_output_missing")
            return

        output_path = Path(output_raw)
        if not output_path.exists():
            self.set_status("open_output_missing")
            return

        os.startfile(str(output_path.parent))


def main() -> None:
    root = tk.Tk()
    ArxmlPickerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
