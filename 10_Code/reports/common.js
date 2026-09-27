// GRAIL reports — shared building blocks for both Word documents.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, Header, Footer, PageNumber, TableOfContents,
  convertInchesToTwip, LevelFormat, PositionalTab, PositionalTabAlignment,
  PositionalTabLeader,
} = require("docx");

// A4 with 20 mm margins -> usable width in DXA (1440 per inch)
const PAGE_W = 11906, PAGE_H = 16838;
const MARGIN = 1134;                      // 20 mm
const USABLE = PAGE_W - 2 * MARGIN;       // 9638 DXA
const USABLE_PX = Math.round((USABLE / 1440) * 96);   // px at 96 dpi

const INK = "1F2124", MUTED = "4A4D52", RULE = "C9CCD1";
const HDR_BG = "EEF2F7", ALT_BG = "F7F9FB";

function p(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text: String(text), ...opts.run })];
  return new Paragraph({
    children: runs,
    spacing: { before: opts.before ?? 0, after: opts.after ?? 120, line: opts.line ?? 276, lineRule: "auto" },
    alignment: opts.align,
    style: opts.style,
    indent: opts.indent,
    border: opts.border,
    keepNext: opts.keepNext,
  });
}

function h(text, level) {
  const lv = { 1: HeadingLevel.HEADING_1, 2: HeadingLevel.HEADING_2, 3: HeadingLevel.HEADING_3 }[level];
  return new Paragraph({
    text,
    heading: lv,
    spacing: { before: level === 1 ? 360 : 280, after: level === 1 ? 160 : 120 },
    keepNext: true,
  });
}

// Rich text: array of [text, {bold, italics, ...}] pairs
function rich(parts, opts = {}) {
  return p(parts.map(([t, o]) => new TextRun({ text: t, ...(o || {}) })), opts);
}

function mono(text) {
  return new TextRun({ text, font: "Consolas", size: 18 });
}

/**
 * A table. `rows[0]` is the header. `widths` are relative weights.
 * Both the table and every cell get an explicit DXA width, which is what makes
 * the table render the same in Word and in Google Docs.
 */
function table(rows, widths, opts = {}) {
  const n = rows[0].length;
  const w = widths || new Array(n).fill(1);
  const tot = w.reduce((a, b) => a + b, 0);
  const cols = w.map((x) => Math.round((x / tot) * USABLE));
  // make the columns sum exactly to the table width
  cols[cols.length - 1] += USABLE - cols.reduce((a, b) => a + b, 0);

  const mk = (cells, ri) =>
    new TableRow({
      tableHeader: ri === 0,
      cantSplit: true,
      children: cells.map((c, ci) => {
        const isHdr = ri === 0;
        const txt = c === null || c === undefined ? "" : String(c);
        const bold = isHdr || (opts.boldFirstCol && ci === 0);
        return new TableCell({
          width: { size: cols[ci], type: WidthType.DXA },
          shading: {
            type: ShadingType.CLEAR,
            fill: isHdr ? HDR_BG : (ri % 2 === 0 ? ALT_BG : "FFFFFF"),
            color: "auto",
          },
          margins: { top: 60, bottom: 60, left: 90, right: 90 },
          children: [
            new Paragraph({
              children: [new TextRun({ text: txt, bold, size: opts.size ?? 19, color: INK })],
              spacing: { before: 0, after: 0, line: 240, lineRule: "auto" },
              alignment:
                ci === 0 ? AlignmentType.LEFT
                  : (opts.alignRight === false ? AlignmentType.LEFT : AlignmentType.RIGHT),
            }),
          ],
        });
      }),
    });

  return new Table({
    columnWidths: cols,
    width: { size: USABLE, type: WidthType.DXA },
    rows: rows.map(mk),
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: RULE },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE },
      left: { style: BorderStyle.SINGLE, size: 4, color: RULE },
      right: { style: BorderStyle.SINGLE, size: 4, color: RULE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      insideVertical: { style: BorderStyle.SINGLE, size: 2, color: RULE },
    },
  });
}

function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, size: 17, color: MUTED, italics: true })],
    spacing: { before: 60, after: 240 },
    alignment: AlignmentType.CENTER,
  });
}

function tableCaption(text) {
  return new Paragraph({
    children: [new TextRun({ text, size: 17, color: MUTED, italics: true })],
    spacing: { before: 120, after: 60 },
    keepNext: true,
  });
}

/** PNG dimensions straight from the IHDR chunk, so images keep their aspect ratio. */
function pngSize(path) {
  const b = fs.readFileSync(path);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function figure(path, cap, frac = 1.0) {
  if (!fs.existsSync(path)) return [p("[missing figure: " + path + "]")];
  const { w, h: hh } = pngSize(path);
  const width = Math.round(USABLE_PX * frac);
  const height = Math.round((width * hh) / w);
  return [
    new Paragraph({
      children: [new ImageRun({ type: "png", data: fs.readFileSync(path),
                                transformation: { width, height } })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 40 },
    }),
    caption(cap),
  ];
}

function bullets(items) {
  return items.map((t) =>
    new Paragraph({
      children: Array.isArray(t) ? t.map(([x, o]) => new TextRun({ text: x, ...(o || {}) }))
                                 : [new TextRun({ text: String(t) })],
      numbering: { reference: "grail-bullets", level: 0 },
      spacing: { before: 0, after: 80, line: 276, lineRule: "auto" },
    }));
}

function numbered(items) {
  return items.map((t) =>
    new Paragraph({
      children: Array.isArray(t) ? t.map(([x, o]) => new TextRun({ text: x, ...(o || {}) }))
                                 : [new TextRun({ text: String(t) })],
      numbering: { reference: "grail-numbers", level: 0 },
      spacing: { before: 0, after: 80, line: 276, lineRule: "auto" },
    }));
}

function calloutBox(title, lines) {
  const rows = [[title]].concat(lines.map((l) => [l]));
  return new Table({
    columnWidths: [USABLE],
    width: { size: USABLE, type: WidthType.DXA },
    rows: rows.map((r, i) =>
      new TableRow({
        children: [new TableCell({
          width: { size: USABLE, type: WidthType.DXA },
          shading: { type: ShadingType.CLEAR, fill: i === 0 ? "FDF2E9" : "FFFBF7", color: "auto" },
          margins: { top: 90, bottom: 90, left: 140, right: 140 },
          children: [new Paragraph({
            children: [new TextRun({ text: r[0], bold: i === 0, size: 19, color: INK })],
            spacing: { before: 0, after: 0, line: 264, lineRule: "auto" },
          })],
        })],
      })),
    borders: {
      top: { style: BorderStyle.SINGLE, size: 6, color: "C0522D" },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: "C0522D" },
      left: { style: BorderStyle.SINGLE, size: 6, color: "C0522D" },
      right: { style: BorderStyle.SINGLE, size: 6, color: "C0522D" },
      insideHorizontal: { style: BorderStyle.NONE, size: 0, color: "auto" },
      insideVertical: { style: BorderStyle.NONE, size: 0, color: "auto" },
    },
  });
}

function spacer(after = 200) {
  return new Paragraph({ children: [], spacing: { after } });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function buildDoc({ title, subtitle, sections, docTitle }) {
  return new Document({
    creator: "GRAIL Collector project",
    title: docTitle || title,
    description: subtitle,
    numbering: {
      config: [
        { reference: "grail-bullets",
          levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
                     alignment: AlignmentType.LEFT,
                     style: { paragraph: { indent: { left: 460, hanging: 260 } } } }] },
        { reference: "grail-numbers",
          levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
                     alignment: AlignmentType.LEFT,
                     style: { paragraph: { indent: { left: 460, hanging: 260 } } } }] },
      ],
    },
    styles: {
      default: {
        document: { run: { font: "Calibri", size: 21, color: INK },
                    paragraph: { spacing: { line: 276, lineRule: "auto", after: 120 } } },
        heading1: { run: { font: "Calibri", size: 30, bold: true, color: "1B4F7A" },
                    paragraph: { spacing: { before: 360, after: 160 } } },
        heading2: { run: { font: "Calibri", size: 25, bold: true, color: "1F2124" },
                    paragraph: { spacing: { before: 280, after: 120 } } },
        heading3: { run: { font: "Calibri", size: 22, bold: true, color: "4A4D52" },
                    paragraph: { spacing: { before: 220, after: 100 } } },
      },
    },
    sections: sections.map((s, i) => ({
      properties: {
        page: { size: { width: PAGE_W, height: PAGE_H },
                margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } },
      },
      headers: i === 0 ? undefined : {
        default: new Header({ children: [new Paragraph({
          children: [new TextRun({ text: title, size: 16, color: MUTED })],
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 6 } },
        })] }),
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ",
                                              PageNumber.TOTAL_PAGES], size: 16, color: MUTED })],
        })] }),
      },
      children: s,
    })),
  });
}

async function write(doc, path) {
  const buf = await Packer.toBuffer(doc);
  fs.writeFileSync(path, buf);
  console.log("wrote " + path + "  (" + (buf.length / 1024).toFixed(0) + " KB)");
}

module.exports = {
  p, h, rich, mono, table, caption, tableCaption, figure, bullets, numbered,
  calloutBox, spacer, pageBreak, buildDoc, write, pngSize,
  Paragraph, TextRun, AlignmentType, HeadingLevel, TableOfContents, PageBreak,
  USABLE, USABLE_PX, INK, MUTED,
};
