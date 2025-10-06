import React from 'react';

const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <ul className="nav-list">
          <li>
            <a href="/" className="nav-link">
              📊 Dashboard
            </a>
          </li>
          <li>
            <a href="/chamados" className="nav-link">
              📋 Chamados
            </a>
          </li>
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;