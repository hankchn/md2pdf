<p align="center"><b>简体中文</b> | <a href="./README_en.md">English</a></p>

# md2pdf Skill

这个 Skill 的目标不是普通 `.md -> PDF`，而是把 Markdown 先理解成结构化文档，再重新排版成适合交付和阅读的精美 PDF。

核心链路：

```text
Markdown -> 文档理解 -> 排版策略 -> 内容重构 -> HTML/CSS -> PDF 渲染 -> QA 检查 -> 最终 PDF
```

## 安装依赖

第一版脚本不依赖 Python 三方 Markdown/Jinja2 包；只需要 Python 3 和一个可用的 Chromium/Chrome。

推荐安装 Playwright，渲染更可控：

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

如果不安装 Python Playwright，脚本会尝试使用 Node Playwright；在 Codex Desktop 运行时，通常可以复用 runtime 里的共享 Node 依赖。最后才回退到本机 Chrome CLI。macOS 默认检测：

```text
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

如果 Chrome 在其它位置：

```bash
export MBPDF_CHROME_PATH="/path/to/chrome"
```

调试渲染器选择时可使用：

```bash
export MBPDF_DISABLE_PLAYWRIGHT=1
export MBPDF_DISABLE_NODE_PLAYWRIGHT=1
```

## 运行

在 `md2pdf` 目录中执行：

```bash
python3 scripts/main.py --input examples/input.md --output output.pdf --template elegant-report
```

保留中间 HTML，方便检查排版：

```bash
python3 scripts/main.py \
  --input examples/input.md \
  --output output.pdf \
  --template elegant-report \
  --title "AI 产品分析报告" \
  --author "Hank" \
  --date "2026-06-26" \
  --toc true \
  --debug
```

单独运行 QA：

```bash
python3 scripts/qa_pdf.py --pdf output.pdf --html output.html
```

如果要运行 `skill-creator` 的官方结构校验脚本，需要 `PyYAML`：

```bash
python3 -m pip install PyYAML
python3 /Users/yanghuan/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## 模板

- `elegant-report`：当前主模板，适合中文报告、PRD、研究分析、知识库文档。
- `product-doc`：产品文档模板骨架，当前复用基础版式并使用产品文档色彩 token。
- `research-brief`：研究简报模板骨架，当前复用基础版式并使用研究简报色彩 token。
- `knowledge-note`：知识笔记模板骨架，当前复用基础版式并使用知识笔记色彩 token。
- `auto`：根据文档关键词推断模板。

默认建议使用 `elegant-report`。

## 当前能力

- 解析标题、段落、无序列表、有序列表、引用块、代码块、表格、链接、图片。
- 支持 `> [!NOTE]`、`> [!IMPORTANT]`、`> [!WARNING]`、`> [!TIP]` callout。
- 自动封面、目录、页眉页脚、页码 CSS、A4 纵向页面。
- 自动识别文档类型并规范标题层级，目录按咨询报告方式区分章、节、点。
- 统一报告色彩系统，让封面、表格、图表、标题使用同一组主色和互补色。
- 页脚保持极简，只显示 `当前页 / 总页数`，不显示工具名或 `Page` 前缀。
- 生成 HTML/CSS 中间稿。
- 使用 Playwright 或 Chromium/Chrome 渲染 PDF，开启背景打印。
- 基础 PDF QA。

## 当前限制

- Markdown parser 是轻量实现，不覆盖所有 CommonMark 边界情况。
- 页码依赖 Chromium 对 CSS page counter 的支持，不同 Chrome 版本可能表现有差异。
- QA 目前以文件级检查为主，还没有自动检测文字溢出或大面积空白。
- `product-doc`、`research-brief`、`knowledge-note` 第一版是可运行模板骨架，还没有独立版式系统。

## 下一步计划

- 增加 PDF 回渲图片检查，检测空白页、表格过宽和代码块溢出。
- 为 PRD、研究简报、知识笔记分别扩展独立版式。
- 增加更完整的 Markdown parser 或可选 `markdown-it-py` 支持。
- 增加字体嵌入和品牌主题配置。

## Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/hankchn">
        <img src="https://github.com/hankchn.png" width="64" height="64" style="border-radius:50%;" alt="hankchn" />
        <br />
        <sub><b>hankchn</b></sub>
      </a>
      <br />
      <sub>Hank Yang</sub>
    </td>
    <td align="center">
      <a href="https://claude.ai">
        <img src="https://avatars.githubusercontent.com/u/76263028?s=200" width="64" height="64" style="border-radius:50%;" alt="Claude" />
        <br />
        <sub><b>Claude</b></sub>
      </a>
      <br />
      <sub>Anthropic AI</sub>
    </td>
  </tr>
</table>
