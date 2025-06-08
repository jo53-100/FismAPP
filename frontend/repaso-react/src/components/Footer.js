// src/components/Footer.js
import React from 'react';

const Footer = () => {
  return (
    <footer style={{ backgroundColor: 'white', boxShadow: '0 -2px 4px rgba(0, 0, 0, 0.05)', padding: '16px' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 16px', display: 'flex', justifyContent: 'space-between', color: '#4b5563', fontSize: '14px' }}>
        <div>
          FismAPP &copy; 2025 - Facultad de Ciencias Físico Matemáticas
        </div>
        <div style={{ display: 'flex', gap: '16px' }}>
          <a href="#" style={{ color: '#4b5563', textDecoration: 'none' }}>Contacto</a>
          <a href="#" style={{ color: '#4b5563', textDecoration: 'none' }}>Ayuda</a>
          <a href="#" style={{ color: '#4b5563', textDecoration: 'none' }}>Privacidad</a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;