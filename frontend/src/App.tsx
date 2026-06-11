import {useEffect, useState} from "react";
import {Route, Routes} from "react-router-dom";
import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import MissionPage from "./pages/MissionPage";
import LogInPage from "./pages/LogInPage";
import MyAccountPage from "./pages/MyAccountPage";
import ContributePage from "./pages/ContributePage";
import keycloak from "./keycloak";
import "./App.css";
import axios from "axios";
import Post from "./components/Post.tsx";
import AdminPanel from "./pages/AdminPanel.tsx";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [keycloakInitialized, setKeycloakInitialized] = useState(false);
  const [selectedPost, setSelectedPost] = useState<any | null>(null);
  const [savedPhotos, setSavedPhotos] = useState<Map<string, any>>(new Map());
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [savingPhoto, setSavingPhoto] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const handleSavePhoto = async (img: any) => {
    if (!keycloak.token) return;

    setSavingPhoto(img.image_url);

    const handleSuccessfulSave = (response: any) => {
        const savedPhoto = {
            ...img,
            id: response.data.id
        };
        setSavedPhotos((prev) => {
            const newMap = new Map();

            newMap.set(img.source_url, savedPhoto);

            prev.forEach((value, key) => {
                 newMap.set(key, value)
            });
            return newMap;
        });
    }

    await axios.post(
        "/api/user/photos",
        {
          provider: img.provider,
          author: img.author,
          description: img.description,
          image_url: img.image_url,
          source_url: img.source_url,
          keywords: img.keywords,
        },
        {
          headers: { Authorization: `Bearer ${keycloak.token}` },
        })
        .then((response) => {
            handleSuccessfulSave(response);
        })
        .catch((err) => {
          if (err.response?.status === 409) {
              handleSuccessfulSave(err)
          } else {
            console.error("Failed to save photo:", err);
            throw new Error("Failed to save photo");
          }
        })
        .finally(() => {
          setSavingPhoto(null);
        });
  };

  const handleDeletePhoto = async (img: any) => {
    if (!keycloak.token) return;

    const photoId: string = savedPhotos.get(img.source_url)?.id;

    if (!photoId) {
        console.error("Photo ID not found for source URL:", img.source_url);
        throw new Error("Photo ID not found");
    }

    setDeletingId(photoId);
    await axios.delete(`/api/user/photos/${photoId}`, {
      headers: { Authorization: `Bearer ${keycloak.token}` },
    })
        .then(() => {
          setSavedPhotos((prev) => {
              const updated = new Map(prev);
              updated.delete(img.source_url);
              return updated;
          });
        })
        .catch((err) => {
          console.error("Failed to delete photo:", err);
          throw new Error("Failed to delete photo");
        })
        .finally(() => setDeletingId(null));
  };

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

  useEffect(() => {
    if (keycloak.authenticated && keycloak.token) {
      setLoading(true);
      axios
          .get("/api/user/photos", {
            headers: {Authorization: `Bearer ${keycloak.token}`},
          })
          .then((response) => {
            setSavedPhotos(new Map(response.data.map((p: any) => [p.source_url, p])));
          })
          .catch((err) => {
            console.error("Failed to load saved photos:", err);
          })
          .finally(()=> setLoading(false));
    }
  }, [isLoggedIn]);

  if (!keycloakInitialized) {
    return <div>Loading...</div>;
  }

  return (
    <div className="App">
      <Navbar isLoggedIn={isLoggedIn} />
      <Routes>
        <Route path="/" element={
          <HomePage
              isLoggedIn={isLoggedIn}
              setSelectedPost={setSelectedPost}
              savingPhoto={savingPhoto}
              handleSavePhoto={handleSavePhoto}
              savedPhotos={savedPhotos}
              results={results}
              setResults={setResults}
          />} />
        <Route
          path="/login"
          element={<LogInPage setIsLoggedIn={setIsLoggedIn} />}
        />
        <Route path="/mission" element={<MissionPage />} />
        <Route
          path="/my-account"
          element={<MyAccountPage
              setIsLoggedIn={setIsLoggedIn}
              setSelectedPost={setSelectedPost}
              handleDeletePhoto={handleDeletePhoto}
              deletingId={deletingId}
              loading={loading}
              savedPhotos={[...savedPhotos.values()]}
          />}
        />
        <Route path="/contribute" element={<ContributePage />} />

          <Route path={"/admin"} element={<AdminPanel setIsLoggedIn={setIsLoggedIn}/>} />
      </Routes>
      {selectedPost && (
          <Post
              img={selectedPost}
              onClose={() => setSelectedPost(null)}
              isLoggedIn={isLoggedIn}
              savedPhotos={savedPhotos}
              savingPhoto={savingPhoto}
              handleSavePhoto={handleSavePhoto}
              handleDeletePhoto={handleDeletePhoto}
              results={results}
              setResults={setResults}
          />
      )}
    </div>
  );
}

export default App;
