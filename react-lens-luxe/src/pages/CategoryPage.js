import React from "react";
import { useParams } from "react-router-dom";
import ItemCard from "../components/ItemCard";
import { CATEGORY_MAP, CATEGORY_LABELS } from "../data";

function CategoryPage() {
  const { category } = useParams();           
  const items = CATEGORY_MAP[category] || []; 
  const title = CATEGORY_LABELS[category] || "Catalog";

  if (!CATEGORY_MAP[category]) {
    return (
      <div className="category-container">
        <h1 className="category-title">{title}</h1>
        <p>Sorry, the “{category}” category doesn’t exist yet.</p>
      </div>
    );
  }

  return (
    <div className="category-container">
      <h1 className="category-title">{title}</h1>
      <div className="items-grid">
        {items.map((item) => (
          <ItemCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}

export default CategoryPage;