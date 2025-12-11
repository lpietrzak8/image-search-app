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

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSearch = () => {
    if (!query.trim()) return;

    setLoading(true);

    axios
      .get(backendUrl, {
        params: {
          s_query: query,
          k: numberOfResults,
        },
      })
      .then((response) => {
        const data = response.data;
        setResults(data);
      })
      .catch((error) => {
        console.error(`Search error: ${error}`);
        setResults([{ description: "Something went wrong" }]);
      })
      .finally(() => setLoading(false));

    resultsRef.current?.scrollIntoView({ behavior: "smooth" });
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
              placeholder=""
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />

            <button className="search-button" onClick={handleSearch}>
              {loading ? "Searching..." : "Search for a photo"}
            </button>
          </div>
        </div>
      </main>
      <section ref={resultsRef} className="results-section">
        <h2>results:</h2>

        {loading && <p>Loading results...</p>}

        {!loading && results.length == 0 && <p>Nothing to display yet</p>}

        <div className={"results-grid"}>
          {[...results].map((img) => (
            <img
              key={img.id}
              src={img.image_url}
              alt={img.description || "photo"}
            />
          ))}
          {/* TODO add style to the grid maybe change it into FixedSizeList */}
        </div>
      </section>
    </>
  );
}

export default HomePage;
