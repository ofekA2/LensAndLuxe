import React, { useState } from "react";
import ItemCard from "./ItemCard";

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
      formData.append("image", file);

      const response = await fetch("http://localhost:5001/api/search", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data);
      } else {
        const text = await response.text().catch(() => "");
        setError(`Search failed. ${text || ""}`.trim());
      }
    } catch (err) {
      setError("Connection error. Make sure the server is running.");
    } finally {
      setLoading(false);
    }
  };

  const normalizeForItemCard = (resItem, i) => {
    const noExt = resItem.filename.replace(/\.(jpe?g|png|gif)$/i, "");
    return {
      id: `sr-${i}`,
      name: noExt,          
      image: resItem.image_url,
      description: "",
      link: ""               
    };
  };

  return (
    <div className="search-container">
      <h1 className="hero-title">Find Your Look from a Photo</h1>
      <p className="hero-sub">Upload an inspo pic. We’ll find similar pieces.</p>

      <form onSubmit={handleSubmit} className="image-search-form">
        <label className="file-upload-label" htmlFor="file-input">
          {file ? (
            <div className="file-name">{file.name}</div>
          ) : (
            <div className="placeholder">
              <span>📷</span>
              <div>Drop an image here or click to upload</div>
              <small>JPG/PNG up to ~10MB</small>
            </div>
          )}
        </label>
        <input
          id="file-input"
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          required
        />

        <button type="submit" disabled={!file || loading}>
          {loading ? "Searching..." : "Search for Similar Clothes"}
        </button>
      </form>

      {error && (
        <div className="error">
          <p>{error}</p>
        </div>
      )}

      {results && (
        <div className="results">
          <h3>Similar items found ({results.total_found})</h3>

          <div className="items-grid results-grid">
            {results.similar_items.map((ri, idx) => (
              <ItemCard key={idx} item={normalizeForItemCard(ri, idx)} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ImageSearch;