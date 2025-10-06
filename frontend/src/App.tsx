import React from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ListaChamados from './pages/ListaChamados';
import DetalhesChamado from './pages/DetalhesChamado';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <div className="app-container">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/chamados" element={<ListaChamados />} />
              <Route path="/chamados/:id" element={<DetalhesChamado />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;