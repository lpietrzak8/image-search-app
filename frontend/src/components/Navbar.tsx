import { useState } from "react";
import { NavLink } from "react-router-dom";
import "./Navbar.css";

interface NavbarProps {
  isLoggedIn: boolean;
}

const Navbar = ({ isLoggedIn }: NavbarProps) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <>
      <header className="header">
        <div className="logo">PHOTO-SEARCH</div>

        <button
          className={`hamburger ${isMenuOpen ? "active" : ""}`}
          onClick={toggleMenu}
          aria-label="Toggle menu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <nav className={isMenuOpen ? "active" : ""}>
          <ul>
            <li>
              <NavLink to="/" onClick={closeMenu}>
                Home
              </NavLink>
            </li>
            {isLoggedIn ? (
              <li>
                <NavLink to="/my-account" onClick={closeMenu}>
                  My Account
                </NavLink>
              </li>
            ) : (
              <li>
                <NavLink to="/login" onClick={closeMenu}>
                  Log-In
                </NavLink>
              </li>
            )}
            <li>
              <NavLink to="/mission" onClick={closeMenu}>
                Our mission
              </NavLink>
            </li>
            <li>
              <NavLink to="/contribute" onClick={closeMenu}>
                Contribute Data
              </NavLink>
            </li>
          </ul>
        </nav>
      </header>

      {isMenuOpen && <div className="menu-overlay" onClick={closeMenu}></div>}
    </>
  );
};

export default Navbar;
