const fs = require("fs");
const path = require("path");

const CATEGORY = (process.argv[2] || "").trim();
if (!CATEGORY) {
  console.error("❌ Please provide a category. Example: node generateCategoryData.js dresses d");
  process.exit(1);
}

const ID_PREFIX = (process.argv[3] || CATEGORY[0] || "x").toLowerCase();

const projectRoot = __dirname;
const imgDir = path.join(projectRoot, "public", "images", CATEGORY);
const outFile = path.join(projectRoot, "src", "data", `${CATEGORY}Data.js`);

if (!fs.existsSync(imgDir)) {
  console.error(`❌ Folder not found: ${imgDir}\nCreate it and put images inside (jpg/png/gif).`);
  process.exit(1);
}

const files = fs
  .readdirSync(imgDir)
  .filter((f) => /\.(jpe?g|png|gif)$/i.test(f))
  .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));

const data = files.map((filename, i) => {
  const name = filename
    .replace(/\.(jpe?g|png|gif)$/i, "")
    .replace(/[-_]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return {
    id: `${ID_PREFIX}${i + 1}`,
    name,
    image: `/images/${CATEGORY}/${filename}`,
    description: "",
    link: "",
  };
});

const content =
  `// THIS FILE IS AUTO-GENERATED. DO NOT EDIT.\n` +
  `export default ${JSON.stringify(data, null, 2)};\n`;

fs.writeFileSync(outFile, content, "utf-8");
console.log(`✅ Generated ${data.length} items → src/data/${CATEGORY}Data.js`);