// src/components/pages/CalendarPage.js
import React from 'react';

const CalendarPage = ({ courses, assignments }) => {
  // Simple placeholder for the Calendar page
  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px' }}>Calendario</h2>
      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)', padding: '24px', textAlign: 'center' }}>
        <p style={{ marginBottom: '16px' }}>Calendario de cursos y entregas</p>
        <p style={{ color: '#6b7280' }}>Próximamente: Vista detallada del calendario</p>
      </div>
    </div>
  );
};

export default CalendarPage;