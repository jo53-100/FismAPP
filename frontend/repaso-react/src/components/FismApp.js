// src/components/FismApp.js
import React, { useState, useEffect } from 'react';

const FismApp = () => {
  const [activeTab, setActiveTab] = useState('home');
  const [isLoading, setIsLoading] = useState(false);
  const [userData, setUserData] = useState({
    name: 'Regina Olvera',
    studentId: '202450528',
    program: 'Física teórica'
  });
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [showOptions, setShowOptions] = useState(false);

  // Options click handler
  const handleOptionsClick = (option) => {
    console.log("Option clicked:", option);
    // Handle different options here
  };

  return (
    <div>
      {/* Blue Header - WITHOUT LOGO */}
      <div style={{
        backgroundColor: '#1d4ed8',
        color: 'white',
        padding: '12px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
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
                {['Subir historial académico', 'Consultar becas', 'Ver anuncios', 'Solicitar laboratorios'].map((option, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      handleOptionsClick(option);
                      setShowOptions(false);
                    }}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      padding: '10px 15px',
                      backgroundColor: 'transparent',
                      border: 'none',
                      borderBottom: index < 3 ? '1px solid #eee' : 'none',
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
            <span>{userData.name}</span>
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

      {/* White Navigation Bar */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <div style={{
          display: 'flex',
          padding: '0 20px'
        }}>
          {['Inicio', 'Cursos', 'Tareas', 'Certificados'].map((tab) => {
            const tabValue = tab.toLowerCase();
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tabValue)}
                style={{
                  padding: '12px 16px',
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderBottom: activeTab === tabValue ? '2px solid #1d4ed8' : 'none',
                  color: activeTab === tabValue ? '#1d4ed8' : '#6b7280',
                  fontWeight: activeTab === tabValue ? 'medium' : 'normal',
                  cursor: 'pointer'
                }}
              >
                {tab}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content */}
      <main style={{ padding: '20px' }}>
        <div>
          <h2>Bienvenido(a), {userData.name}</h2>
          <p>Matrícula: {userData.studentId}</p>
          <p>Programa: {userData.program}</p>

          <h3 style={{ marginTop: '20px' }}>Próximas tareas</h3>
          <ul>
            <li>Tarea 5: Integrales - Cálculo Vectorial - Fecha límite: 2025-05-25</li>
            <li>Proyecto: Algoritmos de grafos - Algoritmos Avanzados - Fecha límite: 2025-05-30</li>
          </ul>
        </div>
      </main>
    </div>
  );
};

export default FismApp;