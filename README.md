# ArxmlToMarkdown

## 中文

将 AUTOSAR `.arxml` / `.dbc` 转成适合 **markmap** 的 Markdown 标题结构。

### 功能

- 命令行转换 `.arxml` / `.dbc` 为 `.md`
- GUI 选择 `.arxml` / `.dbc` 文件并一键生成 Markdown
- 生成结果可直接交给 markmap 生成思维导图

### 安装

```powershell
uv sync
```

### 命令行用法

```powershell
uv run arxml-to-markdown .\mcu.arxml .\mcu.md
uv run arxml-to-markdown .\AutoX_Sbw_Lane1.dbc .\AutoX_Sbw_Lane1.md
```

### GUI 用法

```powershell
uv run arxml-picker-ui
```

### 打包为 EXE（Windows）

```powershell
uv run --with pyinstaller pyinstaller --noconfirm --clean --onefile --windowed --name ArxmlPickerUI arxml_picker_ui.py
```

生成文件：

```text
.\dist\ArxmlPickerUI.exe
```

操作步骤：

1. 点击 **Browse...** 选择 `.arxml` 或 `.dbc` 文件
2. 如需自定义输出位置，点击 **Choose output...**
3. 选择界面语言后，点击 **Generate** 生成 Markdown 文件
4. 点击 **Open output folder** 打开输出目录，使用 markmap 查看生成文件

### markmap 示例

```powershell
npx markmap-cli .\mcu.md
```

### 输出说明

- `arxml_parsey.py` 会尽量提取 ARXML/DBC 中的层级节点并输出为 `# / ## / ###` 标题
- 如果是 ECUC 配置文件，会优先按配置容器结构生成
- 如果不是 ECUC 结构，会回退到 XML 层级中的 `SHORT-NAME` 树
- 对于 DBC 文件，会按节点分组，并在每个节点下按 **Receive / Send** 组织消息（`BO_`）和信号（`SG_`）

## English

Convert AUTOSAR `.arxml` / `.dbc` into Markdown headings that work with **markmap**.

### Features

- Convert `.arxml` / `.dbc` to `.md` from the command line
- Pick an `.arxml` / `.dbc` file in the GUI and generate Markdown
- Use the generated Markdown directly in markmap

### Install

```powershell
uv sync
```

### CLI

```powershell
uv run arxml-to-markdown .\mcu.arxml .\mcu.md
uv run arxml-to-markdown .\AutoX_Sbw_Lane1.dbc .\AutoX_Sbw_Lane1.md
```

### GUI

```powershell
uv run arxml-picker-ui
```

### Package as EXE (Windows)

```powershell
uv run --with pyinstaller pyinstaller --noconfirm --clean --onefile --windowed --name ArxmlPickerUI arxml_picker_ui.py
```

Output:

```text
.\dist\ArxmlPickerUI.exe
```

Steps:

1. Click **Browse...** to choose an `.arxml` or `.dbc` file
2. Click **Choose output...** if you want a custom output location
3. Choose the UI language, then click **Generate** to create the Markdown file
4. Click **Open output folder** to open the output directory and view the generated file with markmap

### markmap example

```powershell
npx markmap-cli .\mcu.md
```

### Output notes

- `arxml_parsey.py` tries to extract hierarchical nodes and write them as `# / ## / ###` headings
- For ECUC config files, it prefers the container structure
- If it is not ECUC-based, it falls back to the XML `SHORT-NAME` tree
- For DBC files, it groups by node, then organizes message (`BO_`) and signal (`SG_`) hierarchy under **Receive / Send**
