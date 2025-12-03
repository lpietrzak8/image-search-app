import { useState, useRef } from "react";
import "./ContributePage.css";

const ContributePage = () => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [description, setDescription] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError("");
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    setPreviewUrl("");
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    if (!description && !selectedImage) {
      setError("Please add a description and select an image");
      setTimeout(() => setError(""), 3000);
      return;
    }

    if (!description) {
      setError("Please add a description");
      setTimeout(() => setError(""), 3000);
      return;
    }

    if (!selectedImage) {
      setError("Please select an image");
      setTimeout(() => setError(""), 3000);
      return;
    }

    // Tutaj będzie logika wysyłania do backendu
    console.log("Image:", selectedImage);
    console.log("Description:", description);
    setError("");
    setSuccess("Image uploaded successfully!");
    setTimeout(() => {
      setSuccess("");
      setSelectedImage(null);
      setPreviewUrl("");
      setDescription("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }, 3000);
  };

  return (
    <div className="contribute-page">
      <div className="contribute-container">
        <h1>Contribute Data</h1>
        <p className="subtitle">
          Help us improve our image search by uploading images with descriptions
        </p>

        <form onSubmit={handleSubmit} className="contribute-form">
          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what's in the image..."
              rows={4}
              className="description-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="image-upload">Upload Image</label>
            <div className="upload-area">
              <input
                ref={fileInputRef}
                type="file"
                id="image-upload"
                accept="image/*"
                onChange={handleImageSelect}
                className="file-input-hidden"
              />
              <label htmlFor="image-upload" className="upload-label">
                {selectedImage ? (
                  <span>✓ {selectedImage.name}</span>
                ) : (
                  <>
                    <span className="upload-icon">📁</span>
                    <span>Click to select an image</span>
                    <span className="upload-hint">or drag and drop</span>
                  </>
                )}
              </label>
            </div>
          </div>

          {previewUrl && (
            <div className="image-preview">
              <img src={previewUrl} alt="Preview" />
              <button
                type="button"
                onClick={removeImage}
                className="remove-image-btn"
              >
                ✕ Remove Image
              </button>
            </div>
          )}

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <button type="submit" className="submit-btn">
            Upload Image
          </button>
        </form>

        <div className="info-section">
          <h3>What happens next?</h3>
          <ol>
            <li>Your image is validated and stored securely</li>
            <li>Our AI analyzes the image and generates embeddings</li>
            <li>The image becomes searchable in our database</li>
            <li>You help improve search results for everyone</li>
          </ol>
        </div>

        <div className="security-info">
          <p>
            🛡️ This form is protected by reCAPTCHA to prevent spam and abuse
          </p>
        </div>
      </div>
    </div>
  );
};

export default ContributePage;
