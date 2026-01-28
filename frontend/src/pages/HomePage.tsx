import { useRef, useEffect, useState } from "react";
import axios from "axios";
import keycloak from "../keycloak";

const backendUrl = "/api/search";
const numberOfResults = 30;

interface HomePageProps {
  isLoggedIn: boolean;
}

function HomePage({ isLoggedIn }: HomePageProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const resultsRef = useRef<HTMLElement>(null);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [savedPhotos, setSavedPhotos] = useState<Set<string>>(new Set());
  const [savingPhoto, setSavingPhoto] = useState<string | null>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    if (isLoggedIn && keycloak.token) {
      axios
        .get("/api/user/photos", {
          headers: { Authorization: `Bearer ${keycloak.token}` },
        })
        .then((response) => {
          const urls = new Set(response.data.map((p: any) => p.image_url));
          setSavedPhotos(urls as Set<string>);
        })
        .catch((err) => console.error("Failed to load saved photos:", err));
    }
  }, [isLoggedIn]);

  const handleSavePhoto = async (img: any) => {
    if (!keycloak.token) return;

    setSavingPhoto(img.image_url);
    try {
      await axios.post(
        "/api/user/photos",
        {
          image_url: img.image_url,
          description: img.description,
          provider: img.provider,
        },
        {
          headers: { Authorization: `Bearer ${keycloak.token}` },
        }
      );
      setSavedPhotos((prev) => new Set(prev).add(img.image_url));
    } catch (err: any) {
      if (err.response?.status === 409) {
        setSavedPhotos((prev) => new Set(prev).add(img.image_url));
      } else {
        console.error("Failed to save photo:", err);
      }
    } finally {
      setSavingPhoto(null);
    }
  };

  const handleSearch = () => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    setQuery("");

    setLoading(true);
    setSearched(true);

    axios
      .get(backendUrl, {
        params: {
          s_query: trimmedQuery,
          k: numberOfResults,
        },
      })
      .then((response) => {
        const data = response.data;
        setResults(data);
      })
      .catch((error) => {
        console.error(`Search error: ${error}`);
        setResults([]);
      })
      .finally(() => setLoading(false));

    resultsRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <>
      <main className="main-content">
        <div className="search-container">
          <h1>
            Simply describe what you're looking for and search for your perfect
            photo
          </h1>
          <div className="search-bar-wrapper">
            <textarea
              ref={inputRef}
              className="search-input"
              placeholder="Search..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />

            <button className="search-button" onClick={handleSearch}>
              {loading ? "Searching..." : "Search for a photo"}
            </button>
          </div>
        </div>
      </main>
      <section ref={resultsRef} className="results-section">
        <h2>results:</h2>

        {loading && (
          <div className="loader-container">
            <div className="loader"></div>
            <p>Loading results...</p>
          </div>
        )}

        {!loading && searched && results.length === 0 && (
          <p>No results found</p>
        )}

        {!loading && !searched && results.length === 0 && (
          <p>Nothing to display yet</p>
        )}

        <div className={"results-grid"}>
          {[...results].map((img) => (
            <div key={img.id} className="image-card">
              <img
                src={img.image_url}
                alt={img.description || "photo"}
              />
              <a
                className="download-btn"
                href={img.image_url}
                download
                title="Download image"
              >
                ⬇
              </a>
              {isLoggedIn && (
                <button
                  className={`save-btn ${savedPhotos.has(img.image_url) ? "saved" : ""}`}
                  onClick={() => handleSavePhoto(img)}
                  disabled={savingPhoto === img.image_url || savedPhotos.has(img.image_url)}
                  title={savedPhotos.has(img.image_url) ? "Saved" : "Save to My Resources"}
                >
                  {savedPhotos.has(img.image_url) ? "✓" : "+"}
                </button>
              )}
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

export default HomePage;
