import { useRef, useEffect, useState } from "react";
import axios from "axios";

const backendUrl = "/api/search";
const numberOfResults = 30;

interface HomePageProps {
  isLoggedIn: boolean;
  setSelectedPost: any;
  savingPhoto: string | null;
  handleSavePhoto: (img: object) => void;
  savedPhotos: Map<string,any>;
  results: any[];
  setResults: (results: any[]) => void;
}

interface searchStatus {
  percent: number;
  status: string;
}

function HomePage(
    { isLoggedIn, setSelectedPost, savingPhoto, handleSavePhoto, savedPhotos, results, setResults }: HomePageProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const resultsRef = useRef<HTMLElement>(null);

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [progress, setProgress] = useState<searchStatus | null>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSearch = async () => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) return;

    setQuery("");
    setProgress({percent: 0, status: "started"});
    setLoading(true);
    setSearched(true);

    try {
      const response = await axios.get(backendUrl, {
        params: {
              s_query: trimmedQuery,
              k: numberOfResults,
            },
          });

      const { job_id } = response.data;

      const es = new EventSource(`/api/search/stream/${job_id}`);

      es.addEventListener("progress", (e) => {
        const payload = JSON.parse(e.data)
        setProgress({percent:payload.percent, status: payload.tag})
      });

      es.addEventListener("done", (e) => {
        const payload = JSON.parse(e.data)
        setResults(payload)
        setLoading(false);
        setProgress(null);
        es.close()
      });

      es.addEventListener("error", (e) => {
        console.error("SSE error", e);
        setLoading(false);
        es.close();
      });
    } catch (error) {
      console.error("Search error:", error);
      setLoading(false);
      setResults([]);
    }

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
            <p>Loading results... {progress && (progress.percent)}%</p>
            {progress && (<p>Searching for tag: {progress.status}</p>)}
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
                onClick={() => setSelectedPost(img)}

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
                  className={`save-btn ${savedPhotos.has(img.source_url) ? "saved" : ""}`}
                  onClick={() => handleSavePhoto(img)}
                  disabled={savingPhoto === img.image_url || savedPhotos.has(img.source_url)}
                  title={savedPhotos.has(img.source_url) ? "Saved" : "Save to My Resources"}
                >
                  {savedPhotos.has(img.source_url) ? "✓" : "+"}
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
