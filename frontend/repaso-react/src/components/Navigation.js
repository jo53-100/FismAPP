// src/components/Navigation.js
import React from 'react';

const Navigation = ({ activeTab, setActiveTab, userType }) => {
  const tabs = ['home', 'courses', 'assignments'];

  // Add certificates tab for professors
  if (userType === 'professor') {
    tabs.push('certificates');
  }

  const tabLabels = {
    home: 'Inicio',
    courses: 'Cursos',
    assignments: 'Tareas',
    certificates: 'Certificados'
  };

  return (
    <nav style={{ backgroundColor: 'white', padding: '8px' }}>
      <div style={{ display: 'flex', gap: '16px' }}>
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '8px 16px',
              backgroundColor: activeTab === tab ? '#f3f4f6' : 'transparent',
              border: 'none',
              borderBottom: activeTab === tab ? '2px solid #1d4ed8' : 'none',
              color: activeTab === tab ? '#1d4ed8' : '#6b7280',
              cursor: 'pointer'
            }}
          >
            {tabLabels[tab]}
          </button>
        ))}
      </div>
    </nav>
  );
};

export default Navigation;