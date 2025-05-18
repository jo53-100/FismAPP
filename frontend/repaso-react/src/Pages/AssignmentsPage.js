// src/components/AssignmentsPage.js
import React from 'react';

const AssignmentsPage = ({ courses, assignments }) => {
  return (
    <div>
      <h2>Tareas y Proyectos</h2>
      <ul>
        {assignments.map(assignment => {
          const course = courses.find(c => c.id === assignment.courseId);
          return (
            <li key={assignment.id}>
              <h3>{assignment.title}</h3>
              <p>Curso: {course?.name}</p>
              <p>Fecha límite: {assignment.dueDate}</p>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default AssignmentsPage;