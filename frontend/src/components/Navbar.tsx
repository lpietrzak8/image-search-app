import { NavLink } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
  return (
    <header className="header">
      <div className="logo">PHOTO-SEARCH</div>
      <nav>
        <ul>
          <li><NavLink to="/">Home</NavLink></li>
          <li><NavLink to="/login">Log-In</NavLink></li>
          <li><NavLink to="/mission">Our mission</NavLink></li>
        </ul>
      </nav>
    </header>
  );
};

export default Navbar;
