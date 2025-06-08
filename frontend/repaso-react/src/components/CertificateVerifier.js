// src/components/CertificateVerifier.js
import React, { useState } from 'react';

const CertificateVerifier = () => {
  const [verificationCode, setVerificationCode] = useState('');
  const [verificationResult, setVerificationResult] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);

  const handleVerifyCertificate = async (e) => {
    e.preventDefault();

    if (!verificationCode.trim()) {
      return;
    }

    setIsVerifying(true);
    setVerificationResult(null);

    // Simulate API verification
    setTimeout(() => {
      if (verificationCode.startsWith('7a') || verificationCode.startsWith('5i')) {
        // Example of valid certificate
        setVerificationResult({
          valid: true,
          certificate: {
            professor: {
              first_name: 'Juan',
              last_name: 'Pérez'
            },
            generated_at: '2025-05-01T10:00:00Z'
          }
        });
      } else {
        // Example of invalid certificate
        setVerificationResult({
          valid: false,
          message: 'El código de verificación no es válido o no existe'
        });
      }
      setIsVerifying(false);
    }, 1500);
  };

  return (
    <div>
      <form onSubmit={handleVerifyCertificate}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>Código de Verificación:</label>
          <input
            type="text"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value)}
            style={{ width: '100%', padding: '8px' }}
            placeholder="Ingresa el código de verificación"
          />
        </div>

        <button
          type="submit"
          disabled={isVerifying}
          style={{
            backgroundColor: isVerifying ? '#9ca3af' : '#1d4ed8',
            color: 'white',
            padding: '8px 16px',
            border: 'none',
            borderRadius: '4px',
            cursor: isVerifying ? 'not-allowed' : 'pointer'
          }}
        >
          {isVerifying ? 'Verificando...' : 'Verificar Certificado'}
        </button>
      </form>

      {verificationResult && (
        <div style={{
          marginTop: '20px',
          padding: '15px',
          backgroundColor: verificationResult.valid ? '#ecfdf5' : '#fef2f2',
          borderRadius: '4px',
          borderLeft: `4px solid ${verificationResult.valid ? '#10b981' : '#ef4444'}`
        }}>
          {verificationResult.valid ? (
            <>
              <h3 style={{ color: '#10b981', marginTop: 0 }}>Certificado Válido</h3>
              <p>Profesor: {verificationResult.certificate.professor.first_name} {verificationResult.certificate.professor.last_name}</p>
              <p>Generado: {new Date(verificationResult.certificate.generated_at).toLocaleDateString()}</p>
            </>
          ) : (
            <>
              <h3 style={{ color: '#ef4444', marginTop: 0 }}>Certificado No Válido</h3>
              <p>{verificationResult.message}</p>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default CertificateVerifier;