import { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import MissionPage from "./pages/MissionPage";
import LogInPage from "./pages/LogInPage";
import MyAccountPage from "./pages/MyAccountPage";
import ContributePage from "./pages/ContributePage";
import keycloak from "./keycloak";
import "./App.css";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [keycloakInitialized, setKeycloakInitialized] = useState(false);
  const [selectedPost, setSelectedPost] = useState<any | null>(null);

  useEffect(() => {
    keycloak
      .init({
        onLoad: "check-sso",
        checkLoginIframe: false,
      })
      .then((authenticated) => {
        setIsLoggedIn(authenticated);
        setKeycloakInitialized(true);

        keycloak.onAuthSuccess = () => {
          setIsLoggedIn(true);
        };

        keycloak.onAuthLogout = () => {
          setIsLoggedIn(false);
        };
      })
      .catch((error) => {
        console.error("Keycloak initialization failed:", error);
        setKeycloakInitialized(true);
      });
  }, []);

  if (!keycloakInitialized) {
    return <div>Loading...</div>;
  }

  return (
    <div className="App">
      <Navbar isLoggedIn={isLoggedIn} />
      <Routes>
        <Route path="/" element={<HomePage isLoggedIn={isLoggedIn} selectedPost={selectedPost} setSelectedPost={setSelectedPost} />} />
        <Route
          path="/login"
          element={<LogInPage setIsLoggedIn={setIsLoggedIn} />}
        />
        <Route path="/mission" element={<MissionPage />} />
        <Route
          path="/my-account"
          element={<MyAccountPage setIsLoggedIn={setIsLoggedIn} selectedPost={selectedPost} setSelectedPost={setSelectedPost} />}
        />
        <Route path="/contribute" element={<ContributePage />} />
      </Routes>
    </div>
  );
}

export default App;
