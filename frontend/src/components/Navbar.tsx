import { NavLink } from "react-router-dom";
import "./Navbar.css";

interface NavbarProps {
  isLoggedIn: boolean;
}

const Navbar = ({ isLoggedIn }: NavbarProps) => {
  return (
    <header className="header">
      <div className="logo">PHOTO-SEARCH</div>
      <nav>
        <ul>
          <li>
            <NavLink to="/">Home</NavLink>
          </li>
          {isLoggedIn ? (
            <li>
              <NavLink to="/my-account">My Account</NavLink>
            </li>
          ) : (
            <li>
              <NavLink to="/login">Log-In</NavLink>
            </li>
          )}
          <li>
            <NavLink to="/mission">Our mission</NavLink>
          </li>
          <li>
            <NavLink to="/contribute">Contribute Data</NavLink>
          </li>
        </ul>
      </nav>
    </header>
  );
};

export default Navbar;
