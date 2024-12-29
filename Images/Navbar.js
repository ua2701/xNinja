// components/Navbar.js
import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="bg-gray-800 p-4">
      <div className="container mx-auto flex justify-between items-center">
        <div className="text-white font-bold">
          <h1>OKTA SPA Demo</h1>
        </div>
        <div className="space-x-4">
          <Link to="/" className="text-white hover:text-gray-300">
            Home
          </Link>
          <br></br>
          <Link to="/login" className="text-white hover:text-gray-300">
            Login
          </Link>
          <br></br>
          <Link to="/protected" className="text-white hover:text-gray-300">
            Protected
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;