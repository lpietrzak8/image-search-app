import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import type { Dispatch, SetStateAction } from "react";
import keycloak from "../keycloak";
import "./LogInPage.css";

interface LogInPageProps {
  setIsLoggedIn: Dispatch<SetStateAction<boolean>>;
}

const LogInPage = ({ setIsLoggedIn }: LogInPageProps) => {
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      if (keycloak.authenticated) {
        setIsLoggedIn(true);
        setTimeout(() => {
          navigate("/");
        }, 100);
      }
    };
    checkAuth();
  }, [keycloak.authenticated, setIsLoggedIn, navigate]);

  const handleLogin = () => {
    keycloak.login({
      redirectUri: window.location.origin + "/login",
    });
  };

  const handleRegister = () => {
    keycloak.register({
      redirectUri: window.location.origin + "/login",
    });
  };

  return (
    <div className="login-page-container">
      <div className="login-box">
        <h2>Welcome to Photo-Search</h2>
        <p>Please log in to continue</p>
        <button className="auth-button" onClick={handleLogin}>
          Login
        </button>
        <button className="auth-button" onClick={handleRegister}>
          Register
        </button>
      </div>
    </div>
  );
};

export default LogInPage;
