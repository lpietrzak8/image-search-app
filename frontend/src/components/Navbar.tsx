import React from 'react';
import './Navbar.css';

interface NavbarProps {
  activePage: string;
  setActivePage: (page: string) => void;
}

const Navbar: React.FC<NavbarProps> = ({ activePage, setActivePage }) => {
  return (
    <header className="header">
      <div className="logo">PHOTO-SEARCH</div>
      <nav>
        <ul>
          <li><a href="#" className={activePage === 'Home' ? 'active' : ''} onClick={() => setActivePage('Home')}>Home</a></li>
          <li><a href="#" className={activePage === 'Log-In' ? 'active' : ''} onClick={() => setActivePage('Log-In')}>Log-In</a></li>
          <li><a href="#" className={activePage === 'Our mission' ? 'active' : ''} onClick={() => setActivePage('Our mission')}>Our mission</a></li>
        </ul>
      </nav>
    </header>
  );
};

export default Navbar;
