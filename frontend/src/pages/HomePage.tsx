import { useRef, useEffect } from 'react';

function HomePage() {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const resultsRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  return (
    <>
      <main className="main-content">
        <div className="search-container">
          <h1>Simply describe what you're looking for and search for your perfect photo</h1>
          <div className="search-bar-wrapper">
            <textarea ref={inputRef} className="search-input" placeholder="" />
            <button className="search-button" onClick={() => resultsRef.current?.scrollIntoView({ behavior: 'smooth' })}>Search for a photo</button>
          </div>
        </div>
      </main>
      <section ref={resultsRef} className="results-section">
        <h2>results:</h2>
      </section>
    </>
  );
}

export default HomePage;
