/*
 * Build FinCrime Stage 2 PIDI Proposal in Word .docx format
 * Run: node scripts/build_proposal_docx.js
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType, VerticalAlign, PageNumber,
  PageBreak, TableOfContents, ExternalHyperlink, TabStopType,
  TabStopPosition, PageOrientation,
} = require("docx");

// ---------- Styling helpers ----------
const FONT = "Calibri";
const COLOR_PRIMARY = "0B2A47";   // dark navy
const COLOR_ACCENT = "C62828";    // PIDI red accent
const COLOR_MUTED = "5A6678";
const COLOR_BG_LIGHT = "F4F6FA";
const COLOR_BG_ACCENT = "FDECEA";
const COLOR_BORDER = "D0D5DB";

const border = (color = COLOR_BORDER) => ({
  style: BorderStyle.SINGLE, size: 1, color,
});
const cellBorders = (color = COLOR_BORDER) => ({
  top: border(color), bottom: border(color),
  left: border(color), right: border(color),
});
const cellMargins = { top: 100, bottom: 100, left: 140, right: 140 };

function p(text, opts = {}) {
  const { bold, italic, color, size, align, spacingBefore, spacingAfter, font } = opts;
  return new Paragraph({
    alignment: align,
    spacing: { before: spacingBefore, after: spacingAfter },
    children: [
      new TextRun({
        text: String(text || ""),
        bold, italics: italic, color, size, font: font || FONT,
      }),
    ],
  });
}

function pRich(runs, opts = {}) {
  return new Paragraph({
    alignment: opts.align,
    spacing: { before: opts.spacingBefore, after: opts.spacingAfter },
    children: runs,
  });
}

function bulletP(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}

function bulletPRich(runs) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 60, after: 60 },
    children: runs,
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 180 },
    children: [new TextRun({ text, bold: true, font: FONT, color: COLOR_PRIMARY, size: 32 })],
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 12, color: COLOR_ACCENT, space: 4 },
    },
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, bold: true, font: FONT, color: COLOR_PRIMARY, size: 26 })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, bold: true, font: FONT, color: COLOR_ACCENT, size: 22 })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 80, after: 80, line: 320 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, font: FONT, size: 22, ...opts })],
  });
}

function labelValueRow(label, value, opts = {}) {
  return new TableRow({
    children: [
      new TableCell({
        borders: cellBorders(),
        width: { size: 2880, type: WidthType.DXA },
        shading: { fill: opts.labelBg || COLOR_BG_LIGHT, type: ShadingType.CLEAR },
        margins: cellMargins,
        children: [p(label, { bold: true, size: 20, color: COLOR_PRIMARY })],
      }),
      new TableCell({
        borders: cellBorders(),
        width: { size: 6480, type: WidthType.DXA },
        margins: cellMargins,
        children: [p(value, { size: 20 })],
      }),
    ],
  });
}

function infoBox(text, color = COLOR_ACCENT) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({
      children: [new TableCell({
        borders: {
          top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
          bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
          right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
          left: { style: BorderStyle.SINGLE, size: 24, color },
        },
        width: { size: 9360, type: WidthType.DXA },
        shading: { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR },
        margins: { top: 160, bottom: 160, left: 240, right: 240 },
        children: text.split("\n").map(line =>
          p(line, { size: 22, italic: true, color: COLOR_MUTED }),
        ),
      })],
    })],
  });
}

// ---------- Content ----------
const SECTIONS = [];

// === COVER PAGE ===
SECTIONS.push(
  pRich([new TextRun({ text: "", size: 28 })], { spacingBefore: 1200 }),
  pRich([new TextRun({
    text: "PROPOSAL TAHAP 2",
    bold: true, font: FONT, color: COLOR_ACCENT, size: 32,
  })], { align: AlignmentType.CENTER, spacingAfter: 200 }),
  pRich([new TextRun({
    text: "Program Inovasi Digital Indonesia (PIDI)",
    font: FONT, color: COLOR_MUTED, size: 24,
  })], { align: AlignmentType.CENTER, spacingAfter: 1000 }),

  pRich([new TextRun({
    text: "FinCrime",
    bold: true, font: FONT, color: COLOR_PRIMARY, size: 72,
  })], { align: AlignmentType.CENTER, spacingAfter: 200 }),

  pRich([new TextRun({
    text: "End-to-End Financial Crime Intelligence System for Indonesia",
    italics: true, font: FONT, color: COLOR_PRIMARY, size: 28,
  })], { align: AlignmentType.CENTER, spacingAfter: 800 }),

  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 400, after: 400 },
    border: {
      top: { style: BorderStyle.SINGLE, size: 18, color: COLOR_ACCENT, space: 6 },
      bottom: { style: BorderStyle.SINGLE, size: 18, color: COLOR_ACCENT, space: 6 },
    },
    children: [new TextRun({
      text: "4-Layer AI · Real-time · POJK No.12/2024 · FATF Rec 22-25",
      bold: true, font: FONT, color: COLOR_PRIMARY, size: 22,
    })],
  }),

  pRich([new TextRun({ text: "", size: 20 })], { spacingBefore: 1000 }),
);

// Cover info table
SECTIONS.push(new Table({
  width: { size: 7200, type: WidthType.DXA },
  columnWidths: [2400, 4800],
  alignment: AlignmentType.CENTER,
  rows: [
    labelValueRow("Nama Tim", "FinCrime"),
    labelValueRow("ID Tim", "[ISI: kode tim PIDI]"),
    labelValueRow("Project Lead", "Andi Arif Abdillah"),
    labelValueRow("Institusi", "Universitas Gunadarma & Universitas Sultan Ageng Tirtayasa"),
    labelValueRow("Anggota", "4 orang lintas-institusi"),
    labelValueRow("Status", "Prototype (Functional MVP)"),
  ],
}));

SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === TABLE OF CONTENTS ===
SECTIONS.push(
  h1("Daftar Isi"),
  new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
);
SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === 1. IDENTITAS TIM ===
SECTIONS.push(h1("1. Identitas Tim & Proposal"));

SECTIONS.push(h2("1.1 Informasi Dasar"));
SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2880, 6480],
  rows: [
    labelValueRow("ID Tim", "[ISI: kode tim PIDI, contoh P0041]"),
    labelValueRow("Nama Tim", "FinCrime"),
    labelValueRow("Proposal Title", "FinCrime: End-to-End Financial Crime Intelligence System for Indonesia"),
  ],
}));

SECTIONS.push(h2("1.2 Komposisi Tim"));
SECTIONS.push(body(
  "Tim FinCrime merupakan kolaborasi lintas-institusi yang terdiri dari empat anggota dengan peran spesifik:",
));

// Team table
const teamRows = [
  ["Andi Arif Abdillah", "Universitas Gunadarma", "Project Lead, ML Engineer & Blockchain Analytics", "Layer 2 (GraphSAGE GNN Crypto Tracing) + Multi-chain crypto integration (BTC, ETH, BSC, Polygon, Tron)"],
  ["Raya Sesan Firdaus", "Universitas Gunadarma", "ML Engineer & Data Intelligence", "Layer 0 (XGBoost Risk Scoring + SHAP), OFAC/UN/DTTOT sanctions screening, negative news scraper"],
  ["Rambu Ilalang", "Universitas Gunadarma", "Backend AI & MLOps Engineer", "Layer 1 (Isolation Forest + Autoencoder), FastAPI, Docker/Kubernetes, Prometheus+Grafana, Airflow DAGs"],
  ["TB Muhammad Fikri Arsyad", "Universitas Sultan Ageng Tirtayasa", "Fullstack Developer", "Layer 3 (LTKM/LTKT regtech), dashboard web UI 13 tab termasuk Privacy Coin Monitor, mobile PWA, Telegram bot"],
];

const teamHeader = new TableRow({
  tableHeader: true,
  children: ["Nama", "Institusi", "Peran", "Tanggung Jawab"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [1900, 1900, 2300, 3260][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

const teamBody = teamRows.map(row => new TableRow({
  children: row.map((cell, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [1900, 1900, 2300, 3260][i], type: WidthType.DXA },
    margins: cellMargins,
    children: [p(cell, { size: 20 })],
  })),
}));

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [1900, 1900, 2300, 3260],
  rows: [teamHeader, ...teamBody],
}));

SECTIONS.push(h2("1.3 Executive Summary"));
SECTIONS.push(body(
  "FinCrime adalah sistem AI terintegrasi untuk mendeteksi dan mencegah kejahatan keuangan di Indonesia secara real-time. Sistem mengombinasikan empat layer: (1) Risk Scoring berbasis XGBoost+SHAP, (2) Fraud Detection real-time dengan Isolation Forest + Autoencoder, (3) Crypto Tracing menggunakan GraphSAGE GNN multi-chain (BTC/ETH/BSC/Polygon/Tron), dan (4) Auto-generated LTKM/LTKT dengan narasi LLM Claude.",
));
SECTIONS.push(body(
  "Sejak Tahap 1, tim telah membangun 40+ komponen end-to-end terverifikasi: web UI 13 tab termasuk Privacy Coin Monitor, mobile PWA, integrasi OFAC real-time (1.000+ entitas sanksi + 313 alamat crypto), modul deteksi privacy coin (Monero/Zcash/Dash) berbasis on/off-ramp monitoring sesuai standar industri, Prometheus+Grafana observability, dan MLflow model registry.",
));
SECTIONS.push(body(
  "Sistem menargetkan reduksi waktu pembuatan LTKM dari 1-3 hari menjadi 5 menit, sesuai POJK No.12/2024, UU PDP No.27/2022, dan FATF Recommendations 22-25. Arsitektur DLT-agnostic juga AML-ready untuk Project Garuda Rupiah Digital — siap men-trace transaksi wholesale dan retail saat launch.",
));

SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === 2. PROBLEM ALIGNMENT ===
SECTIONS.push(h1("2. Problem Alignment & Refinement"));

SECTIONS.push(h2("2.1 Problem Statement"));
SECTIONS.push(infoBox("Strengthening Financial Resilience and Innovation — Risk Management"));

SECTIONS.push(h2("2.2 Primary Sub-Problem Statement"));
SECTIONS.push(bulletP("Fraud Detection Systems (FDS)"));
SECTIONS.push(bulletP("AML/CFT and Transaction Tracing including crypto"));
SECTIONS.push(bulletP("Regtech & Suptech"));
SECTIONS.push(bulletP("Alternative Data Utilization / Credit Scoring"));

SECTIONS.push(h2("2.3 Problem Validation"));
SECTIONS.push(body(
  "Masalah inti yang FinCrime selesaikan adalah ketidakmampuan sistem pemantauan keuangan Indonesia saat ini untuk mendeteksi kejahatan keuangan—khususnya pencucian uang berbasis kripto dan keterlibatan sektor private (DNFBP)—secara real-time dan terintegrasi. Tiga akar masalah utama:",
));
SECTIONS.push(body(
  "Pertama, silo data antar-institusi membuat pelacakan dana lintas-instrumen (bank ↔ e-wallet ↔ crypto ↔ properti/aset mewah) hampir mustahil dilakukan holistik. Kedua, fraud detection konvensional bersifat reaktif dan berbasis rule statis, menghasilkan false positive tinggi sekaligus melewatkan pola layering kompleks. Ketiga, pelaporan AML/CFT (LTKM/LTKT) masih sangat manual; sektor DNFBP (notaris, dealer logam mulia, properti) bahkan banyak yang belum punya sistem otomatis sama sekali, padahal FATF Rec 22-25 mewajibkan.",
));
SECTIONS.push(body(
  "POJK No.12/2024 menuntut strategi anti-fraud proaktif, akurat, dan auditable. PPATK mencatat pencucian uang berbasis kripto mencapai Rp 800 miliar (CNBC, 2024), OJK mencatat kerugian investasi ilegal Rp 142 triliun (Infobank, 2024), dan FATF Mutual Evaluation Indonesia masih flag DNFBP supervision sebagai gap utama.",
));

SECTIONS.push(h2("2.4 Problem–Solution Mapping"));
SECTIONS.push(body("Pemetaan eksplisit problem → mekanisme solusi → outcome:"));

const psMapping = [
  ["Problem 1", "Silo data lintas-instrumen keuangan", "Arsitektur API-driven microservices dengan ingestion pipeline (Apache Kafka) yang menggabungkan transaksi bank, e-wallet, blockchain on-chain, dan transaksi DNFBP ke dalam stream terintegrasi.", "Visibilitas holistik aliran dana lintas-instrumen termasuk sektor privat."],
  ["Problem 2", "Fraud detection reaktif dengan FP tinggi", "Ensemble Layer 1 (Isolation Forest + PyTorch Autoencoder + rule engine) untuk deteksi anomali adaptif, dilanjutkan Layer 2 GraphSAGE GNN multi-chain.", "Deteksi proaktif dalam hitungan detik dengan target false positive rate < 2% pada production data."],
  ["Problem 3", "LTKM/LTKT manual dan DNFBP unsupervised", "Layer 3 template engine Jinja2 + narasi AI (Claude LLM) menghasilkan LTKM otomatis sesuai format PPATK GRIPS + modul DNFBP screening, UBO tracker, shell company detector.", "Waktu pelaporan turun dari 1-3 hari menjadi 5 menit; coverage AML mencakup sektor privat sesuai FATF."],
];

const psHeader = new TableRow({
  tableHeader: true,
  children: ["#", "Problem", "Solution Mechanism", "Outcome"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [800, 2400, 3680, 2480][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [800, 2400, 3680, 2480],
  rows: [psHeader, ...psMapping.map(row => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [800, 2400, 3680, 2480][i], type: WidthType.DXA },
      margins: cellMargins,
      children: [p(cell, { size: 19, bold: i === 0 })],
    })),
  }))],
}));

SECTIONS.push(h2("2.5 Ecosystem Alignment"));
SECTIONS.push(body(
  "FinCrime dirancang untuk terintegrasi dengan ekosistem regulasi keuangan Indonesia. Di level regulator, sistem disiapkan untuk terhubung dengan PPATK sebagai penerima LTKM/LTKT via GRIPS API, OJK untuk validasi kepatuhan POJK No.12/2024, dan Bappebti untuk pengawasan aset kripto sesuai POJK No.27/2024. Di level lembaga keuangan, FinCrime menyediakan REST API drop-in untuk core banking (107+ bank umum), e-wallet (GoPay, OVO, Dana), dan exchange kripto berlisensi PFAK — integrasi nyata menyusul melalui MoU dan pilot.",
));
SECTIONS.push(body(
  "Di level DNFBP (FATF Rec 22-23), sistem mendukung pelaporan dari notaris/PPAT, dealer logam mulia, agen properti, dan pejabat lelang. Di level penegakan hukum, output investigasi mendukung PPATK, KPK, dan Kejaksaan dalam pelacakan tindak pidana asal.",
));
SECTIONS.push(body(
  "Sistem patuh UU PDP No.27/2022 dengan data minimization, end-to-end encryption, dan immutable audit log. Pilot implementation direncanakan via OJK Regulatory Sandbox di tahun 2027.",
));

// ============================================================
// Section 2.6 — Strategic Alignment dengan Project Garuda CBDC
// ============================================================
SECTIONS.push(h2("2.6 Strategic Alignment dengan Project Garuda CBDC"));
SECTIONS.push(body(
  "FinCrime dirancang DLT-agnostic dan siap menjadi AML/CFT compliance layer untuk Project Garuda — inisiatif Central Bank Digital Currency (CBDC) Bank Indonesia. Hal ini bukan klaim spekulatif: Bank Indonesia secara eksplisit menyebut AML/CFT sebagai requirement integritas Rupiah Digital. (Catatan status: per Desember 2024, Garuda baru menyelesaikan PoC tahap pertama (wholesale) dan belum membuka akses integrasi publik — sehingga FinCrime memposisikan diri sebagai kandidat compliance layer untuk fase berikutnya, bukan integrasi yang sudah berjalan.)",
));

SECTIONS.push(infoBox(
  "Kutipan White Paper CBDC 2022 (hal. 16): \"...integritas keuangan terutama dalam konteks pemenuhan komitmen Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme.\"\n\n" +
  "Kutipan White Paper CBDC 2022 (hal. 19): \"Digitalisasi ekonomi keuangan juga disertai risiko... shadow banking, risiko siber dan fraud, pencucian uang dan pendanaan terorisme...\"",
  COLOR_PRIMARY,
));

SECTIONS.push(body(
  "FinCrime menjawab 3 dari 5 risiko utama CBDC yang BI khawatirkan: fraud, pencucian uang, dan pendanaan terorisme. Tabel di bawah memetakan 7 titik persinggungan antara desain Garuda dan kapabilitas FinCrime:",
));

const cbdcAlignmentRows = [
  ["DLT Permissioned (PoA)", "Tracing transaksi antar-validating-node", "Layer 2 GraphSAGE GNN + Neo4j (sudah implemented)"],
  ["w-Rupiah Digital (wholesale, PoC Dec 2024 selesai)", "Anti-fraud + monitoring volume tinggi antar-bank", "Layer 1 IsolationForest + Autoencoder + rule engine"],
  ["r-Rupiah Digital (retail, future end-state)", "LTKM/LTKT untuk transaksi retail publik", "Layer 3 auto-LTKM + DNFBP module"],
  ["Programmability (Smart Contract)", "Compliance rules embedded dalam kontrak", "Rule engine + WebSocket real-time alerts"],
  ["Identity service + Regulatory service", "KYC + sanctions screening built-in", "OFAC/UN/DTTOT integration + News screener"],
  ["Cross-border interoperability (3i)", "FATF Travel Rule + behavioral fingerprinting", "Multi-chain unified interface ready"],
  ["Privacy + integrity transactions", "Selective disclosure untuk regulator", "Audit log immutable + RBAC + Case Management"],
];

const cbdcHeader = new TableRow({
  tableHeader: true,
  children: ["Aspek CBDC Garuda", "Kebutuhan AML/Compliance", "Modul FinCrime yang Match"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [2800, 3280, 3280][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2800, 3280, 3280],
  rows: [cbdcHeader, ...cbdcAlignmentRows.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [2800, 3280, 3280][i], type: WidthType.DXA },
      shading: idx % 2 === 0
        ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
        : { fill: "FFFFFF", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [p(cell, { size: 19, bold: i === 0 })],
    })),
  }))],
}));

SECTIONS.push(h3("Strategic Differentiation"));
SECTIONS.push(body(
  "Belum ada kompetitor (Chainalysis, Elliptic, NICE Actimize) yang dirancang agar kompatibel dengan arsitektur CBDC permissioned DLT. FinCrime membangun sejak awal dengan asumsi: \"sistem yang sama yang men-trace Ethereum hari ini, harus bisa men-trace Rupiah Digital besok\". Layer 2 GraphSAGE bekerja pada struktur graph/DAG apapun — termasuk platform DLT permissioned seperti Hyperledger Besu atau R3 Corda, maupun blockchain transparent lain — sehingga adaptasinya bersifat teknis, bukan rebuild."
));
SECTIONS.push(body(
  "Roadmap integrasi: ketika BI buka access ke wholesale DLT API (target 2027), FinCrime adapter dapat dibangun dalam 3-4 minggu untuk consume DLT transaction events dan inject ke pipeline existing Layer 0/1/2/3 tanpa rebuild infrastruktur."
));
SECTIONS.push(infoBox(
  "Implikasi: FinCrime tidak hanya solve masalah AML hari ini, tapi juga future-proof untuk mendukung peningkatan rating FATF Mutual Evaluation Indonesia ketika Rupiah Digital launch — turning a compliance burden into a national competitive advantage.",
  COLOR_ACCENT,
));

SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === 3. SOLUTION & IMPACT ===
SECTIONS.push(h1("3. Solution & Impact Deep Dive"));

SECTIONS.push(h2("3.1 Solution Approach & Mechanism"));
SECTIONS.push(body(
  "FinCrime bekerja melalui pipeline real-time 4-layer terintegrasi.",
));
SECTIONS.push(h3("Tahap Input"));
SECTIONS.push(body(
  "Data dikumpulkan dari empat sumber: transaksi perbankan (REST/Open API), aktivitas e-wallet, blockchain multi-chain (Ethereum/Bitcoin/BSC/Polygon/Tron via Etherscan/Blockstream/TronGrid API), dan transaksi DNFBP (properti, logam mulia, UBO). Semua data dinormalisasi ke schema Pydantic kanonik dan di-stream via Apache Kafka.",
));

SECTIONS.push(h3("Tahap Processing — 4 Layer Sekuensial"));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Layer 0 Risk Scoring: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "XGBoost dengan SHAP explainability menghasilkan skor risiko 0-100 per entitas dalam <100ms, fitur termasuk velocity transaksi, PEP/sanction flag, dan integrasi OFAC SDN real-time.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Layer 1 Fraud Detection: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Ensemble Isolation Forest + PyTorch Autoencoder + rule engine mengevaluasi setiap transaksi terhadap distribusi historis, menghasilkan alert real-time untuk smurfing, volume spike, atau transfer ke yurisdiksi berisiko tinggi.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Layer 2 GNN Crypto Tracing: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Wallet terflag diteruskan ke graph database Neo4j. GraphSAGE message passing antar-node mendeteksi pola layering dan smurfing yang invisible bagi ML konvensional. Plus modul Beneficial Ownership (UBO) tracker dan Shell Company detector untuk sektor private.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Layer 3 Regtech: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Template engine Jinja2 + narasi LLM Claude menyusun LTKM/LTKT otomatis sesuai format PPATK, dengan auto-screening DTTOT/UN/news Indonesia (Kompas, Detik, Tempo, Antara, CNN ID).", font: FONT, size: 22 }),
]));

SECTIONS.push(h3("Tahap Output"));
SECTIONS.push(body(
  "(1) Real-time WebSocket alerts ke compliance officer, (2) visualisasi graph interaktif, (3) LTKM/LTKT siap submit ke PPATK GRIPS, (4) audit log immutable untuk regulator. Dilengkapi mobile PWA dan Telegram bot untuk officer mobile.",
));

SECTIONS.push(h2("3.2 Impact Scale & Targets"));
SECTIONS.push(body("FinCrime menargetkan dampak di lima lapisan ekosistem keuangan Indonesia:"));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Lembaga Keuangan: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Menurunkan kerugian fraud melalui deteksi proaktif. Indonesia memiliki 107 bank umum, ribuan fintech, dan 30.000+ DNFBP. Target pilot: minimal 3 lembaga keuangan + 2 sektor DNFBP dalam 12 bulan pertama.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Regulator (OJK, BI, PPATK, Bappebti): ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Memberikan visibilitas real-time atas aliran dana mencurigakan. PPATK menerima puluhan ribu laporan transaksi mencurigakan per tahun; FinCrime mempersingkat waktu generasi laporan dari 1-3 hari menjadi 5 menit.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Sektor DNFBP: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Menyediakan AML/CFT toolkit yang sebelumnya hanya tersedia bagi bank besar, sehingga sektor private bisa memenuhi FATF Rec 22-23 tanpa investasi IT besar.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Masyarakat dan UMKM: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Memperluas inklusi keuangan via credit scoring berbasis data alternatif. Lebih dari 50 juta UMKM Indonesia masih unbanked/underbanked.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Indonesia di Level Makro: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Memperkuat integritas sistem keuangan, menurunkan Rp 800 miliar pencucian uang kripto dan Rp 142 triliun investasi ilegal, memperbaiki rating FATF Mutual Evaluation.", font: FONT, size: 22 }),
]));

SECTIONS.push(h2("3.3 Impact Measurement (KPI)"));

// KPI Table
const kpiCategories = [
  { title: "KPI Teknis", color: "1E3A8A", items: [
    ["Fraud detection recall", "> 80% (IBM AML + Elliptic)"],
    ["Fraud precision", "> 70% (target FP rate < 2% pada production benchmark)"],
    ["Inference latency", "L0 <100ms, L1 <500ms, L2 <2s"],
    ["Composite F1-score", "> 75%"],
    ["Model drift PSI", "< 0.10 sliding 2 minggu"],
    ["System uptime", "> 99.5%"],
  ]},
  { title: "KPI Proses", color: "166534", items: [
    ["Waktu LTKM/LTKT", "1-3 hari → 5 menit"],
    ["Investigasi cross-instrument", "Minggu → jam"],
    ["LTKM per officer per hari", "10-20x naik"],
    ["Coverage DNFBP", "Property, HVA, UBO, Notaris"],
  ]},
  { title: "KPI Pasar", color: "9A3412", items: [
    ["Onboarded Y1", "3 LK + 2 DNFBP"],
    ["Transaksi/bulan Y1", "1 juta+"],
    ["NPS compliance officer", "> 7/10"],
    ["Mobile PWA adoption", "> 80%"],
  ]},
  { title: "KPI Outcome Sistemik", color: "7E22CE", items: [
    ["Reduksi fraud loss Y1", "30%+ di lembaga mitra"],
    ["Akurasi LTKM ke PPATK", "+50%"],
    ["Median deteksi crypto laundering", "Minggu → jam"],
    ["FATF MER DNFBP rating", "Improvement"],
  ]},
];

for (const cat of kpiCategories) {
  SECTIONS.push(new Paragraph({
    spacing: { before: 240, after: 100 },
    children: [new TextRun({
      text: cat.title, bold: true, font: FONT, color: cat.color, size: 22,
    })],
  }));

  SECTIONS.push(new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [4680, 4680],
    rows: cat.items.map((row, idx) => new TableRow({
      children: row.map((cell, i) => new TableCell({
        borders: cellBorders(),
        width: { size: 4680, type: WidthType.DXA },
        shading: idx % 2 === 0
          ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
          : { fill: "FFFFFF", type: ShadingType.CLEAR },
        margins: cellMargins,
        children: [p(cell, { size: 20, bold: i === 0 })],
      })),
    })),
  }));
}

SECTIONS.push(h2("3.4 System & Public Value Proposition"));
SECTIONS.push(body(
  "FinCrime memberikan nilai sistemik melampaui manfaat individu pengguna. Pertama, memperkuat integritas sistem keuangan Indonesia dengan deteksi fraud proaktif lintas-instrumen. Kedua, meningkatkan pengawasan ekosistem kripto multi-chain yang menjadi celah utama pencucian uang. Ketiga, meningkatkan transparansi kepatuhan via LTKM auditable, timestamped, dengan narasi LLM Bahasa Indonesia baku.",
));
SECTIONS.push(body(
  "Keempat, mendukung inklusi keuangan via alternative data credit scoring untuk UMKM tanpa riwayat kredit formal. Kelima, mendemokratisasi AML compliance untuk sektor private (DNFBP) yang sebelumnya tidak punya akses tools enterprise. Keenam, meningkatkan efisiensi regulator—dengan automasi LTKM, PPATK dan OJK dapat fokus pada investigasi prioritas tinggi. FinCrime diposisikan bukan sekadar produk SaaS, tetapi sebagai infrastruktur publik untuk integritas finansial Indonesia.",
));

SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === 4. ORIGINALITY & INNOVATION ===
SECTIONS.push(h1("4. Originality & Innovation"));

SECTIONS.push(h2("4.1 Solution Originality"));
SECTIONS.push(body(
  "FinCrime adalah platform AML/CFT pertama di Indonesia yang mengintegrasikan LIMA hal yang belum pernah disatukan dalam satu produk: (1) GraphSAGE GNN multi-chain untuk crypto tracing real (BTC/ETH/BSC/Polygon/Tron), (2) LLM-powered LTKM narrative dalam Bahasa Indonesia baku, (3) Privacy Coin Monitor — deteksi konversi ke/dari privacy coin (Monero, Zcash, Dash) melalui strategi on/off-ramp monitoring berstandar industri, dengan auto-flag karena privacy coin tidak masuk daftar PFAK Bappebti, dilengkapi modul screening sektor private/DNFBP, (4) auto-sync dengan list sanksi internasional (OFAC SDN 19.000+ entitas + UN Consolidated 1.000+ entitas + DTTOT) plus negative news screening 5 media Indonesia, dan (5) DLT-agnostic architecture yang siap menjadi AML compliance layer untuk Project Garuda Rupiah Digital Bank Indonesia.",
));
SECTIONS.push(body(
  "Pendekatan ini membedakan FinCrime dari produk komersial: Chainalysis (hanya crypto transparent, mahal USD 100k+/tahun, tidak Garuda-ready), Elliptic (sama), Actimize/SAS (hanya bank konvensional, tidak crypto/DNFBP/CBDC). Kami adalah satu-satunya yang menggabungkan kelima dimensi tersebut dengan fokus konteks Indonesia: Bahasa Indonesia baku, regulasi POJK/PMK, format PPATK GRIPS, ambang IDR, plus open architecture untuk adopsi institusi tier-2 dan DNFBP kecil dengan biaya rendah.",
));
SECTIONS.push(body(
  "Keunikan strategis ke-5 (CBDC-ready) khususnya relevan untuk Bank Indonesia: tidak ada produk AML komersial yang didesain native-compatible dengan permissioned DLT Indonesia. Saat BI launch w-Rupiah Digital (PoC selesai Desember 2024), FinCrime menjadi opsi natural untuk integration tanpa overhead biaya re-engineering dari produk asing.",
));

SECTIONS.push(h2("4.2 Technological / Method Innovation"));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "GraphSAGE GNN untuk crypto tracing — ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "menggantikan rule-based heuristic dengan message-passing neural network yang belajar representasi node, mendeteksi pola layering invisible bagi ML flat. Dilatih pada Elliptic Bitcoin dataset (200k node labeled).", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "LLM-powered LTKM narrative — ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "integrasi Claude API untuk auto-generate 'Ringkasan Kecurigaan' dalam Bahasa Indonesia formal sesuai standar PPATK, dengan fallback template offline.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Multi-chain unified interface — ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "single API mendukung 5 blockchain (BTC via Blockstream gratis, ETH via Etherscan, BSC/Polygon via Etherscan-clone, Tron via TronGrid) dengan auto-detect dari format address.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Hybrid ensemble Layer 1 — ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Isolation Forest + PyTorch Autoencoder + 6 deterministic rules untuk balance recall (ML) vs explainability (rules).", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "UBO graph traversal — ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "algoritma BFS upward pada NetworkX directed graph untuk trace ultimate beneficial owner sampai threshold 25% (FATF compliant), plus shell company scoring berdasarkan offshore jurisdiction (FATF FSI 2023).", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Real-time WebSocket alerts + drift detection PSI/KS — ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "untuk MLOps maturity. Semua model di-track via MLflow registry; pipeline scheduled via Apache Airflow.", font: FONT, size: 22 }),
]));

SECTIONS.push(h2("4.3 Creativity in Implementation"));
SECTIONS.push(body(
  "Distribusi mobile-first via Progressive Web App (PWA) — compliance officer install aplikasi dari browser tanpa app store, jalan offline-capable, dengan deep-link shortcut untuk Cases/Screening/Live Trace. Plus Telegram bot untuk on-the-go investigation dengan commands /trace, /risk, /screen.",
));
SECTIONS.push(body(
  "Engagement via multi-bahasa (ID/EN toggle), toast notification real-time WebSocket, Command Palette ⌘K untuk power user, dan Investigation Cases workflow yang terstruktur. Monetisasi tier-based: Free (DNFBP kecil), Professional Rp 25 juta/bulan (bank tier-3, fintech), Enterprise Rp 250 juta/bulan (bank tier-1/2), plus Regulator Subscription gratis untuk OJK/BI/PPATK sebagai subsidi infrastruktur publik.",
));

SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === 5. TECHNICAL ===
SECTIONS.push(h1("5. Technical Design"));

SECTIONS.push(h2("5.1 System Architecture"));
SECTIONS.push(body("Arsitektur FinCrime berbasis microservices API-driven dengan 7 lapisan logis:"));

const archLayers = [
  ["1", "Ingestion Layer", "Apache Kafka stream dari bank (REST/SFTP/Open API), e-wallet, blockchain (Etherscan/Blockstream/TronGrid), CSV importer (BCA/Mandiri/BRI/BNI)"],
  ["2", "Processing Layer", "4 model AI independen: Layer 0 XGBoost+SHAP (<100ms), Layer 1 IsoForest+Autoencoder+rules (<500ms), Layer 2 GraphSAGE+NetworkX+Neo4j (<2s), Layer 3 Jinja2+Claude LLM (<5min E2E)"],
  ["3", "Data Layer", "PostgreSQL (cases, audit), Neo4j (wallet graph), ClickHouse (analytics), Redis (cache), MinIO/S3 (model artifacts)"],
  ["4", "API Layer", "FastAPI 60+ endpoints, OpenAPI docs, async-ready stateless untuk horizontal scale"],
  ["5", "Presentation Layer", "Web UI 13 tab termasuk Privacy Coin Monitor (HTML+vanilla JS), Streamlit fallback, mobile PWA installable, Telegram bot"],
  ["6", "Observability Layer", "Prometheus (metrics), Grafana (7 panels), structlog, immutable audit log, MLflow (experiment + registry)"],
  ["7", "Orchestration Layer", "Apache Airflow 4 DAGs (OFAC daily, news 6h, retrain weekly, drift daily), Docker Compose, Kubernetes manifests HPA 3-20 pods"],
];

const archHeader = new TableRow({
  tableHeader: true,
  children: ["#", "Layer", "Komponen Teknis"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [800, 2200, 6360][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [800, 2200, 6360],
  rows: [archHeader, ...archLayers.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [800, 2200, 6360][i], type: WidthType.DXA },
      shading: idx % 2 === 0
        ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
        : { fill: "FFFFFF", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [p(cell, { size: 20, bold: i < 2 })],
    })),
  }))],
}));

SECTIONS.push(body(
  "Deployment-ready via GitHub Actions CI/CD ke staging k8s cluster, dengan security scanning + automated tests.",
));

SECTIONS.push(h2("5.2 Data & Feasibility"));
SECTIONS.push(h3("Data Publik (terintegrasi)"));
SECTIONS.push(bulletP("OFAC SDN List — 19.041 entitas sanksi + 313 alamat crypto (auto-refresh 24 jam)"));
SECTIONS.push(bulletP("UN Security Council Consolidated List — 1.004 entitas"));
SECTIONS.push(bulletP("FATF FSI 2023 — 32 offshore jurisdictions"));
SECTIONS.push(bulletP("Negative news — Kompas, Detik, Tempo, Antara, CNN ID (RSS scraping)"));
SECTIONS.push(bulletP("Etherscan API, Blockstream BTC, BscScan, PolygonScan, TronGrid"));
SECTIONS.push(bulletP("CoinGecko — live crypto-to-IDR conversion"));

SECTIONS.push(h3("Dataset Training (Kaggle, publik)"));
SECTIONS.push(bulletP("IBM AML Transactions — 180M transaksi labeled untuk Layer 1"));
SECTIONS.push(bulletP("Elliptic Bitcoin Dataset — 200k wallet labeled untuk Layer 2 (GraphSAGE benchmark)"));
SECTIONS.push(bulletP("BAF NeurIPS 2022 — 1M bank account fraud records untuk Layer 0"));
SECTIONS.push(bulletP("PaySim — mobile money simulator untuk smurfing patterns"));

SECTIONS.push(h3("Data Partner (target Y1 via MoU)"));
SECTIONS.push(bulletP("Core banking BCA/Mandiri/BRI/BNI Open API"));
SECTIONS.push(bulletP("PPATK SIPESAT DTTOT (terduga teroris)"));
SECTIONS.push(bulletP("OJK regulatory data feed"));
SECTIONS.push(bulletP("Bappebti registered exchange list"));

SECTIONS.push(body(
  "Feasibility tinggi: ~70% kebutuhan data sudah tersedia gratis publik. Validasi sample sintetis 7.500 entitas + 30k transaksi: Layer 0 ROC AUC = 0.79 (target 0.85+ di data real).",
));

SECTIONS.push(h2("5.3 Security & Compliance"));

SECTIONS.push(h3("Regulasi Indonesia"));
SECTIONS.push(bulletP("POJK No.12/2024 — proactive anti-fraud strategy"));
SECTIONS.push(bulletP("UU PDP No.27/2022 — data minimization, encryption in transit (TLS), at rest (KMS), data residency Indonesia"));
SECTIONS.push(bulletP("UU TPPU No.8/2010 + PP No.43/2015 — full DNFBP coverage"));
SECTIONS.push(bulletP("PMK No.55/2017 — notaris/PPAT reporting otomatis"));
SECTIONS.push(bulletP("PPATK GRIPS format — LTKM/LTKT compliant template"));

SECTIONS.push(h3("Standar Internasional"));
SECTIONS.push(bulletP("FATF Recommendations 10, 11, 20, 22-25, 32"));
SECTIONS.push(bulletP("OFAC Sanctions — real-time auto-refresh"));
SECTIONS.push(bulletP("UN Security Council Consolidated List"));

SECTIONS.push(h3("Security Measures"));
SECTIONS.push(bulletP("Immutable audit log (append-only) untuk setiap prediction, report, case change"));
SECTIONS.push(bulletP("RBAC ready untuk SSO (Azure AD/Okta via OAuth2)"));
SECTIONS.push(bulletP("Secrets via .env (production: HashiCorp Vault)"));
SECTIONS.push(bulletP("Model versioning via MLflow — full reproducibility audit"));
SECTIONS.push(bulletP("Prometheus monitoring + Grafana alerting"));
SECTIONS.push(bulletP("GitHub Actions security scanning"));
SECTIONS.push(bulletP("Docker hardening + non-root user, K8s SealedSecrets, mTLS antar-microservices"));
SECTIONS.push(body(
  "Penetration testing dan ISO 27001 certification direncanakan sebelum production deployment (Y1 Q4 2026).",
));

SECTIONS.push(h2("5.4 Implementation Readiness (MVP)"));
SECTIONS.push(body(
  "MVP FinCrime SUDAH SELESAI DIBANGUN END-TO-END dan terverifikasi berfungsi:",
));

const mvpItems = [
  "4 Layer AI Models — terlatih, terdeploy, dapat di-query via API",
  "60+ REST API endpoints — OpenAPI docs lengkap (/docs)",
  "Web UI 13 tab — Overview, Risk Scoring, Fraud, Tracing, Reports, Live Trace, Cases, Screening, Private Sector AML, Multi-chain, Monitoring, Timeline, Privacy Coin Monitor",
  "Mobile PWA — installable di HP, offline-capable",
  "Telegram bot — 7 commands untuk officer mobile (termasuk /privacycoin)",
  "Real OFAC/UN/DTTOT integration — 1.000+ entitas terload",
  "Multi-chain crypto — BTC (free), ETH/BSC/Polygon/Tron (free API key)",
  "Privacy Coin Monitor — deteksi on/off-ramp Monero/Zcash/Dash, matriks 3-tier, auto-flag non-PFAK Bappebti (tab UI + API + Telegram)",
  "DNFBP screening — Property, HVA, UBO, Shell Company detector (modul sektor private)",
  "LLM-powered LTKM narrative (Claude API)",
  "Prometheus + Grafana observability — 7 dashboard panels",
  "MLflow model registry + Apache Airflow 4 DAGs",
  "GitHub Actions CI/CD",
  "Docker Compose full stack + Kubernetes manifests",
  "Immutable audit log",
  "14/14 pytest passing",
];
for (const item of mvpItems) {
  SECTIONS.push(bulletPRich([
    new TextRun({ text: "✓ ", bold: true, color: "166534", font: FONT, size: 22 }),
    new TextRun({ text: item, font: FONT, size: 22 }),
  ]));
}
SECTIONS.push(body(
  "Target 3 bulan ke depan: pilot dengan 1 bank mitra di OJK Regulatory Sandbox, integrasi PPATK SIPESAT (perlu MoU), retrain di data real (IBM AML + Elliptic) untuk meningkatkan ROC AUC ke 0.85+.",
));

// ============================================================
// SECTION 5.5 — Privacy Coin Strategy & AML Coverage Matrix
// ============================================================
SECTIONS.push(h2("5.5 Privacy Coin Strategy & AML Coverage Matrix"));
SECTIONS.push(body(
  "Salah satu pertanyaan kritis untuk solusi AML berbasis blockchain adalah: bagaimana sistem menangani privacy coins seperti Monero dan Zcash yang dirancang secara kriptografis untuk tidak dapat di-trace? FinCrime mengadopsi pendekatan transparan, jujur, dan sejalan dengan standar industri (Chainalysis, Elliptic, TRM Labs) serta regulasi Indonesia (Bappebti).",
));

SECTIONS.push(h3("5.5.1 Privacy Coin — Prioritas Utama AML Crypto"));
SECTIONS.push(body(
  "Privacy coin adalah tantangan AML crypto paling serius karena dirancang untuk menyembunyikan jejak transaksi secara kriptografis. FinCrime menjadikan pemantauan privacy coin sebagai modul unggulan: tab Privacy Coin Monitor di dashboard, endpoint /v1/privacy-coin/* di API, dan command /privacycoin di Telegram bot. Agar tidak rancu, perlu dibedakan dua istilah yang sering tertukar dalam diskusi AML:",
));

const termClarification = [
  ["\"Privacy Coin\" (fokus bagian ini)", "Cryptocurrency yang dirancang menyembunyikan pengirim, penerima, dan jumlah transaksi secara kriptografis", "Monero (XMR), Zcash (ZEC), Dash, Beam, Grin, Pirate Chain"],
  ["\"Sektor Private\" / DNFBP", "Lembaga pelapor non-bank menurut FATF Rec 22-23 — ditangani modul terpisah", "Notaris, dealer logam mulia, agen properti, dealer mobil mewah, KAP, lawyer"],
];

const termHeader = new TableRow({
  tableHeader: true,
  children: ["Istilah", "Pengertian", "Contoh"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [2400, 3680, 3280][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2400, 3680, 3280],
  rows: [termHeader, ...termClarification.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [2400, 3680, 3280][i], type: WidthType.DXA },
      shading: idx % 2 === 0
        ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
        : { fill: "FFFFFF", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [p(cell, { size: 20, bold: i === 0 })],
    })),
  }))],
}));

SECTIONS.push(body(
  "FinCrime menangani KEDUA scope tersebut melalui modul terpisah: Privacy Coin Monitor (dibahas detail di bagian ini) untuk aset kripto anonim, dan modul Sektor Private/DNFBP untuk lembaga pelapor non-bank. Sisa Bagian 5.5 berfokus pada strategi privacy coin.",
));

SECTIONS.push(h3("5.5.2 Tiga Tingkat Traceability Crypto"));
SECTIONS.push(body(
  "Crypto AML tracing memiliki tingkat kesulitan berbeda tergantung jenis aset. FinCrime mengadopsi pendekatan terstratifikasi:",
));

const tierRows = [
  ["TIER 1\nTransparent", "Bitcoin, Ethereum, BSC, Polygon, Tron, Solana", "Setiap transaksi PUBLIK di blockchain", "✅ FULL TRACE via Etherscan/Blockstream/BscScan/PolygonScan/TronGrid. GraphSAGE GNN trace alamat & layering chains", "BTC, ETH, BSC, Polygon, Tron (5 chains)"],
  ["TIER 2\nObfuscated", "Tornado Cash, CoinJoin, Wasabi, ChipMixer, cross-chain bridges", "Tx internal tersembunyi tapi alamat entry/exit visible", "⚠️ FLAG WALLET yang interact dengan mixer/bridge sanctioned. Tidak trace internal mixer.", "Tornado Cash addresses (OFAC), Lazarus Group, Hydra Market"],
  ["TIER 3\nPrivate (Privacy Coins)", "Monero (XMR), Zcash z-address, Dash PrivateSend, Beam, Grin", "Pengirim, penerima, dan jumlah SEMUA tersembunyi by design (ring signatures, zk-SNARKs)", "❌ TIDAK BISA trace internal (cryptographic limitation). ✅ MONITOR on/off-ramps (exchange yang trade privacy coins).", "Behavioral flagging exchange yang dukung Monero pair"],
];

const tierHeader = new TableRow({
  tableHeader: true,
  children: ["Tier", "Contoh Aset", "Karakteristik", "Kemampuan FinCrime", "Implementasi"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [1500, 1700, 2200, 2300, 1660][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 18 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [1500, 1700, 2200, 2300, 1660],
  rows: [tierHeader, ...tierRows.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [1500, 1700, 2200, 2300, 1660][i], type: WidthType.DXA },
      shading: idx === 0
        ? { fill: "DCFCE7", type: ShadingType.CLEAR }
        : idx === 1
        ? { fill: "FEF3C7", type: ShadingType.CLEAR }
        : { fill: "FEE2E2", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: cell.split("\n").map(line => p(line, {
        size: 18, bold: i === 0,
      })),
    })),
  }))],
}));

SECTIONS.push(h3("5.5.3 On/Off-Ramp Monitoring Strategy (Industry Standard)"));
SECTIONS.push(body(
  "Untuk Tier 3 (privacy coins), bahkan tools komersial top-tier seperti Chainalysis Reactor, Elliptic, dan TRM Labs TIDAK dapat trace internal Monero atau Zcash karena keterbatasan kriptografis fundamental. Strategi yang dipakai industri (dan diadopsi FinCrime) adalah \"Trace what's traceable, flag the gateway\":",
));

SECTIONS.push(bulletPRich([
  new TextRun({ text: "Strategi 1 — Exchange Flagging: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Wallet di transparent chain (BTC/ETH) yang kirim dana ke exchange yang mendukung Monero/Zcash pair (Kraken, KuCoin) otomatis di-tag \"potential privacy coin routing\".", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Strategi 2 — Off-ramp Surveillance: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Ketika dana keluar privacy coin balik ke USDT/USDC/fiat lewat exchange regulated, sistem trace destination address karena exchange wajib KYC (Travel Rule FATF Rec 16).", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Strategi 3 — Behavioral Fingerprinting: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Walaupun internal Monero hidden, perilaku user (timing pattern, jumlah, source-of-funds) bisa di-fingerprint dengan ML untuk identifikasi pelaku.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Strategi 4 — Network-level Surveillance: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Riset akademis (CMU, ETH Zürich) menunjukkan beberapa tx Monero bisa di-deanonymize via analisis P2P network layer + IP correlation. Bukan default FinCrime, tapi roadmap kolaborasi riset.", font: FONT, size: 22 }),
]));

SECTIONS.push(h3("5.5.4 Alignment dengan Regulasi Indonesia & Internasional"));
SECTIONS.push(body(
  "Pendekatan FinCrime terhadap privacy coins sejalan dengan trend regulasi global yang membatasi privacy coins di ekosistem regulated:",
));

const regAlignmentRows = [
  ["🇮🇩 Bappebti Indonesia", "Daftar PFAK (Penyelenggara Fisik Aset Kripto) approved TIDAK include Monero, Zcash, Dash. Hanya 501 aset kripto yang di-approve, semua transparent chains.", "✅ FinCrime sudah align — fokus ke 5 chain transparent"],
  ["🌍 FATF Rec 16 (Travel Rule)", "VASP wajib share informasi pengirim/penerima untuk tx >USD 1.000. Privacy coins by design tidak comply → delisted.", "✅ FinCrime integrate sanctions list & exchange flagging"],
  ["🇪🇺 EU MiCA (eff. 2024)", "Privacy coins dilarang masuk regulated exchange di EU. Binance UK, Kraken UK delisted Monero.", "✅ FinCrime tidak prioritize Monero/Zcash internal trace"],
  ["🇺🇸 OFAC (US Treasury)", "Sanksi Tornado Cash 2022 — mixer/obfuscation tools jadi target hukum. Developer ditangkap.", "✅ Auto-refresh OFAC list (19k entitas, 313 alamat crypto)"],
  ["🏛 PPATK Indonesia", "STR (Suspicious Transaction Report) wajib untuk semua tx mencurigakan, termasuk crypto transparent.", "✅ Auto-LTKM termasuk crypto risk indicators"],
];

const regHeader = new TableRow({
  tableHeader: true,
  children: ["Regulator", "Posisi terhadap Privacy Coins", "FinCrime Compliance"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [2000, 4360, 3000][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2000, 4360, 3000],
  rows: [regHeader, ...regAlignmentRows.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [2000, 4360, 3000][i], type: WidthType.DXA },
      shading: idx % 2 === 0
        ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
        : { fill: "FFFFFF", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [p(cell, { size: 19, bold: i === 0 })],
    })),
  }))],
}));

SECTIONS.push(h3("5.5.5 Honest Limitations Statement"));
SECTIONS.push(infoBox(
  "FinCrime TIDAK mengklaim bisa trace internal Monero atau Zcash. Tidak ada produk komersial manapun (Chainalysis, Elliptic, TRM Labs) yang bisa karena keterbatasan kriptografis. Yang FinCrime lakukan adalah pendekatan industri-standar: trace transparent chains secara lengkap (5 chains), flag wallet yang interact dengan mixer (OFAC), dan monitor on/off-ramp ke exchange yang mendukung privacy coins. Pendekatan ini SUDAH MAKSIMAL secara teknis dan compliant dengan posisi Bappebti yang tidak include Monero/Zcash di PFAK list.",
  COLOR_ACCENT,
));

SECTIONS.push(h3("5.5.6 Tipikal Skenario Pencucian Uang Crypto (yang Tertangkap Sistem)"));
SECTIONS.push(body(
  "Contoh end-to-end skenario pencucian uang hasil korupsi Rp 5 miliar dan bagaimana setiap layer FinCrime menangkapnya:",
));

const launderingFlow = [
  ["1", "Dana hasil korupsi masuk ke rekening bank nominee", "Layer 1 detect volume_spike + new_account flag"],
  ["2", "Transfer ke 5 rekening @ Rp 1 miliar (structuring)", "Layer 1 rule engine: smurfing_pattern_detected"],
  ["3", "Beli BTC di exchange (KYC bypass via mule)", "Layer 0 risk score naik (has_crypto_activity=true)"],
  ["4", "BTC transfer ke 10 wallet pribadi (layering)", "Layer 2 GraphSAGE: detect layering chain depth 4+"],
  ["5", "Sebagian ke Tornado Cash (obfuscation)", "Layer 2 + OFAC: flag interaction dengan sanctioned wallet"],
  ["6", "Sisanya convert USDT → beli properti via SPV", "Private Sector AML: notaris flag cash payment >Rp 1M"],
  ["7", "LTKM otomatis disiapkan + dikirim PPATK", "Layer 3 + LLM: narasi Bahasa Indonesia <5 menit"],
];

const flowHeader = new TableRow({
  tableHeader: true,
  children: ["Step", "Aksi Pelaku", "Layer yang Menangkap"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [800, 4280, 4280][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [800, 4280, 4280],
  rows: [flowHeader, ...launderingFlow.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [800, 4280, 4280][i], type: WidthType.DXA },
      shading: idx % 2 === 0
        ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
        : { fill: "FFFFFF", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [p(cell, { size: 19, bold: i === 0 })],
    })),
  }))],
}));

SECTIONS.push(body(
  "Jika pelaku mencoba menggunakan Monero/Zcash, sistem akan menangkap di on/off-ramp (saat convert dari/ke fiat atau transparent crypto), serta otomatis menaikkan risk score karena privacy coins TIDAK termasuk PFAK Bappebti approved list — sehingga membeli/menjual Monero di exchange Indonesia sudah jadi indikator suspicious by itself.",
));

SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === 6. BUSINESS MODEL ===
SECTIONS.push(h1("6. Business Model & Sustainability"));

SECTIONS.push(h2("6.1 Value Proposition"));
SECTIONS.push(h3("Untuk Compliance Officer (End User)"));
SECTIONS.push(bulletP("LTKM otomatis dalam 5 menit (dari 1-3 hari) dengan narasi LLM Bahasa Indonesia"));
SECTIONS.push(bulletP("Mobile-first via PWA dan Telegram — investigasi dari mana saja"));
SECTIONS.push(bulletP("Real-time WebSocket alerts — tidak perlu refresh"));
SECTIONS.push(bulletP("Case Management workflow yang terstruktur"));

SECTIONS.push(h3("Untuk Bank/Fintech (Institusi Pelapor)"));
SECTIONS.push(bulletP("Drop-in REST API — integrasi 2-4 minggu (vs Actimize 6-12 bulan)"));
SECTIONS.push(bulletP("Reduksi fraud loss hingga 30% via deteksi proaktif"));
SECTIONS.push(bulletP("Compliance otomatis POJK No.12/2024 — auditable, timestamped"));
SECTIONS.push(bulletP("Cost saving — gantikan kebutuhan tim analyst manual"));

SECTIONS.push(h3("Untuk DNFBP (Notaris, Dealer, Properti)"));
SECTIONS.push(bulletP("AML toolkit enterprise-grade dengan biaya terjangkau"));
SECTIONS.push(bulletP("Pemenuhan FATF Rec 22-23 tanpa investasi IT besar"));
SECTIONS.push(bulletP("Templates LTKM khusus DNFBP sesuai PMK No.55/2017"));

SECTIONS.push(h3("Untuk Regulator (OJK, BI, PPATK, Bappebti)"));
SECTIONS.push(bulletP("Read-only dashboard real-time atas seluruh lembaga mitra"));
SECTIONS.push(bulletP("Format PPATK GRIPS-compliant"));
SECTIONS.push(bulletP("Cross-instrument visibility (bank ↔ e-wallet ↔ crypto ↔ DNFBP)"));

SECTIONS.push(h2("6.2 Revenue Model / Funding"));

const revenueRows = [
  ["Free Tier", "DNFBP kecil, max 1.000 tx/bulan", "Rp 0 (acquisition)"],
  ["Professional", "Bank tier-3, fintech, koperasi (max 100k tx)", "Rp 25 juta/bulan"],
  ["Enterprise", "Bank tier-1/tier-2, exchange besar (unlimited + SLA 99.9%)", "Rp 250 juta/bulan"],
  ["Per-Transaction API", "L0: Rp 50/call · L1: Rp 100/call · L2: Rp 500/call", "Volume-based"],
  ["Regulator Subscription", "OJK, BI, PPATK, Bappebti", "Gratis (subsidi publik)"],
  ["Consulting", "Custom integration ke core banking", "Rp 500jt - 2M one-time"],
];

const revHeader = new TableRow({
  tableHeader: true,
  children: ["Tier", "Target & Scope", "Harga"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [2400, 4960, 2000][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2400, 4960, 2000],
  rows: [revHeader, ...revenueRows.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [2400, 4960, 2000][i], type: WidthType.DXA },
      shading: idx % 2 === 0
        ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
        : { fill: "FFFFFF", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [p(cell, { size: 20, bold: i === 0 })],
    })),
  }))],
}));

SECTIONS.push(h3("Funding Sources"));
SECTIONS.push(bulletP("Bank Indonesia PIDI grant (current submission)"));
SECTIONS.push(bulletP("OJK Regulatory Sandbox grant"));
SECTIONS.push(bulletP("LPDP research grant untuk academic partnership"));
SECTIONS.push(bulletP("Strategic investor (bank atau fintech holding company)"));
SECTIONS.push(bulletP("World Bank / ADB Financial Inclusion grant"));

SECTIONS.push(h3("Target Revenue"));
SECTIONS.push(bulletP("Tahun 1: Rp 2-3 miliar (3 Enterprise + 10 Professional)"));
SECTIONS.push(bulletP("Tahun 2: Rp 8-12 miliar"));
SECTIONS.push(bulletP("Tahun 3: Rp 25-40 miliar"));

SECTIONS.push(h2("6.3 Cost Structure & Sustainability"));
SECTIONS.push(h3("Biaya Operasional Tahunan (Y1)"));

const costRows = [
  ["Cloud infrastructure (AWS/GCP/Indonesian cloud)", "Rp 150 juta/tahun"],
  ["AI inference compute (model serving)", "Rp 50 juta/tahun"],
  ["LLM API (Claude untuk LTKM narrative, ~50k LTKM)", "Rp 30 juta/tahun"],
  ["Third-party API (Etherscan, BscScan, dll)", "Rp 20 juta/tahun"],
  ["Security & monitoring tools", "Rp 25 juta/tahun"],
  ["Domain, SSL, misc", "Rp 5 juta/tahun"],
  ["TOTAL Operational", "~Rp 280 juta/tahun"],
];

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [6360, 3000],
  rows: costRows.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [6360, 3000][i], type: WidthType.DXA },
      shading: idx === costRows.length - 1
        ? { fill: COLOR_BG_ACCENT, type: ShadingType.CLEAR }
        : (idx % 2 === 0
            ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
            : { fill: "FFFFFF", type: ShadingType.CLEAR }),
      margins: cellMargins,
      children: [p(cell, {
        size: 20,
        bold: idx === costRows.length - 1,
        color: idx === costRows.length - 1 ? COLOR_ACCENT : undefined,
      })],
    })),
  })),
}));

SECTIONS.push(h3("Sustainability Strategy"));
SECTIONS.push(bulletP("Break-even di Tahun 2 dengan 8 institusi mitra Enterprise tier"));
SECTIONS.push(bulletP("Revenue diversification (SaaS + per-tx + consulting + grant)"));
SECTIONS.push(bulletP("Open-source non-core untuk komunitas (drive adoption)"));
SECTIONS.push(bulletP("Strategic partnership untuk distribution leverage (Perbanas, INI, AFTECH)"));
SECTIONS.push(bulletP("Reinvest 30% revenue ke R&D"));

SECTIONS.push(h2("6.4 Scalability"));
SECTIONS.push(body(
  "Skalabilitas teknis: stateless FastAPI + Kubernetes HPA (3-20 pods) untuk horizontal scale linear, Kafka partition-based throughput (1k → 100k+ tx/s), Neo4j Enterprise (100M nodes), ClickHouse analytics, Redis cache, TorchServe inference server."
));

SECTIONS.push(h3("Kapasitas Saat Ini → Setelah Migration"));

const scaleRows = [
  ["Layer 0 risk scoring", "1.000 req/s", "10.000+ req/s"],
  ["Layer 1 fraud detection", "500 req/s", "5.000+ req/s"],
  ["Layer 2 GNN trace", "50 trace/s", "500+ trace/s"],
  ["Total entitas", "Single node", "100M+ entities"],
];

const scaleHeader = new TableRow({
  tableHeader: true,
  children: ["Komponen", "Single-node (dev)", "Migrated (Postgres + 3 pods + Redis)"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [3120, 3120, 3120][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [3120, 3120, 3120],
  rows: [scaleHeader, ...scaleRows.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [3120, 3120, 3120][i], type: WidthType.DXA },
      shading: idx % 2 === 0
        ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
        : { fill: "FFFFFF", type: ShadingType.CLEAR },
      margins: cellMargins,
      children: [p(cell, { size: 20, bold: i === 0 })],
    })),
  }))],
}));

SECTIONS.push(h3("Skalabilitas Geografis"));
SECTIONS.push(bulletP("Y1: pilot 3 bank Indonesia + 2 DNFBP"));
SECTIONS.push(bulletP("Y2: nationwide 30+ bank, 100+ DNFBP, 500+ fintech"));
SECTIONS.push(bulletP("Y3: ASEAN expansion (Malaysia, Singapura, Filipina)"));
SECTIONS.push(bulletP("Y5: emerging markets Asia-Africa"));
SECTIONS.push(body(
  "Framework FATF yang sama memudahkan ekspansi lintas-negara dengan minor localization."
));

SECTIONS.push(h2("6.5 Partnership & Distribution"));
SECTIONS.push(body(
  "Strategi distribusi multi-channel dengan partnership strategis di empat level:"
));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Regulator: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Bank Indonesia (PIDI grant), OJK (Regulatory Sandbox 2027), PPATK (MoU SIPESAT untuk GRIPS API), Bappebti (exchange kripto PFAK).", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Institusi Keuangan: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Tier-1 banks via OJK Sandbox, tier-2/3 via Perbanas, fintech via AFTECH, e-wallet (GoPay/OVO/Dana) post-pilot, exchange kripto via Aspakrindo.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Sektor DNFBP: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Ikatan Notaris Indonesia (30k+ notaris), APPI properti, Asosiasi Logam Mulia, Pejabat Lelang Kemkeu.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Akademis + Internasional: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "Gunadarma + Universitas Sultan Ageng Tirtayasa, BI Institute, ITB/UI/UGM. Chainalysis/Elliptic data sharing, World Bank Financial Inclusion.", font: FONT, size: 22 }),
]));
SECTIONS.push(body(
  "Channel: direct sales (Enterprise), self-service signup (Free/Pro), partner reseller komisi (DNFBP), OJK Sandbox entry point, open-source non-core."
));

SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === 7. MARKET FIT ===
SECTIONS.push(h1("7. Market Fit & Adoption"));

SECTIONS.push(h2("7.1 Problem–Market Fit"));
SECTIONS.push(body(
  "Masalah AML/CFT urgent karena tiga konsekuensi konkret jika tidak diselesaikan:"
));
SECTIONS.push(body(
  "(1) Lembaga keuangan: POJK No.12/2024 wajibkan anti-fraud proaktif sebelum 2025 — non-compliance berarti denda + pencabutan izin. Compliance officer burnout dari kerja manual repetitif (LTKM 1-3 hari/lapor)."
));
SECTIONS.push(body(
  "(2) DNFBP: FATF Mutual Evaluation 2023 flag DNFBP sebagai gap utama Indonesia. 90% notaris dan dealer logam mulia belum punya sistem pelaporan otomatis padahal PP 43/2015 mewajibkan."
));
SECTIONS.push(body(
  "(3) Regulator dan masyarakat: PPATK delay process 75 ribu LTKM/tahun. Crypto money laundering Rp 800 miliar (CNBC 2024), illegal investment Rp 142 triliun (Infobank 2024) terus meningkat. UMKM tidak akses kredit formal — alternative data scoring critical."
));
SECTIONS.push(body(
  "Intensitas masalah: HIGH — frequent (harian), costly (triliunan), regulated (mandatory)."
));

SECTIONS.push(h2("7.2 Evidence of Demand"));
SECTIONS.push(body(
  "Regulatory Demand (mandatory): POJK No.12/2024 (anti-fraud wajib sebelum 2025), PP 43/2015 + PMK 55/2017 (DNFBP wajib lapor), FATF MER 2023 (2 tahun perbaiki DNFBP), POJK 27/2024 (crypto oversight Bappebti→OJK)."
));
SECTIONS.push(body(
  "Market Demand: 36.500 institusi wajib lapor (107 bank umum + 1.700 BPR + 350 fintech + 30.000 DNFBP). PPATK terima 75 ribu LTKM dan 2 juta LTKT per tahun. Crypto exchange volume Indonesia Rp 859 triliun (2024, Bappebti)."
));
SECTIONS.push(body(
  "Pain Point Interviews: diskusi dengan 5 compliance officer bank menengah konfirmasi rata-rata 2-3 hari per LTKM dan frustrasi tools lama. Notaris Jakarta Selatan masih manual via Excel. Fintech P2P butuh real-time fraud detection tapi NICE Actimize > USD 500k implementation."
));

SECTIONS.push(h3("Competitor Landscape — Gap Confirmed"));

const compRows = [
  ["Chainalysis", "Hanya crypto, mahal (USD 100k+/tahun)", "Tidak cover bank/DNFBP"],
  ["Actimize/SAS", "Hanya bank, mahal", "Tidak crypto, tidak DNFBP"],
  ["FinCrime", "End-to-end 4 layer + DNFBP + multi-chain + Bahasa Indonesia", "AFFORDABLE untuk tier-2/tier-3"],
];

const compHeader = new TableRow({
  tableHeader: true,
  children: ["Produk", "Strength", "Gap (vs FinCrime)"].map((h, i) => new TableCell({
    borders: cellBorders(),
    width: { size: [2400, 3680, 3280][i], type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [p(h, { bold: true, color: "FFFFFF", size: 20 })],
  })),
});

SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2400, 3680, 3280],
  rows: [compHeader, ...compRows.map((row, idx) => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders(),
      width: { size: [2400, 3680, 3280][i], type: WidthType.DXA },
      shading: idx === compRows.length - 1
        ? { fill: COLOR_BG_ACCENT, type: ShadingType.CLEAR }
        : (idx % 2 === 0
            ? { fill: COLOR_BG_LIGHT, type: ShadingType.CLEAR }
            : { fill: "FFFFFF", type: ShadingType.CLEAR }),
      margins: cellMargins,
      children: [p(cell, {
        size: 20,
        bold: i === 0 || idx === compRows.length - 1,
        color: idx === compRows.length - 1 ? COLOR_ACCENT : undefined,
      })],
    })),
  }))],
}));

SECTIONS.push(h2("7.3 Target Market"));
SECTIONS.push(body(
  "Primary Market Y1 (~2.200 institusi keuangan formal): 107 bank umum, 1.700 BPR, 350 fintech terdaftar OJK, 12 exchange kripto PFAK Bappebti."
));
SECTIONS.push(body(
  "Secondary Market Y2 (~85.000 DNFBP): 30.000 notaris/PPAT (INI), 5.000 dealer logam mulia, 50.000 agen properti, 1.000 KAP, 500 pejabat lelang."
));
SECTIONS.push(body(
  "Tertiary Market Y3+: Regulator (OJK, BI, PPATK, Bappebti, KPK, Kejagung), 50+ law firm AML practice, Big-4 + mid-tier audit."
));
SECTIONS.push(body(
  "GTM priority: Y1 = 3-5 bank tier-2 via OJK Sandbox; Y2 = nationwide tier-2/3 + 100 DNFBP early adopter; Y3 = tier-1 banks + ASEAN expansion."
));

SECTIONS.push(h3("User Personas"));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Bu Sari (35) ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "— Compliance Officer Bank Tier-2 Surabaya, handle 200+ LTKM/bulan manual.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Pak Budi (50) ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "— Notaris Jakarta Selatan, takut sanksi PPATK tapi tidak ada budget Actimize.", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Pak Wahyu (45) ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "— Pengawas Madya OJK, butuh dashboard read-only monitor 12 lembaga.", font: FONT, size: 22 }),
]));

SECTIONS.push(h2("7.4 Adoption Readiness"));
SECTIONS.push(h3("Integrasi Teknis"));
SECTIONS.push(bulletP("REST API drop-in: 2-4 minggu integrasi core banking (vs Actimize 6-12 bulan)"));
SECTIONS.push(bulletP("Self-service signup web < 10 menit (Free/Professional tier)"));
SECTIONS.push(bulletP("Multi-channel input: REST API / Kafka / CSV bulk import"));
SECTIONS.push(bulletP("Pre-built connector BCA/Mandiri/BRI/BNI auto-detect"));
SECTIONS.push(bulletP("Single-command Docker deployment, on-prem ready untuk data residency"));

SECTIONS.push(h3("Operasional"));
SECTIONS.push(bulletP("UI Bahasa Indonesia (toggle EN tersedia)"));
SECTIONS.push(bulletP("Mobile PWA + Telegram bot untuk officer mobility"));
SECTIONS.push(bulletP("LTKM auto-generated, officer cukup review + approve"));

SECTIONS.push(h3("Change Management"));
SECTIONS.push(bulletP("Pilot mode parallel run 1-3 bulan dengan sistem lama"));
SECTIONS.push(bulletP("Trial 30 hari + money-back guarantee 90 hari (Enterprise)"));
SECTIONS.push(bulletP("Time-to-value: <1 minggu fitur dasar, <1 bulan full integration"));
SECTIONS.push(bulletP("Training: Free=docs+community, Pro=email 24h SLA, Enterprise=dedicated CSM"));

SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === 8. PROGRESS & STATUS ===
SECTIONS.push(h1("8. Progress & Current Status"));

SECTIONS.push(h2("8.1 Progress Since the 1st Submission"));
SECTIONS.push(infoBox(
  "Tahap 1: Konsep + Layer 2 prototype standalone\n" +
  "Tahap 2: Full 4-layer end-to-end MVP terverifikasi (40+ komponen)",
  COLOR_ACCENT,
));
SECTIONS.push(body(
  "Core 4-layer trained dan API-ready: XGBoost+SHAP (Layer 0), IsolationForest+Autoencoder+rules (Layer 1), GraphSAGE GNN multi-chain (Layer 2), Jinja2+Claude LLM narrative (Layer 3)."
));
SECTIONS.push(body(
  "Coverage Expansion baru: DNFBP module (Property, HVA, UBO, Shell Company detector), multi-chain crypto (BTC/ETH/BSC/Polygon/Tron), OFAC+UN+DTTOT sanctions integration (1.000+ entitas), negative news scraper (5 media Indonesia)."
));
SECTIONS.push(body(
  "UX & Mobility baru: Web UI 13-tab (termasuk Privacy Coin Monitor), Mobile PWA installable, Telegram bot officer dengan command /privacycoin, Command Palette ⌘K, WebSocket alerts, i18n ID/EN, Investigation Timeline viz."
));
SECTIONS.push(body(
  "MLOps & Production: Prometheus+Grafana (7 panels), MLflow registry, Apache Airflow 4 DAGs, immutable audit log, Case Management workflow, GitHub Actions CI/CD, Docker+Kubernetes deploy. Validasi: 14/14 tests passing, 62+ REST endpoints, <30 detik ingestion → LTKM."
));

SECTIONS.push(h2("8.2 Current Status"));
SECTIONS.push(infoBox(
  "PROTOTYPE (Functional MVP) — siap pilot",
  "166534",
));
SECTIONS.push(body(
  "40+ task selesai, 62+ API endpoints (termasuk /v1/privacy-coin/*), 13 UI tab, OFAC+UN data ter-load, Docker stack working, 14/14 tests pass. Next 3 bulan: pilot 1 bank via OJK Sandbox, PostgreSQL migration, PPATK SIPESAT MoU, retrain di data real (Elliptic + IBM AML)."
));

SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));

// === 9. ATTACHMENTS ===
SECTIONS.push(h1("9. Attachments & Links"));

SECTIONS.push(h2("9.1 Repository & Demo"));
SECTIONS.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2400, 6960],
  rows: [
    labelValueRow("GitHub Repository", "[ISI: https://github.com/USERNAME/fincrime-ai]"),
    labelValueRow("Demo Video (5 menit)", "[ISI: https://drive.google.com/file/d/XXXXX/view]"),
    labelValueRow("Live Demo URL", "[ISI: http://demo.fincrime.id atau localhost:8000 saat presentasi]"),
    labelValueRow("API Documentation", "Available at /docs (OpenAPI Swagger)"),
    labelValueRow("Code Repository Size", "130+ Python modules, 62+ API endpoints, 13 UI tabs"),
  ],
}));

SECTIONS.push(h2("9.2 Dokumentasi Tambahan"));
SECTIONS.push(bulletP("README.md — Quick start dan setup guide"));
SECTIONS.push(bulletP("docs/architecture.md — Detail arsitektur 4-layer + microservices"));
SECTIONS.push(bulletP("docs/api.md — Full REST API reference"));
SECTIONS.push(bulletP("docs/deployment.md — Production deployment (Docker + K8s)"));
SECTIONS.push(bulletP("docs/real_data_guide.md — Panduan integrasi data real (Bahasa Indonesia)"));

SECTIONS.push(h2("9.3 Format File"));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Format: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "PDF (max 5 MB)", font: FONT, size: 22 }),
]));
SECTIONS.push(bulletPRich([
  new TextRun({ text: "Penamaan file: ", bold: true, font: FONT, size: 22 }),
  new TextRun({ text: "[ID Tim] - FinCrime End-to-End Financial Crime Intelligence System.pdf", font: FONT, size: 22, italics: true }),
]));

// === FOOTER PAGE ===
SECTIONS.push(new Paragraph({ children: [new PageBreak()] }));
SECTIONS.push(
  pRich([new TextRun({ text: "", size: 22 })], { spacingBefore: 2000 }),
  pRich([new TextRun({
    text: "Terima Kasih",
    bold: true, font: FONT, color: COLOR_ACCENT, size: 56,
  })], { align: AlignmentType.CENTER, spacingAfter: 400 }),
  pRich([new TextRun({
    text: "FinCrime",
    bold: true, font: FONT, color: COLOR_PRIMARY, size: 36,
  })], { align: AlignmentType.CENTER, spacingAfter: 200 }),
  pRich([new TextRun({
    text: "End-to-End Financial Crime Intelligence System for Indonesia",
    italics: true, font: FONT, color: COLOR_MUTED, size: 22,
  })], { align: AlignmentType.CENTER, spacingAfter: 600 }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 400, after: 400 },
    border: {
      top: { style: BorderStyle.SINGLE, size: 12, color: COLOR_ACCENT, space: 4 },
    },
    children: [new TextRun({
      text: "Bank Indonesia · Program Inovasi Digital Indonesia 2026",
      font: FONT, color: COLOR_PRIMARY, size: 22,
    })],
  }),
);

// === DOCUMENT ASSEMBLY ===
const doc = new Document({
  creator: "FinCrime Team",
  title: "FinCrime - Proposal Tahap 2 PIDI",
  description: "End-to-End Financial Crime Intelligence System for Indonesia",
  styles: {
    default: {
      document: { run: { font: FONT, size: 22 } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: COLOR_PRIMARY },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: COLOR_PRIMARY },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: FONT, color: COLOR_ACCENT },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({
            text: "FinCrime — Proposal Tahap 2 PIDI 2026",
            font: FONT, color: COLOR_MUTED, size: 18, italics: true,
          })],
          border: {
            bottom: { style: BorderStyle.SINGLE, size: 6, color: COLOR_ACCENT, space: 4 },
          },
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          tabStops: [
            { type: TabStopType.CENTER, position: 4680 },
            { type: TabStopType.RIGHT, position: 9360 },
          ],
          border: {
            top: { style: BorderStyle.SINGLE, size: 6, color: COLOR_ACCENT, space: 4 },
          },
          children: [
            new TextRun({ text: "© 2026 FinCrime Team", font: FONT, size: 18, color: COLOR_MUTED }),
            new TextRun({ text: "\tFinCrime Proposal\t", font: FONT, size: 18, color: COLOR_MUTED }),
            new TextRun({ text: "Hal. ", font: FONT, size: 18, color: COLOR_MUTED }),
            new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: COLOR_MUTED }),
            new TextRun({ text: " / ", font: FONT, size: 18, color: COLOR_MUTED }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 18, color: COLOR_MUTED }),
          ],
        })],
      }),
    },
    children: SECTIONS,
  }],
});

// Build the document
Packer.toBuffer(doc).then(buffer => {
  const outPath = path.join("D:", "kuliah", "BANK INDONESIA", "FInCrime", "Proposal_Tahap_2_FinCrime.docx");
  fs.writeFileSync(outPath, buffer);
  const size = fs.statSync(outPath).size;
  console.log(`✓ Word document created: ${outPath}`);
  console.log(`  Size: ${(size / 1024).toFixed(1)} KB`);
  console.log(`  Sections: ${SECTIONS.length} content blocks`);
}).catch(err => {
  console.error("Error:", err);
  process.exit(1);
});
