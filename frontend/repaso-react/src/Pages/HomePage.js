// src/components/HomePage.js
import React from 'react';

const HomePage = ({ userData, courses, assignments }) => {
  return (
    <div>
      <h2>Bienvenido(a), {userData?.name}</h2>
      <p>Matrícula: {userData?.studentId}</p>
      <p>Programa: {userData?.program}</p>

      <h3 style={{ marginTop: '20px' }}>Próximas tareas</h3>
      <ul>
        {assignments.map(assignment => {
          const course = courses.find(c => c.id === assignment.courseId);
          return (
            <li key={assignment.id}>
              {assignment.title} - {course?.name} - Fecha límite: {assignment.dueDate}
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default HomePage;