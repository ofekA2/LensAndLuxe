import React, { useState } from "react";
import { tidyTitle, inferMeta } from "../utils/itemMeta";

function ItemCard({ item }) {
  const [open, setOpen] = useState(false);

  const cleanedName = tidyTitle(item.name || "");
  const displayName = cleanedName.replace(/\s*\([^)]*\)$/, "");

  const skuMatch = (item.name || "").match(/\(([^)]+)\)$/);
  const sku = skuMatch ? skuMatch[1] : null;

  const buyUrl = item.link || (sku ? `https://www.next.co.uk/style/${sku}` : null);

  const parsed = inferMeta(item.name || "");
  const color =
    item.color || parsed.color || null;
  const materials =
    Array.isArray(item.materials) && item.materials.length > 0
      ? item.materials
      : parsed.materials;

  return (
    <>
      <div className="item-card" onClick={() => setOpen(true)}>
        <img src={item.image} alt={displayName} />
        <div className="item-name">{displayName}</div>
      </div>

      {open && (
        <div className="modal-backdrop" onClick={() => setOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">{displayName}</h3>

            {item.description && (
              <p className="modal-description">{item.description}</p>
            )}

            <img src={item.image} alt={displayName} className="modal-image" />

            <div className="modal-meta">
              {color && (
                <div className="meta-row">
                  <span className="meta-label">Color:</span>
                  <span className="meta-value">{color}</span>
                </div>
              )}

              {materials && materials.length > 0 && (
                <div className="meta-row">
                  <span className="meta-label">Material:</span>
                  <span className="meta-value">{materials.join(" • ")}</span>
                </div>
              )}

              {parsed.fabrics && parsed.fabrics.length > 0 && (
                <div className="meta-row">
                  <span className="meta-label">Fabric:</span>
                  <span className="meta-value">{parsed.fabrics.join(" • ")}</span>
                </div>
              )}
            </div>

            {buyUrl && (
              <a
                href={buyUrl}
                target="_blank"
                rel="noreferrer"
                className="modal-link"
              >
                Buy on Next
              </a>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default ItemCard;