import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import type { Dispatch, SetStateAction } from "react";
import keycloak from "../keycloak";
import "./MyAccountPage.css";

interface SavedPhoto {
  id: string;
  author: any;
  image_url: string;
  source_url: string;
  description: string | null;
  provider: string | null;
  created_at: any;
}

interface MyAccountPageProps {
  setIsLoggedIn: Dispatch<SetStateAction<boolean>>;
  setSelectedPost: any;
  handleDeletePhoto: (img: any) => void;
  deletingId: string | null;
  loading: boolean;
  savedPhotos: SavedPhoto[];
}

const MyAccountPage = ({
                         setIsLoggedIn, setSelectedPost, handleDeletePhoto, deletingId, loading, savedPhotos }: MyAccountPageProps) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("resources");

  useEffect(() => {
    if (!keycloak.authenticated) {
      navigate("/login");
    }
  }, [navigate]);

  const handleLogout = () => {
    keycloak.logout({
      redirectUri: window.location.origin + "/",
    });
    setIsLoggedIn(false);
  };

  const user = {
    username: keycloak.tokenParsed?.preferred_username || "User",
    email: keycloak.tokenParsed?.email || "No email",
  };

  return (
    <div className="my-account-container">
      <div className="my-account-content">
        <h1>My Account</h1>
        <div className="tabs">
          <button
            className={`tab-button ${
              activeTab === "resources" ? "active" : ""
            }`}
            onClick={() => setActiveTab("resources")}
          >
            My Resources
          </button>
          <button
            className={`tab-button ${activeTab === "info" ? "active" : ""}`}
            onClick={() => setActiveTab("info")}
          >
            Account Information
          </button>
          <button
            className={`tab-button ${activeTab === "logout" ? "active" : ""}`}
            onClick={() => setActiveTab("logout")}
          >
            Log Out
          </button>
        </div>

        <div className="tab-content">
          {activeTab === "info" && (
            <div className="user-info">
              <p>
                <strong>Username:</strong> {user.username}
              </p>
              <p>
                <strong>Email:</strong> {user.email}
              </p>
            </div>
          )}
          {activeTab === "resources" && (
            <div className="resources-container">
              {loading && <p>Loading your saved photos...</p>}
              {!loading && savedPhotos.length === 0 && (
                <p>You haven't saved any photos yet. Search for photos and click the + button to save them here.</p>
              )}
              {!loading && savedPhotos.length > 0 && (
                <div className="saved-photos-grid">
                  {savedPhotos.map((photo) => (
                    <div key={photo.id} className="saved-photo-card">
                      <img
                          src={photo.image_url}
                          alt={photo.description || "Saved photo"}
                          onClick={() => setSelectedPost(photo)}
                      />
                      <button
                        className="remove-btn"
                        onClick={() => handleDeletePhoto(photo)}
                        disabled={deletingId === photo.id}
                        title="Remove from saved"
                      >
                        {deletingId === photo.id ? "..." : "×"}
                      </button>
                      <a
                        className="download-btn"
                        href={photo.image_url}
                        download
                        title="Download image"
                      >
                        ⬇
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {activeTab === "logout" && (
            <div>
              <p>Are you sure you want to log out?</p>
              <button onClick={handleLogout} className="logout-button">
                Yes, Log Out
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MyAccountPage;
