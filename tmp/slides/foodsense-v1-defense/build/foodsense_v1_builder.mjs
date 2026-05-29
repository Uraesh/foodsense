// Node-oriented editable pro deck builder.
// Run this after editing SLIDES, SOURCES, and layout functions.
// The init script installs a sibling node_modules/@oai/artifact-tool package link
// and package.json with type=module for shell-run eval builders. Run with the
// Node executable from Codex workspace dependencies or the platform-appropriate
// command emitted by the init script.
// Do not use pnpm exec from the repo root or any Node binary whose module
// lookup cannot resolve the builder's sibling node_modules/@oai/artifact-tool.

const fs = await import("node:fs/promises");
const path = await import("node:path");
const { Presentation, PresentationFile } = await import("@oai/artifact-tool");

const W = 1280;
const H = 720;

const DECK_ID = "foodsense-v1-defense";
const OUT_DIR = "D:\\Licience 3 IA-BD\\SEMANTIC-SEARCH\\docs\\presentation\\foodsense-v1-defense";
const REF_DIR = "D:\\Licience 3 IA-BD\\SEMANTIC-SEARCH\\tmp\\slides\\foodsense-v1-defense\\references";
const SCRATCH_DIR = path.resolve(process.env.PPTX_SCRATCH_DIR || path.join("tmp", "slides", DECK_ID));
const PREVIEW_DIR = path.join(SCRATCH_DIR, "preview");
const VERIFICATION_DIR = path.join(SCRATCH_DIR, "verification");
const INSPECT_PATH = path.join(SCRATCH_DIR, "inspect.ndjson");
const MAX_RENDER_VERIFY_LOOPS = 3;

const INK = "#101214";
const GRAPHITE = "#30363A";
const MUTED = "#687076";
const PAPER = "#F7F4ED";
const PAPER_96 = "#F7F4EDF5";
const WHITE = "#FFFFFF";
const ACCENT = "#27C47D";
const ACCENT_DARK = "#116B49";
const GOLD = "#D7A83D";
const CORAL = "#E86F5B";
const TRANSPARENT = "#00000000";

const TITLE_FACE = "Caladea";
const BODY_FACE = "Lato";
const MONO_FACE = "Aptos Mono";

const FALLBACK_PLATE_DATA_URL =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=";

const SOURCES = {
  repo: "FoodSense README, evaluation README and project journal dated April 2026.",
  metrics: "Versioned V1 metrics: Precision@3 0.75, Success@3 1.0, MRR 0.8333 vs lexical baseline 0.6667, 0.75, 0.75.",
  scope: "V1 scope validated in project documentation: ProductId is the search unit; summary is centered on client reviews.",
};

const SLIDES = [
  {
    kicker: "FoodSense V1",
    title: "Moteur de recherche semantique pour produits alimentaires",
    subtitle: "Une V1 centree sur l'intention de recherche, la robustesse technique et une evaluation comparative face au lexical.",
    expectedVisual: "Editorial cover with central title, thesis callout and warm data-research mood.",
    moment: "Rechercher par sens, pas seulement par mot-cle",
    notes: "Ouvrir la soutenance en rappelant l'objectif: construire une recherche semantique defendable, demonstrable et honnete sur ses limites.",
    sources: ["repo", "scope"],
  },
  {
    kicker: "Probleme",
    title: "Pourquoi une recherche semantique ?",
    subtitle: "La recherche mot-a-mot ne suffit pas lorsque l'utilisateur exprime un besoin, une intention ou une contrainte sans connaitre le nom exact du produit.",
    expectedVisual: "Three evidence cards describing keyword limits, user intent and project answer.",
    cards: [
      ["Constat", "Un utilisateur formule souvent une intention comme chocolat noir pauvre en sucre ou gluten free cookies, et non un nom de produit precis."],
      ["Limite", "Une recherche purement lexicale peut rater des resultats utiles si les termes exacts n'apparaissent pas ou si les formulations divergent."],
      ["Reponse", "FoodSense cherche a rapprocher la requete du sens present dans les avis agregees, tout en gardant un comportement robuste."],
    ],
    notes: "Donner un exemple de requete naturelle et expliquer pourquoi la semantique est pertinente.",
    sources: ["repo"],
  },
  {
    kicker: "Dataset",
    title: "Contrainte majeure : Amazon Fine Food Reviews",
    subtitle: "Le dataset est interessant pour la recherche semantique, mais il ne fournit pas un vrai catalogue produit riche avec un nom propre stable et des metadonnees nutritionnelles structurees.",
    expectedVisual: "Three metric-style statements framing the real dataset constraint.",
    metrics: [
      ["ProductId", "Unite de recherche V1", "Le produit est reconstruit autour de ProductId."],
      ["Avis agregees", "Matiere principale", "Summary, Text, note moyenne et nombre d'avis."],
      ["Pas de vrai catalogue", "Limite metier", "Pas de product_name officiel fiable pour un RAG complet."],
    ],
    notes: "Insister sur le fait que la V1 est bien un moteur de recherche semantique, mais pas encore un moteur catalogue ou nutritionnel complet.",
    sources: ["scope", "repo"],
  },
  {
    kicker: "Cadrage V1",
    title: "Ce que la V1 fait vraiment",
    subtitle: "Nous avons volontairement choisi un perimetre defendable, en livrant une recherche semantique sur documents produits reconstruits plutot qu'une recommandation nutritionnelle fragile.",
    expectedVisual: "Three cards describing V1 boundaries.",
    cards: [
      ["Recherche", "Chaque produit est represente par un document de recherche construit a partir de Summary, Text, note moyenne et nombre d'avis."],
      ["Interface", "Le frontend affiche ProductId, label infere, extraits utiles, score de pertinence et un bouton Resume centre sur les avis clients."],
      ["Honnetete", "La V1 n'est ni un moteur medical ni un RAG complet; elle pose une base fiable pour une V2 enrichie."],
    ],
    notes: "Cette slide doit rassurer: le perimetre a ete reduit pour livrer quelque chose de robuste.",
    sources: ["scope", "repo"],
  },
  {
    kicker: "Pipeline",
    title: "Du CSV aux documents produits",
    subtitle: "Le pipeline prepare le corpus avant la recherche: nettoyage, agregation et generation de documents produits prets pour la vectorisation.",
    expectedVisual: "Three cards describing the preparation flow.",
    cards: [
      ["Nettoyage", "Les donnees sont preparees avec Polars afin de retirer le bruit inutile et de normaliser les champs utiles aux traitements suivants."],
      ["Agregation", "Les reviews sont regroupees par ProductId pour reconstruire un document plus riche que chaque avis isole."],
      ["Artefacts", "Le pipeline produit des fichiers preprocesses et des embeddings locaux qui alimentent ensuite le backend et Qdrant."],
    ],
    notes: "Si le professeur insiste, rappeler que le pipeline a ete pense comme une base MLOps simple et reproductible.",
    sources: ["repo"],
  },
  {
    kicker: "Architecture",
    title: "Architecture technique de FoodSense",
    subtitle: "Le systeme s'appuie sur une separation claire entre interface, API, vectorisation et stockage vectoriel.",
    expectedVisual: "Three metric cards describing the system blocks.",
    metrics: [
      ["Next.js", "Frontend", "Experience de recherche et affichage des resultats."],
      ["FastAPI", "Backend", "Routes principales: /search et /summarize/{product_id}."],
      ["Qdrant + Ollama", "Recherche", "Base vectorielle Qdrant et embeddings bge-m3 localement."],
    ],
    notes: "Presenter l'enchainement: requete utilisateur vers backend, embedding, interrogation Qdrant, puis reponse structuree au frontend.",
    sources: ["repo"],
  },
  {
    kicker: "Retrieval",
    title: "Logique de recherche: semantic_hybrid",
    subtitle: "La V1 combine un signal semantique et un signal lexical afin de conserver une bonne robustesse meme sur machine locale contrainte.",
    expectedVisual: "Three cards for semantic, lexical and fallback.",
    cards: [
      ["Semantique", "La requete utilisateur est vectorisee avec bge-m3 puis comparee aux documents produits indexes dans Qdrant."],
      ["Hybride", "Le classement final combine un score semantique et un signal lexical pour renforcer les cas ou les mots comptent fortement."],
      ["Fallback", "Si l'embedding echoue, le backend bascule vers lexical_fallback afin de garantir une reponse plutot qu'un plantage."],
    ],
    notes: "Bien dire que le fallback est un mecanisme de resilience, pas un aveu d'echec architectural.",
    sources: ["repo"],
  },
  {
    kicker: "Interface",
    title: "Experience utilisateur de la V1",
    subtitle: "L'interface reste volontairement simple: une recherche, des resultats classes, des indices utiles et un bouton Resume pour lire plus vite les avis clients.",
    expectedVisual: "Three cards describing UI affordances.",
    cards: [
      ["Resultats", "Chaque resultat expose ProductId, un label infere, des extraits utiles, une note et un score de pertinence."],
      ["Resume", "Le bouton Resume reste central dans le cahier des charges; il repose par defaut sur une synthese extractive stable."],
      ["Transparence", "Si le backend tombe en lexical_fallback, l'interface peut l'indiquer honnetement a l'utilisateur."],
    ],
    notes: "Pendant l'oral, annoncer que la demo montrera la requete, le classement et le resume.",
    sources: ["scope", "repo"],
  },
  {
    kicker: "Evaluation",
    title: "Comparaison avec une baseline lexicale",
    subtitle: "Nous avons evalue la V1 sur un petit benchmark avec trois metriques: Precision@3, Success@3 et MRR.",
    expectedVisual: "Three metric cards with semantic results.",
    metrics: [
      ["0.75", "Precision@3 semantique", "Baseline lexicale: 0.6667."],
      ["1.00", "Success@3 semantique", "Baseline lexicale: 0.75."],
      ["0.8333", "MRR semantique", "Baseline lexicale: 0.75."],
    ],
    notes: "Conclure explicitement que la recherche semantique depasse la baseline lexicale sur le benchmark versionne.",
    sources: ["metrics", "repo"],
  },
  {
    kicker: "Demo",
    title: "Scenario de demonstration conseille",
    subtitle: "La demonstration doit etre courte, stable et centree sur une preuve claire de valeur.",
    expectedVisual: "Three cards for the demo sequence.",
    cards: [
      ["1. Requete", "Lancer une requete simple et credible comme dark chocolate low sugar ou gluten free cookies."],
      ["2. Lecture", "Montrer les resultats classes, commenter le score de pertinence et rappeler que l'unite retournee est ProductId."],
      ["3. Resume", "Cliquer sur Resume pour montrer la synthese des avis clients et illustrer la valeur de lecture rapide."],
    ],
    notes: "Si la machine est fragile, garder une capture de secours. Si tout fonctionne, rester sur une seule requete forte.",
    sources: ["repo"],
  },
  {
    kicker: "Limites",
    title: "Limites identifiees en V1",
    subtitle: "La V1 est solide techniquement, mais elle reste limitee par le dataset et par le cout local de l'inference d'embedding.",
    expectedVisual: "Three cards framing current limits.",
    cards: [
      ["Dataset", "L'absence de vrais noms de produits et de metadonnees nutritionnelles empeche une recherche produit riche ou un RAG bien ancre."],
      ["Ressources", "Sur machine locale, l'embedding avec Ollama peut devenir fragile lorsque la RAM est sous pression."],
      ["Benchmark", "Le jeu de requetes reste encore petit; une evaluation V2 devra etre plus large et mieux annotee."],
    ],
    notes: "Dire que ces limites sont connues, documentees et deja prises en compte dans la vision V2.",
    sources: ["repo", "metrics"],
  },
  {
    kicker: "Suite",
    title: "Vision V2",
    subtitle: "La V2 visera un dataset enrichi avec de vrais noms de produits, une recherche plus propre et une generation mieux ancree.",
    expectedVisual: "Three metric cards for the roadmap.",
    metrics: [
      ["Dataset enrichi", "Vrai product_name", "Base plus favorable a une recherche produit et a un futur RAG."],
      ["Retrieval plus leger", "FastEmbed possible", "Reduction du cout d'embedding et meilleure stabilite locale."],
      ["RAG pertinent", "Apres enrichissement", "Generation utile seulement quand le contexte recuperé devient propre."],
    ],
    notes: "Clore en montrant que la V1 n'est pas une fin, mais une fondation propre pour une V2 plus metier.",
    sources: ["repo", "scope"],
  },
];

const inspectRecords = [];

async function pathExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readImageBlob(imagePath) {
  const bytes = await fs.readFile(imagePath);
  if (!bytes.byteLength) {
    throw new Error(`Image file is empty: ${imagePath}`);
  }
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

async function normalizeImageConfig(config) {
  if (!config.path) {
    return config;
  }
  const { path: imagePath, ...rest } = config;
  return {
    ...rest,
    blob: await readImageBlob(imagePath),
  };
}

async function ensureDirs() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const obsoleteFinalArtifacts = [
    "preview",
    "verification",
    "inspect.ndjson",
    ["presentation", "proto.json"].join("_"),
    ["quality", "report.json"].join("_"),
  ];
  for (const obsolete of obsoleteFinalArtifacts) {
    await fs.rm(path.join(OUT_DIR, obsolete), { recursive: true, force: true });
  }
  await fs.mkdir(SCRATCH_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(VERIFICATION_DIR, { recursive: true });
}

function lineConfig(fill = TRANSPARENT, width = 0) {
  return { style: "solid", fill, width };
}

function recordShape(slideNo, shape, role, shapeType, x, y, w, h) {
  if (!slideNo) return;
  inspectRecords.push({
    kind: "shape",
    slide: slideNo,
    id: shape?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    shapeType,
    bbox: [x, y, w, h],
  });
}

function addShape(slide, geometry, x, y, w, h, fill = TRANSPARENT, line = TRANSPARENT, lineWidth = 0, meta = {}) {
  const shape = slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: lineConfig(line, lineWidth),
  });
  recordShape(meta.slideNo, shape, meta.role || geometry, geometry, x, y, w, h);
  return shape;
}

function normalizeText(text) {
  if (Array.isArray(text)) {
    return text.map((item) => String(item ?? "")).join("\n");
  }
  return String(text ?? "");
}

function textLineCount(text) {
  const value = normalizeText(text);
  if (!value.trim()) {
    return 0;
  }
  return Math.max(1, value.split(/\n/).length);
}

function requiredTextHeight(text, fontSize, lineHeight = 1.18, minHeight = 8) {
  const lines = textLineCount(text);
  if (lines === 0) {
    return minHeight;
  }
  return Math.max(minHeight, lines * fontSize * lineHeight);
}

function assertTextFits(text, boxHeight, fontSize, role = "text") {
  const required = requiredTextHeight(text, fontSize);
  const tolerance = Math.max(2, fontSize * 0.08);
  if (normalizeText(text).trim() && boxHeight + tolerance < required) {
    throw new Error(
      `${role} text box is too short: height=${boxHeight.toFixed(1)}, required>=${required.toFixed(1)}, ` +
        `lines=${textLineCount(text)}, fontSize=${fontSize}, text=${JSON.stringify(normalizeText(text).slice(0, 90))}`,
    );
  }
}

function wrapText(text, widthChars) {
  const words = normalizeText(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > widthChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) {
    lines.push(current);
  }
  return lines.join("\n");
}

function recordText(slideNo, shape, role, text, x, y, w, h) {
  const value = normalizeText(text);
  inspectRecords.push({
    kind: "textbox",
    slide: slideNo,
    id: shape?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    text: value,
    textPreview: value.replace(/\n/g, " | ").slice(0, 180),
    textChars: value.length,
    textLines: textLineCount(value),
    bbox: [x, y, w, h],
  });
}

function recordImage(slideNo, image, role, imagePath, x, y, w, h) {
  inspectRecords.push({
    kind: "image",
    slide: slideNo,
    id: image?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    path: imagePath,
    bbox: [x, y, w, h],
  });
}

function applyTextStyle(box, text, size, color, bold, face, align, valign, autoFit, listStyle) {
  box.text = text;
  box.text.fontSize = size;
  box.text.color = color;
  box.text.bold = Boolean(bold);
  box.text.alignment = align;
  box.text.verticalAlignment = valign;
  box.text.typeface = face;
  box.text.insets = { left: 0, right: 0, top: 0, bottom: 0 };
  if (autoFit) {
    box.text.autoFit = autoFit;
  }
  if (listStyle) {
    box.text.style = "list";
  }
}

function addText(
  slide,
  slideNo,
  text,
  x,
  y,
  w,
  h,
  {
    size = 22,
    color = INK,
    bold = false,
    face = BODY_FACE,
    align = "left",
    valign = "top",
    fill = TRANSPARENT,
    line = TRANSPARENT,
    lineWidth = 0,
    autoFit = null,
    listStyle = false,
    checkFit = true,
    role = "text",
  } = {},
) {
  if (!checkFit && textLineCount(text) > 1) {
    throw new Error("checkFit=false is only allowed for single-line headers, footers, and captions.");
  }
  if (checkFit) {
    assertTextFits(text, h, size, role);
  }
  const box = addShape(slide, "rect", x, y, w, h, fill, line, lineWidth);
  applyTextStyle(box, text, size, color, bold, face, align, valign, autoFit, listStyle);
  recordText(slideNo, box, role, text, x, y, w, h);
  return box;
}

async function addImage(slide, slideNo, config, position, role, sourcePath = null) {
  const image = slide.images.add(await normalizeImageConfig(config));
  image.position = position;
  recordImage(slideNo, image, role, sourcePath || config.path || config.uri || "inline-data-url", position.left, position.top, position.width, position.height);
  return image;
}

async function addPlate(slide, slideNo, opacityPanel = false) {
  slide.background.fill = PAPER;
  addShape(slide, "ellipse", -120, -90, 420, 320, "#E9F5EE", TRANSPARENT, 0, { slideNo, role: "decor top left" });
  addShape(slide, "ellipse", 1000, -40, 260, 220, "#FCEED6", TRANSPARENT, 0, { slideNo, role: "decor top right" });
  addShape(slide, "ellipse", 920, 520, 360, 260, "#E8F0FF", TRANSPARENT, 0, { slideNo, role: "decor bottom right" });
  addShape(slide, "roundRect", 56, 92, 1168, 556, "#FFFFFFD8", "#E5DED1", 1, { slideNo, role: "main canvas" });
  const platePath = path.join(REF_DIR, `slide-${String(slideNo).padStart(2, "0")}.png`);
  if (await pathExists(platePath)) {
    await addImage(
      slide,
      slideNo,
      { path: platePath, fit: "cover", alt: `Text-free art-direction plate for slide ${slideNo}` },
      { left: 0, top: 0, width: W, height: H },
      "art plate",
      platePath,
    );
  } else {
    await addImage(
      slide,
      slideNo,
      { dataUrl: FALLBACK_PLATE_DATA_URL, fit: "cover", alt: `Fallback blank art plate for slide ${slideNo}` },
      { left: 0, top: 0, width: W, height: H },
      "fallback art plate",
      "fallback-data-url",
    );
  }
  if (opacityPanel) {
    addShape(slide, "rect", 0, 0, W, H, "#FFFFFFB8", TRANSPARENT, 0, { slideNo, role: "plate readability overlay" });
  }
}

function addHeader(slide, slideNo, kicker, idx, total) {
  addText(slide, slideNo, String(kicker || "").toUpperCase(), 64, 34, 430, 24, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    checkFit: false,
    role: "header",
  });
  addText(slide, slideNo, `${String(idx).padStart(2, "0")} / ${String(total).padStart(2, "0")}`, 1114, 34, 104, 24, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    align: "right",
    checkFit: false,
    role: "header",
  });
  addShape(slide, "rect", 64, 64, 1152, 2, INK, TRANSPARENT, 0, { slideNo, role: "header rule" });
  addShape(slide, "ellipse", 57, 57, 16, 16, ACCENT, INK, 2, { slideNo, role: "header marker" });
}

function addTitleBlock(slide, slideNo, title, subtitle = null, x = 64, y = 86, w = 780, dark = false) {
  const titleColor = dark ? PAPER : INK;
  const bodyColor = dark ? PAPER : GRAPHITE;
  addText(slide, slideNo, title, x, y, w, 142, {
    size: 40,
    color: titleColor,
    bold: true,
    face: TITLE_FACE,
    role: "title",
  });
  if (subtitle) {
    addText(slide, slideNo, subtitle, x + 2, y + 148, Math.min(w, 720), 70, {
      size: 19,
      color: bodyColor,
      face: BODY_FACE,
      role: "subtitle",
    });
  }
}

function addIconBadge(slide, slideNo, x, y, accent = ACCENT, kind = "signal") {
  addShape(slide, "ellipse", x, y, 54, 54, PAPER_96, INK, 1.2, { slideNo, role: "icon badge" });
  if (kind === "flow") {
    addShape(slide, "ellipse", x + 13, y + 18, 10, 10, accent, INK, 1, { slideNo, role: "icon glyph" });
    addShape(slide, "ellipse", x + 31, y + 27, 10, 10, accent, INK, 1, { slideNo, role: "icon glyph" });
    addShape(slide, "rect", x + 22, y + 25, 19, 3, INK, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
  } else if (kind === "layers") {
    addShape(slide, "roundRect", x + 13, y + 15, 26, 13, accent, INK, 1, { slideNo, role: "icon glyph" });
    addShape(slide, "roundRect", x + 18, y + 24, 26, 13, GOLD, INK, 1, { slideNo, role: "icon glyph" });
    addShape(slide, "roundRect", x + 23, y + 33, 20, 10, CORAL, INK, 1, { slideNo, role: "icon glyph" });
  } else {
    addShape(slide, "rect", x + 16, y + 29, 6, 12, accent, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "rect", x + 25, y + 21, 6, 20, accent, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
    addShape(slide, "rect", x + 34, y + 14, 6, 27, accent, TRANSPARENT, 0, { slideNo, role: "icon glyph" });
  }
}

function addCard(slide, slideNo, x, y, w, h, label, body, { accent = ACCENT, fill = PAPER_96, line = INK, iconKind = "signal" } = {}) {
  if (h < 156) {
    throw new Error(`Card is too short for editable pro-deck copy: height=${h.toFixed(1)}, minimum=156.`);
  }
  addShape(slide, "roundRect", x, y, w, h, fill, line, 1.2, { slideNo, role: `card panel: ${label}` });
  addShape(slide, "rect", x, y, 8, h, accent, TRANSPARENT, 0, { slideNo, role: `card accent: ${label}` });
  addIconBadge(slide, slideNo, x + 22, y + 24, accent, iconKind);
  addText(slide, slideNo, label, x + 88, y + 22, w - 108, 28, {
    size: 15,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    role: "card label",
  });
  const wrapped = wrapText(body, Math.max(28, Math.floor(w / 13)));
  const bodyY = y + 86;
  const bodyH = h - (bodyY - y) - 22;
  if (bodyH < 54) {
    throw new Error(`Card body area is too short: height=${bodyH.toFixed(1)}, cardHeight=${h.toFixed(1)}, label=${JSON.stringify(label)}.`);
  }
  addText(slide, slideNo, wrapped, x + 24, bodyY, w - 48, bodyH, {
    size: 17,
    color: INK,
    face: BODY_FACE,
    role: `card body: ${label}`,
  });
}

function addMetricCard(slide, slideNo, x, y, w, h, metric, label, note = null, accent = ACCENT) {
  if (h < 132) {
    throw new Error(`Metric card is too short for editable pro-deck copy: height=${h.toFixed(1)}, minimum=132.`);
  }
  addShape(slide, "roundRect", x, y, w, h, PAPER_96, INK, 1.2, { slideNo, role: `metric panel: ${label}` });
  addShape(slide, "rect", x, y, w, 7, accent, TRANSPARENT, 0, { slideNo, role: `metric accent: ${label}` });
  addText(slide, slideNo, metric, x + 22, y + 24, w - 44, 54, {
    size: 34,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "metric value",
  });
  addText(slide, slideNo, label, x + 24, y + 82, w - 48, 38, {
    size: 16,
    color: GRAPHITE,
    face: BODY_FACE,
    role: "metric label",
  });
  if (note) {
    addText(slide, slideNo, note, x + 24, y + h - 42, w - 48, 22, {
      size: 10,
      color: MUTED,
      face: BODY_FACE,
      role: "metric note",
    });
  }
}

function addNotes(slide, body, sourceKeys) {
  const sourceLines = (sourceKeys || []).map((key) => `- ${SOURCES[key] || key}`).join("\n");
  slide.speakerNotes.setText(`${body || ""}\n\n[Sources]\n${sourceLines}`);
}

function addReferenceCaption(slide, slideNo) {
  addText(
    slide,
    slideNo,
    "FoodSense V1 | Recherche semantique sur documents produits reconstruits",
    64,
    674,
    840,
    22,
    {
      size: 10,
      color: MUTED,
      face: BODY_FACE,
      checkFit: false,
      role: "caption",
    },
  );
}

async function slideCover(presentation) {
  const slideNo = 1;
  const data = SLIDES[0];
  const slide = presentation.slides.add();
  await addPlate(slide, slideNo);
  addShape(slide, "rect", 0, 0, W, H, "#FFFFFFCC", TRANSPARENT, 0, { slideNo, role: "cover contrast overlay" });
  addShape(slide, "rect", 64, 86, 7, 455, ACCENT, TRANSPARENT, 0, { slideNo, role: "cover accent rule" });
  addText(slide, slideNo, data.kicker, 86, 88, 520, 26, {
    size: 13,
    color: ACCENT_DARK,
    bold: true,
    face: MONO_FACE,
    role: "kicker",
  });
  addText(slide, slideNo, data.title, 82, 130, 785, 184, {
    size: 48,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover title",
  });
  addText(slide, slideNo, data.subtitle, 86, 326, 610, 86, {
    size: 20,
    color: GRAPHITE,
    face: BODY_FACE,
    role: "cover subtitle",
  });
  addShape(slide, "roundRect", 86, 456, 390, 92, PAPER_96, INK, 1.2, { slideNo, role: "cover moment panel" });
  addText(slide, slideNo, data.moment || "Replace with core idea", 112, 478, 336, 40, {
    size: 23,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover moment",
  });
  addReferenceCaption(slide, slideNo);
  addNotes(slide, data.notes, data.sources);
}

async function slideCards(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  await addPlate(slide, idx);
  addShape(slide, "rect", 0, 0, W, H, "#FFFFFFB8", TRANSPARENT, 0, { slideNo: idx, role: "content contrast overlay" });
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 760);
  const cards = data.cards?.length
    ? data.cards
    : [
        ["Replace", "Add a specific, sourced point for this slide."],
        ["Author", "Use native PowerPoint chart objects for charts; use deterministic geometry for cards and callouts."],
        ["Verify", "Render previews, inspect them at readable size, and fix actionable layout issues within 3 total render loops."],
      ];
  const cols = Math.min(3, cards.length);
  const cardW = (1114 - (cols - 1) * 24) / cols;
  const iconKinds = ["signal", "flow", "layers"];
  for (let cardIdx = 0; cardIdx < cols; cardIdx += 1) {
    const [label, body] = cards[cardIdx];
    const x = 84 + cardIdx * (cardW + 24);
    addCard(slide, idx, x, 378, cardW, 228, label, body, { iconKind: iconKinds[cardIdx % iconKinds.length] });
  }
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function slideMetrics(presentation, idx) {
  const data = SLIDES[idx - 1];
  const slide = presentation.slides.add();
  await addPlate(slide, idx);
  addShape(slide, "rect", 0, 0, W, H, "#FFFFFFBD", TRANSPARENT, 0, { slideNo: idx, role: "metrics contrast overlay" });
  addHeader(slide, idx, data.kicker, idx, SLIDES.length);
  addTitleBlock(slide, idx, data.title, data.subtitle, 64, 86, 700);
  const metrics = data.metrics || [
    ["00", "Replace metric", "Source"],
    ["00", "Replace metric", "Source"],
    ["00", "Replace metric", "Source"],
  ];
  const accents = [ACCENT, GOLD, CORAL];
  for (let metricIdx = 0; metricIdx < Math.min(3, metrics.length); metricIdx += 1) {
    const [metric, label, note] = metrics[metricIdx];
    addMetricCard(slide, idx, 92 + metricIdx * 370, 404, 330, 174, metric, label, note, accents[metricIdx % accents.length]);
  }
  addReferenceCaption(slide, idx);
  addNotes(slide, data.notes, data.sources);
}

async function createDeck() {
  await ensureDirs();
  if (!SLIDES.length) {
    throw new Error("SLIDES must contain at least one slide.");
  }
  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  await slideCover(presentation);
  for (let idx = 2; idx <= SLIDES.length; idx += 1) {
    const data = SLIDES[idx - 1];
    if (data.metrics) {
      await slideMetrics(presentation, idx);
    } else {
      await slideCards(presentation, idx);
    }
  }
  return presentation;
}

async function saveBlobToFile(blob, filePath) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  await fs.writeFile(filePath, bytes);
}

async function writeInspectArtifact(presentation) {
  inspectRecords.unshift({
    kind: "deck",
    id: DECK_ID,
    slideCount: presentation.slides.count,
    slideSize: { width: W, height: H },
  });
  presentation.slides.items.forEach((slide, index) => {
    inspectRecords.splice(index + 1, 0, {
      kind: "slide",
      slide: index + 1,
      id: slide?.id || `slide-${index + 1}`,
    });
  });
  const lines = inspectRecords.map((record) => JSON.stringify(record)).join("\n") + "\n";
  await fs.writeFile(INSPECT_PATH, lines, "utf8");
}

async function currentRenderLoopCount() {
  const logPath = path.join(VERIFICATION_DIR, "render_verify_loops.ndjson");
  if (!(await pathExists(logPath))) return 0;
  const previous = await fs.readFile(logPath, "utf8");
  return previous.split(/\r?\n/).filter((line) => line.trim()).length;
}

async function nextRenderLoopNumber() {
  return (await currentRenderLoopCount()) + 1;
}

async function appendRenderVerifyLoop(presentation, previewPaths, pptxPath) {
  const logPath = path.join(VERIFICATION_DIR, "render_verify_loops.ndjson");
  const priorCount = await currentRenderLoopCount();
  const record = {
    kind: "render_verify_loop",
    deckId: DECK_ID,
    loop: priorCount + 1,
    maxLoops: MAX_RENDER_VERIFY_LOOPS,
    capReached: priorCount + 1 >= MAX_RENDER_VERIFY_LOOPS,
    timestamp: new Date().toISOString(),
    slideCount: presentation.slides.count,
    previewCount: previewPaths.length,
    previewDir: PREVIEW_DIR,
    inspectPath: INSPECT_PATH,
    pptxPath,
  };
  await fs.appendFile(logPath, JSON.stringify(record) + "\n", "utf8");
  return record;
}

async function verifyAndExport(presentation) {
  await ensureDirs();
  const nextLoop = await nextRenderLoopNumber();
  if (nextLoop > MAX_RENDER_VERIFY_LOOPS) {
    throw new Error(
      `Render/verify/fix loop cap reached: ${MAX_RENDER_VERIFY_LOOPS} total renders are allowed. ` +
        "Do not rerender; note any remaining visual issues in the final response.",
    );
  }
  await writeInspectArtifact(presentation);
  const previewPaths = [];
  for (let idx = 0; idx < presentation.slides.items.length; idx += 1) {
    const slide = presentation.slides.items[idx];
    const preview = await presentation.export({ slide, format: "png", scale: 1 });
    const previewPath = path.join(PREVIEW_DIR, `slide-${String(idx + 1).padStart(2, "0")}.png`);
    await saveBlobToFile(preview, previewPath);
    previewPaths.push(previewPath);
  }
  const pptxBlob = await PresentationFile.exportPptx(presentation);
  const pptxPath = path.join(OUT_DIR, "output.pptx");
  await pptxBlob.save(pptxPath);
  const loopRecord = await appendRenderVerifyLoop(presentation, previewPaths, pptxPath);
  return { pptxPath, loopRecord };
}

const presentation = await createDeck();
const result = await verifyAndExport(presentation);
console.log(result.pptxPath);
