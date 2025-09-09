import React, { useState } from 'react';

function ImageSearch() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
    setResults(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch('http://localhost:5000/api/search', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data);
      } else {
        setError('Search failed. Please try again.');
      }
    } catch (err) {
      setError('Connection error. Make sure the server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-container">
      <h1>Lens & Luxe - Find Similar Clothes</h1>
      
      <form onSubmit={handleSubmit} className="search-form">
        <div className="file-input-container">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            required
          />
        </div>
        
        <button type="submit" disabled={!file || loading}>
          {loading ? 'Searching...' : 'Search for Similar Clothes'}
        </button>
      </form>

      {error && (
        <div className="error">
          <p>{error}</p>
        </div>
      )}

      {results && (
        <div className="results">
          <h2>Analysis Results:</h2>
          <p><strong>Clothing Type:</strong> {results.clothing_type}</p>
          <p><strong>Colors:</strong> {results.colors}</p>
          
          <h3>Similar Items Found ({results.total_found}):</h3>
          <div className="items-grid">
            {results.similar_items.map((item, index) => (
              <div key={index} className="item">
                 <img
                    src={item.image_url}
                    alt={item.filename}
                    style={{ width: '200px', height: '200px', objectFit: 'cover' }}
                  />
                <p>{item.filename}</p>
                <p>Match Score: {item.score}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ImageSearch;