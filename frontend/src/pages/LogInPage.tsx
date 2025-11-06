import { useNavigate } from 'react-router-dom';
import type { Dispatch, SetStateAction } from 'react';
import "./LogInPage.css";

interface LogInPageProps {
  setIsLoggedIn: Dispatch<SetStateAction<boolean>>;
}

const LogInPage = ({ setIsLoggedIn }: LogInPageProps) => {
  const navigate = useNavigate();

  const handleLogin = () => {
    setIsLoggedIn(true);
    navigate('/');
  };

  return (
    <div className="login-page-container">
      <div className="login-box">
        <h2>Welcome to Photo-Search</h2>
        <p>Please log in to continue</p>
        <button className="auth-button" onClick={handleLogin}>
          Login
        </button>
        <button className="auth-button">Register</button>
      </div>
    </div>
  );
};

export default LogInPage;
