// src/services/api.js
export const fetchUserData = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        name: 'Regina Olvera',
        studentId: '202450528',
        program: 'Física teórica'
      });
    }, 1000);
  });
};

export const fetchCourses = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { id: 101, code: 'MAT2050', name: 'Cálculo Vectorial', professor: 'Dr. Carlos Méndez' },
        { id: 102, code: 'FIS3040', name: 'Física Moderna', professor: 'Dra. Elena Fuentes' },
        { id: 103, code: 'COM2030', name: 'Algoritmos Avanzados', professor: 'Dr. Roberto Sánchez' }
      ]);
    }, 1000);
  });
};

export const fetchAssignments = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { id: 201, courseId: 101, title: 'Tarea 5: Integrales', dueDate: '2025-05-25' },
        { id: 202, courseId: 103, title: 'Proyecto: Algoritmos de grafos', dueDate: '2025-05-30' }
      ]);
    }, 1000);
  });
};

export const formatDate = (dateString) => {
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  return new Date(dateString).toLocaleDateString('es-MX', options);
};