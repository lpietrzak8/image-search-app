import { useRef, useEffect, useState } from "react";
import axios from "axios";

const backendUrl = "/api/search";
const numberOfResults = 30;

function HomePage() {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const resultsRef = useRef<HTMLElement>(null);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

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
            <img
              key={img.id}
              src={img.image_url}
              alt={img.description || "photo"}
            />
          ))}
        </div>
      </section>
    </>
  );
}

export default HomePage;
