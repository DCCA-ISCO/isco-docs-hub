# Converting Documents to Markdown

All documents in the hub are written in Markdown. If your source document is in another format — Word, SharePoint, PDF, HTML — you need to convert it before adding it to `docs/manual/`. This page covers the most common formats.

---

## Tool: Pandoc

[Pandoc](https://pandoc.org/) is the recommended conversion tool for most formats. It is a free, open-source command-line utility.

**Install Pandoc:**

=== "Windows"
    Download the installer from [pandoc.org/installing.html](https://pandoc.org/installing.html), or via winget:
    ```
    winget install JohnMacFarlane.Pandoc
    ```

=== "macOS"
    ```
    brew install pandoc
    ```

=== "Linux (Fedora/RHEL)"
    ```
    sudo dnf install pandoc
    ```

=== "Linux (Debian/Ubuntu)"
    ```
    sudo apt install pandoc
    ```

---

## From Word (.docx)

Pandoc handles Word documents well, including headings, tables, bold/italic, and lists.

**Basic conversion:**
```
pandoc input.docx -o output.md
```

**With images extracted** (recommended if the document contains images):
```
pandoc input.docx --extract-media=./images -o output.md
```

This creates an `images/` folder alongside `output.md` containing all embedded images. Move both into `docs/manual/<your-doc>/` and update any image paths in the Markdown if needed.

**After conversion, check for:**

- Tables — Pandoc converts these to Markdown pipe tables, which render well in MkDocs.
- Footnotes — converted but may need cleanup.
- Text boxes and SmartArt — these do not convert; copy their content manually.
- Headers/footers — stripped automatically.

---

## From SharePoint

SharePoint has two common document types: **Word files stored in document libraries** and **modern SharePoint pages**.

### Word files in a SharePoint document library

1. Open the file in SharePoint.
2. Click **Download** (or open in Word desktop and save locally).
3. Convert with Pandoc as described above.

### Modern SharePoint pages (wiki-style pages)

SharePoint modern pages cannot be directly exported to Markdown. Use one of these approaches:

**Option A — Copy and paste (simplest):**

1. Open the SharePoint page.
2. Select all content on the page (`Ctrl+A` or `Cmd+A`).
3. Paste into a new `.md` file in your editor.
4. Clean up formatting manually — headings, lists, tables, and links will likely need adjustment.

**Option B — Save as HTML, then convert with Pandoc:**

1. Open the SharePoint page in your browser.
2. Use **File → Save As** (or `Ctrl+S`) and save as **Webpage, Complete** (`.html`).
3. Convert with Pandoc:
   ```
   pandoc input.html -o output.md
   ```
4. The output will include a lot of SharePoint navigation boilerplate — delete everything above the actual page content.

**Option C — Export to Word (if available):**

Some SharePoint pages support **Page Details → Export to Word** or a similar option depending on your SharePoint version. If available, download the Word file and convert with Pandoc.

---

## From PDF

Pandoc's PDF-to-Markdown support is limited. For best results:

**If the PDF was originally a Word document:**

1. Open the PDF in Word (Word can open PDFs directly): **File → Open → Browse → select the PDF**.
2. Word will convert it — review the result.
3. Save as `.docx` and convert with Pandoc.

**If the PDF is a scanned image (no selectable text):**

The text must be extracted via OCR. Use [Adobe Acrobat](https://acrobat.adobe.com/) (if licensed) or an online OCR tool. Export to Word or plain text, then convert.

**If the PDF has selectable text:**

1. Open in your browser or PDF reader.
2. Select all text (`Ctrl+A`) and copy.
3. Paste into a `.md` file and add Markdown formatting manually (headings with `#`, bold with `**`, lists with `-`).

---

## From HTML

```
pandoc input.html -o output.md
```

If the HTML page is a web page (not a local file), save it first:

1. Open the page in your browser.
2. **File → Save As → Webpage, HTML Only** (not "Complete" — that saves the full page with navigation).
3. Run Pandoc on the saved file.

---

## From Google Docs

1. In Google Docs, go to **File → Download → Microsoft Word (.docx)**.
2. Convert the downloaded `.docx` with Pandoc.

---

## Cleaning Up After Conversion

Regardless of the source format, review the converted Markdown before committing:

- **Remove boilerplate** — navigation bars, footers, page numbers, headers.
- **Fix headings** — ensure the document has a single `#` H1 at the top.
- **Check tables** — Pandoc pipe tables render correctly in MkDocs; verify alignment.
- **Check links** — internal links to other documents may break; update or remove them.
- **Check images** — verify image paths resolve correctly relative to the Markdown file.
- **Remove duplicate blank lines** — Pandoc sometimes inserts extra whitespace.

A quick preview before committing:
```
pip install mkdocs-material
mkdocs serve
```
Then open [http://localhost:8000](http://localhost:8000) to review the rendered output.

---

## Next Step

Once your document is converted and cleaned up, follow the [non-GitHub sourcing instructions](../index.md#from-sharepoint-local-files-or-other-non-github-sources) on the home page to add it to the hub.
