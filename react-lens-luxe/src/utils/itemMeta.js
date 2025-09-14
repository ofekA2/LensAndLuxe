const COLORS = [
  "Black","White","Grey","Gray","Navy","Blue","Beige","Brown","Green","Red","Pink",
  "Purple","Yellow","Orange","Silver","Gold","Cream","Ivory","Nude","Khaki","Olive",
  "Burgundy","Cobalt","Teal","Charcoal","Tan","Lilac","Multi","Multicolor"
];

const MATERIALS = [
  "Cotton","Linen","Hemp","Ramie","Wool","Merino","Lambswool","Cashmere","Mohair","Alpaca",
  "Silk","Viscose","Rayon","Modal","Lyocell","Tencel","Acetate",
  "Polyester","Nylon","Polyamide","Acrylic","Elastane","Spandex","Lycra",
  "Polyurethane","PU","PVC","Leather","Down","Feather"
];

const FABRICS = [
  "Satin","Sateen","Chiffon","Crepe","Georgette","Poplin","Twill","Gabardine","Chambray",
  "Corduroy","Velvet","Velour","Jersey","Rib","Ribbed","Cable","Bouclé","Boucle","Tweed",
  "Jacquard","Brocade","Lace","Eyelet","Broderie","Crochet","Mesh","Tulle","Organza",
  "Fleece","Sherpa","Borg","Scuba","Ponte","Softshell","Shell","Taffeta","Seersucker",
  "Denim"
];

const QUALIFIERS = ["Organic","Recycled","Vegan","Faux","Genuine"];

export function tidyTitle(name) {
  let s = (name || "")
    .replace(/_/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim();

  s = s.replace(
    new RegExp(`\\b(\\d{1,3})\\s+(${MATERIALS.join("|")})\\b`, "gi"),
    (_m, num, mat) => `${num}% ${mat}`
  );
  return s;
}

export function inferMeta(name) {
  const title = tidyTitle(name || "");

  const colorRe = new RegExp(`\\b(${COLORS.join("|")})\\b`, "i");
  const color = (title.match(colorRe) || [])[1] || null;

  const matSet = new Set();
  const matRe = new RegExp(
    `\\b(?:(${QUALIFIERS.join("|")})\\s+)?(${MATERIALS.join("|")})\\b`,
    "gi"
  );
  let m;
  while ((m = matRe.exec(title)) !== null) {
    const qualifier = (m[1] || "").trim();
    const mat = normalizeWord(m[2]);
    const phrase = qualifier ? `${capitalize(qualifier)} ${mat}` : mat;
    matSet.add(phrase.toLowerCase());
  }
  const materials = Array.from(matSet).map(capitalizeEach);

  const fabSet = new Set();
  const fabRe = new RegExp(`\\b(${FABRICS.join("|")})\\b`, "gi");
  let f;
  while ((f = fabRe.exec(title)) !== null) {
    const raw = normalizeWord(f[1]);
    let pretty = raw;
    if (/^Ribbed?$/i.test(raw)) pretty = "Rib Knit";
    if (/^Cable$/i.test(raw))   pretty = "Cable Knit";
    fabSet.add(pretty.toLowerCase());
  }
  const fabrics = Array.from(fabSet).map(capitalizeEach);

  return { title, color, materials, fabrics };
}

function normalizeWord(s) {
  return s ? s.replace(/é/g, "e") : s;
}
function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;
}
function capitalizeEach(s) {
  return s
    .split(" ")
    .map(w => (w ? w.charAt(0).toUpperCase() + w.slice(1).toLowerCase() : w))
    .join(" ");
}