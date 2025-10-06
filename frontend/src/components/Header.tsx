import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-container">
        <h1 className="header-title">WEX Intelligence</h1>
        <nav className="header-nav">
          <span className="user-info">Sistema de Triagem Automática</span>
        </nav>
      </div>
    </header>
  );
};

export default Header;