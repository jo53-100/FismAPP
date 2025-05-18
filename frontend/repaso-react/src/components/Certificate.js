// src/components/Certificate.js
import React, { useState, useEffect } from 'react';

const CertificatesPage = ({ professorId }) => {
  const [certificates, setCertificates] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Mock fetch certificates for now
    setTimeout(() => {
      setCertificates([
        {
          id: 1,
          verification_code: '7a8b9c0d1e2f3g4h',
          generated_at: '2025-05-01T10:00:00Z',
          template: { id: 1, name: 'Constancia de Docencia' }
        },
        {
          id: 2,
          verification_code: '5i6j7k8l9m0n1o2p',
          generated_at: '2025-04-15T14:30:00Z',
          template: { id: 2, name: 'Constancia de Participación en Eventos' }
        }
      ]);

      setTemplates([
        { id: 1, name: 'Constancia de Docencia' },
        { id: 2, name: 'Constancia de Participación en Eventos' },
        { id: 3, name: 'Reconocimiento Académico' }
      ]);

      setIsLoading(false);
    }, 1000);

    // Later replace with actual API call
    // const fetchCertificates = async () => {
    //   try {
    //     const response = await fetch(`/api/v1/certificates/?professor=${professorId}`);
    //     const data = await response.json();
    //     setCertificates(data);
    //
    //     const templatesResponse = await fetch('/api/v1/certificate-templates/');
    //     const templatesData = await templatesResponse.json();
    //     setTemplates(templatesData);
    //
    //     setIsLoading(false);
    //   } catch (error) {
    //     console.error('Error fetching certificates:', error);
    //     setIsLoading(false);
    //   }
    // };
    // fetchCertificates();
  }, [professorId]);

  if (isLoading) {
    return <div>Cargando certificados...</div>;
  }

  return (
    <div>
      <h2>Mis Certificados</h2>
      {certificates.length === 0 ? (
        <p>No tienes certificados generados.</p>
      ) : (
        <ul style={{ listStyleType: 'none', padding: 0 }}>
          {certificates.map(certificate => (
            <li key={certificate.id} style={{
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '15px',
              marginBottom: '15px',
              backgroundColor: '#f9fafb'
            }}>
              <h3>Certificado #{certificate.verification_code.slice(0, 8)}</h3>
              <p>Generado: {new Date(certificate.generated_at).toLocaleDateString()}</p>
              <p>Template: {certificate.template.name}</p>
              <button
                onClick={() => alert('Descargando certificado...')}
                style={{
                  backgroundColor: '#1d4ed8',
                  color: 'white',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}
              >
                Descargar PDF
              </button>
            </li>
          ))}
        </ul>
      )}

      <h3 style={{ marginTop: '30px' }}>Generar Nuevo Certificado</h3>
      <GenerateCertificateForm
        templates={templates}
        professorId={professorId}
        onCertificateGenerated={() => alert('¡Certificado generado exitosamente!')}
      />
    </div>
  );
};

const GenerateCertificateForm = ({ templates, professorId, onCertificateGenerated }) => {
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [periodos, setPeriodos] = useState(['202510', '202535', '202430', '202425']);
  const [selectedPeriodos, setSelectedPeriodos] = useState([]);
  const [periodoActual, setPeriodoActual] = useState('');

  const handleGenerateCertificate = async (e) => {
    e.preventDefault();

    if (!selectedTemplate) {
      setError('Por favor selecciona una plantilla');
      return;
    }

    setIsGenerating(true);
    setError(null);

    // Simulate API call with timeout
    setTimeout(() => {
      setIsGenerating(false);
      onCertificateGenerated();
    }, 2000);
  };

  return (
    <form onSubmit={handleGenerateCertificate}>
      {error && <p style={{ color: 'red' }}>{error}</p>}

      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>Plantilla de Certificado:</label>
        <select
          value={selectedTemplate}
          onChange={(e) => setSelectedTemplate(e.target.value)}
          style={{ width: '100%', padding: '8px' }}
        >
          <option value="">Selecciona una plantilla</option>
          {templates.map(template => (
            <option key={template.id} value={template.id}>{template.name}</option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>Periodos a incluir:</label>
        <select
          multiple
          value={selectedPeriodos}
          onChange={(e) => setSelectedPeriodos(Array.from(e.target.selectedOptions, option => option.value))}
          style={{ width: '100%', padding: '8px', height: '100px' }}
        >
          {periodos.map(periodo => (
            <option key={periodo} value={periodo}>{periodo}</option>
          ))}
        </select>
        <small>Mantén presionado Ctrl para seleccionar múltiples periodos</small>
      </div>

      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>Periodo Actual (opcional):</label>
        <select
          value={periodoActual}
          onChange={(e) => setPeriodoActual(e.target.value)}
          style={{ width: '100%', padding: '8px' }}
        >
          <option value="">Ninguno</option>
          {periodos.map(periodo => (
            <option key={periodo} value={periodo}>{periodo}</option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={isGenerating}
        style={{
          backgroundColor: isGenerating ? '#9ca3af' : '#1d4ed8',
          color: 'white',
          padding: '8px 16px',
          border: 'none',
          borderRadius: '4px',
          cursor: isGenerating ? 'not-allowed' : 'pointer'
        }}
      >
        {isGenerating ? 'Generando...' : 'Generar Certificado'}
      </button>
    </form>
  );
};

export default CertificatesPage;