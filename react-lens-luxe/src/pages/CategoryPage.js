import React from 'react';

function CategoryPage({ category }) {
  return (
    <div className="category">
      <h2>{category} Collection</h2>
      {/* Later: render the grid of clothes for this category */}
    </div>
  );
}

export default CategoryPage;
