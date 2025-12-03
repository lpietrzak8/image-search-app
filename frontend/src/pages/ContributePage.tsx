import { useState, useRef, useEffect } from "react";
import "./ContributePage.css";

const RECAPTCHA_SITE_KEY = "6LcRbSAsAAAAAO7V3ox2Bs-5Trj-a3nECArCrc9G";

declare global {
  interface Window {
    grecaptcha: any;
  }
}

const ContributePage = () => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [description, setDescription] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [recaptchaLoaded, setRecaptchaLoaded] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = `https://www.google.com/recaptcha/api.js?render=${RECAPTCHA_SITE_KEY}`;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if (window.grecaptcha) {
        window.grecaptcha.ready(() => {
          setRecaptchaLoaded(true);
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      const scriptElement = document.querySelector(
        `script[src*="recaptcha/api.js"]`
      );
      if (scriptElement) {
        document.head.removeChild(scriptElement);
      }
    };
  }, []);

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

  const executeRecaptcha = async (): Promise<string | null> => {
    if (!recaptchaLoaded || !window.grecaptcha) {
      setError("reCAPTCHA is still loading. Please wait a moment.");
      setTimeout(() => setError(""), 3000);
      return null;
    }

    try {
      const token = await window.grecaptcha.execute(RECAPTCHA_SITE_KEY, {
        action: "submit",
      });
      return token;
    } catch (err) {
      console.error("reCAPTCHA error:", err);
      setError("reCAPTCHA verification failed. Please try again.");
      setTimeout(() => setError(""), 3000);
      return null;
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
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

    const recaptchaToken = await executeRecaptcha();
    if (!recaptchaToken) {
      return;
    }
    try {
      const formData = new FormData();
      formData.append("image", selectedImage);
      formData.append("description", description);
      formData.append("recaptcha_token", recaptchaToken);

      const response = await fetch("http://localhost:5001/api/contribute", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setError("");
        setSuccess(result.message || "Image uploaded successfully!");
        setTimeout(() => {
          setSuccess("");
          setSelectedImage(null);
          setPreviewUrl("");
          setDescription("");
          if (fileInputRef.current) {
            fileInputRef.current.value = "";
          }
        }, 3000);
      } else {
        setError(result.error || "Upload failed. Please try again.");
        setTimeout(() => setError(""), 3000);
      }
    } catch (err) {
      console.error("Upload error:", err);
      setError("Network error. Please check your connection.");
      setTimeout(() => setError(""), 3000);
    }
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
          <p>🛡️ This form is protected by Google reCAPTCHA v3</p>
          <small>
            This site is protected by reCAPTCHA and the Google{" "}
            <a
              href="https://policies.google.com/privacy"
              target="_blank"
              rel="noopener noreferrer"
            >
              Privacy Policy
            </a>{" "}
            and{" "}
            <a
              href="https://policies.google.com/terms"
              target="_blank"
              rel="noopener noreferrer"
            >
              Terms of Service
            </a>{" "}
            apply.
          </small>
        </div>
      </div>
    </div>
  );
};

export default ContributePage;
