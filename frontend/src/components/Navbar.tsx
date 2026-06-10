import {useEffect, useState} from "react";
import {Link, NavLink} from "react-router-dom";
import "./Navbar.css";
import keycloak from "../keycloak.ts";

interface NavbarProps {
  isLoggedIn: boolean;
}

const Navbar = ({ isLoggedIn }: NavbarProps) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const roles = keycloak.tokenParsed?.realm_access?.roles || [];
    if(roles.includes("admin")) {
      setIsAdmin(true)
    } else {
      setIsAdmin(false)
    }
  }, [isLoggedIn])

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <>
      <header className="header">
        <Link to={"/"}><div className="logo">PHOTO-SEARCH</div></Link>

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
            {isAdmin && (
                <li>
                 <NavLink to="/admin" onClick={closeMenu}>
                   Admin Panel
                 </NavLink>
                </li>
            )}
          </ul>
        </nav>
      </header>

      {isMenuOpen && <div className="menu-overlay" onClick={closeMenu}></div>}
    </>
  );
};

export default Navbar;
