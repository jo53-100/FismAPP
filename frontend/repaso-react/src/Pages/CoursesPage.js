// src/components/CoursesPage.js
import React from 'react';

const CoursesPage = ({ courses }) => {
  return (
    <div>
      <h2>Mis Cursos</h2>
      <ul>
        {courses.map(course => (
          <li key={course.id}>
            <h3>{course.name} ({course.code})</h3>
            <p>Profesor: {course.professor}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default CoursesPage;