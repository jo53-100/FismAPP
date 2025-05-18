// src/components/Header.js
import React, { useState } from 'react';
import fcfmLogo from '../Images/fcfm.jpeg'; // Adjust the path as needed

const Header = ({ userData, onOptionsClick, options = ['Subir historial académico', 'Consultar becas', 'Ver anuncios', 'Solicitar laboratorios'] }) => {
  const [showOptions, setShowOptions] = useState(false);
  const [activeTab, setActiveTab] = useState('Inicio');

  return (
    <div>
      {/* Blue app header with navigation */}
      <div style={{
        backgroundColor: '#1d4ed8',
        color: 'white',
        padding: '12px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {/* Logo */}
          <img
            src={fcfmLogo}
            alt="FCFM Logo"
            style={{
              height: '40px',
              marginRight: '15px',
              borderRadius: '4px'
            }}
          />

          <h1 style={{
            margin: 0,
            fontSize: '24px',
            fontWeight: 'bold',
            marginRight: '30px'
          }}>
            FismAPP
          </h1>

          <div style={{ display: 'flex', gap: '20px' }}>
            <a
              href="#inicio"
              style={{
                color: 'white',
                textDecoration: 'none'
              }}
            >
              Inicio
            </a>
            <a
              href="#anuncios"
              style={{
                color: 'white',
                textDecoration: 'none'
              }}
            >
              Anuncios
            </a>
            <a
              href="#contacto"
              style={{
                color: 'white',
                textDecoration: 'none'
              }}
            >
              Contacto
            </a>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowOptions(!showOptions)}
              style={{
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                padding: '8px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              Opciones ▼
            </button>

            {showOptions && (
              <div style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                backgroundColor: 'white',
                boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
                borderRadius: '4px',
                width: '200px',
                zIndex: 10
              }}>
                {options.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      onOptionsClick(option);
                      setShowOptions(false);
                    }}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      padding: '10px 15px',
                      backgroundColor: 'transparent',
                      border: 'none',
                      borderBottom: index < options.length - 1 ? '1px solid #eee' : 'none',
                      cursor: 'pointer',
                      color: '#333'
                    }}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>Regina Olvera</span>
            <div style={{
              width: '28px',
              height: '28px',
              backgroundColor: '#fff',
              color: '#1d4ed8',
              borderRadius: '50%',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontWeight: 'bold',
              fontSize: '14px'
            }}>
              R
            </div>
          </div>
        </div>
      </div>

      {/* Only one set of sub-navigation tabs */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <div style={{
          display: 'flex',
          padding: '0 20px'
        }}>
          {['Inicio', 'Cursos', 'Tareas', 'Certificados'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '12px 16px',
                backgroundColor: 'transparent',
                border: 'none',
                borderBottom: activeTab === tab ? '2px solid #1d4ed8' : 'none',
                color: activeTab === tab ? '#1d4ed8' : '#6b7280',
                fontWeight: activeTab === tab ? 'medium' : 'normal',
                cursor: 'pointer'
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Header;