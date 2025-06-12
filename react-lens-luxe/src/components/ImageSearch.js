import React, { useState } from 'react';

function ImageSearch({ onSearch }) {
  const [file, setFile] = useState(null);

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type.startsWith('image/')) {
      setFile(dropped);
    }
  };

  const handleChange = (e) => setFile(e.target.files[0]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file) return;
    console.log('Searching by image:', file);
    // TODO: call your backend here
    onSearch && onSearch(file);
  };

  return (
    <form className="image-search-form" onSubmit={handleSubmit}>
      <label
        htmlFor="file-upload"
        className="file-upload-label"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        {file ? (
          <p className="file-name">{file.name}</p>
        ) : (
          <div className="placeholder">
            <span role="img" aria-label="camera">📷</span>
            <p>Click or drag an image here</p>
          </div>
        )}
      </label>
      <input
        id="file-upload"
        type="file"
        accept="image/*"
        onChange={handleChange}
      />
      <button type="submit" disabled={!file}>Search</button>
    </form>
  );
}

export default ImageSearch;