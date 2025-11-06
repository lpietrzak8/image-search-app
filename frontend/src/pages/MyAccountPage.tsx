import { useNavigate } from 'react-router-dom';
import type { Dispatch, SetStateAction } from 'react';

interface MyAccountPageProps {
  setIsLoggedIn: Dispatch<SetStateAction<boolean>>;
}

const MyAccountPage = ({ setIsLoggedIn }: MyAccountPageProps) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    setIsLoggedIn(false);
    navigate('/');
  };

  return (
    <div>
      <h1>My Account</h1>
      <p>Welcome to your profile!</p>
      <button onClick={handleLogout}>Log Out</button>
    </div>
  );
};

export default MyAccountPage;
