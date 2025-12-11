import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import type { Dispatch, SetStateAction } from "react";
import keycloak from "../keycloak";
import "./MyAccountPage.css";

interface MyAccountPageProps {
  setIsLoggedIn: Dispatch<SetStateAction<boolean>>;
}

const MyAccountPage = ({ setIsLoggedIn }: MyAccountPageProps) => {
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
      <h1>My Account</h1>
      <div className="tabs">
        <button
          className={`tab-button ${activeTab === "resources" ? "active" : ""}`}
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
          <div>
            <p>Your resources will be displayed here.</p>
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
  );
};

export default MyAccountPage;
