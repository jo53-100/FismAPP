const CertificateAdminPanel = () => {
  const [templates, setTemplates] = useState([]);
  const [professors, setProfessors] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedProfessors, setSelectedProfessors] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch certificate templates
        const templatesResponse = await fetch('/api/v1/certificate-templates/');
        const templatesData = await templatesResponse.json();
        setTemplates(templatesData);

        // Fetch professors
        const professorsResponse = await fetch('/api/v1/professors/');
        const professorsData = await professorsResponse.json();
        setProfessors(professorsData);

        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleBulkGenerate = async (e) => {
    e.preventDefault();

    if (!selectedTemplate || selectedProfessors.length === 0) {
      alert('Por favor selecciona una plantilla y al menos un profesor');
      return;
    }

    setIsGenerating(true);
    setResult(null);

    try {
      const response = await fetch('/api/v1/certificates/bulk-generate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template_id: selectedTemplate,
          professor_ids: selectedProfessors,
          destinatario: 'A QUIEN CORRESPONDA',
          incluir_qr: true
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error generating certificates:', error);
      setResult({ error: 'Ha ocurrido un error al generar los certificados' });
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  return (
    <div>
      <h2>Administración de Certificados</h2>

      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
        <div style={{ flex: 1 }}>
          <h3>Plantillas de Certificados</h3>
          <ul>
            {templates.map(template => (
              <li key={template.id}>
                <h4>{template.name}</h4>
                <p>{template.description}</p>
                <button
                  onClick={() => window.location.href = `/admin/certificates/certificatetemplate/${template.id}/change/`}
                  style={{
                    backgroundColor: '#1d4ed8',
                    color: 'white',
                    padding: '6px 12px',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    marginRight: '10px',
                    fontSize: '14px'
                  }}
                >
                  Editar
                </button>
              </li>
            ))}
          </ul>
          <button
            onClick={() => window.location.href = '/admin/certificates/certificatetemplate/add/'}
            style={{
              backgroundColor: '#10b981',
              color: 'white',
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
          >
            Nueva Plantilla
          </button>
        </div>

        <div style={{ flex: 1 }}>
          <h3>Generación de Certificados por Lote</h3>
          <form onSubmit={handleBulkGenerate}>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Plantilla:</label>
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
              <label style={{ display: 'block', marginBottom: '5px' }}>Profesores:</label>
              <select
                multiple
                value={selectedProfessors}
                onChange={(e) => setSelectedProfessors(Array.from(e.target.selectedOptions, option => option.value))}
                style={{ width: '100%', padding: '8px', height: '150px' }}
              >
                {professors.map(professor => (
                  <option key={professor.id} value={professor.id}>
                    {professor.first_name} {professor.last_name}
                  </option>
                ))}
              </select>
              <small>Mantén presionado Ctrl para seleccionar múltiples profesores</small>
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
              {isGenerating ? 'Generando...' : 'Generar Certificados'}
            </button>
          </form>

          {result && (
            <div style={{ marginTop: '20px' }}>
              <h4>Resultado:</h4>
              {result.error ? (
                <p style={{ color: 'red' }}>{result.error}</p>
              ) : (
                <>
                  <p style={{ color: '#10b981' }}>
                    Se generaron {result.generated} certificados exitosamente
                  </p>
                  {result.errors && result.errors.length > 0 && (
                    <>
                      <p style={{ color: 'red' }}>
                        Errores ({result.errors.length}):
                      </p>
                      <ul>
                        {result.errors.map((error, index) => (
                          <li key={index} style={{ color: 'red' }}>
                            Profesor ID {error.professor_id}: {error.error}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      <h3>Importar Historial de Cursos</h3>
      <div style={{ marginBottom: '15px' }}>
        <input type="file" accept=".xlsx, .xls" />
        <button
          style={{
            backgroundColor: '#1d4ed8',
            color: 'white',
            padding: '8px 16px',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginLeft: '10px'
          }}
        >
          Importar Excel
        </button>
      </div>
    </div>
  );
};