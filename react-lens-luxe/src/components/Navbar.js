import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
  const categories = [
    'Trousers',
    'Tops',
    'Skirts',
    'Shorts',
    'Shirts',
    'Leggings',
    'Knitwear',
    'Jeans',
    'Dresses'
  ];

  return (
    <nav className="navbar">
      <Link to="/" className="logo"> Lens&Luxe </Link>
      <div className="nav-links">
        {categories.map((cat) => (
          <Link key={cat} to={`/category/${cat.toLowerCase()}`} className="nav-link">
            {cat}
          </Link>
        ))}
      </div>
    </nav>
  );
}

export default Navbar;