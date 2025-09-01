#!/usr/bin/env python3
"""
Simple test script to demonstrate the public API endpoints for certificates
Run this script to test the API without any authentication
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api/certificates"

def test_api_info():
    """Test the API info endpoint"""
    print("🔍 Testing API Info Endpoint...")
    response = requests.get(f"{BASE_URL}/api-info/")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API Info retrieved successfully!")
        print(f"📋 Message: {data['message']}")
        print(f"🔗 Available endpoints: {len(data['endpoints'])}")
        
        for name, info in data['endpoints'].items():
            print(f"  • {name}: {info['method']} {info['url']}")
            print(f"    {info['description']}")
        
        return True
    else:
        print(f"❌ Failed to get API info: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_professors_list():
    """Test the professors list endpoint"""
    print("\n👥 Testing Professors List Endpoint...")
    response = requests.get(f"{BASE_URL}/professors-public/")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Professors list retrieved successfully!")
        print(f"📊 Total professors: {data['count']}")
        
        # Show first few professors
        for prof in data['professors'][:5]:
            print(f"  • {prof['name']} (ID: {prof['id_docente']}) - {prof['course_count']} courses")
        
        if data['count'] > 5:
            print(f"  ... and {data['count'] - 5} more")
        
        return data['professors'][0]['id_docente'] if data['professors'] else None
    else:
        print(f"❌ Failed to get professors list: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_templates_list():
    """Test the templates list endpoint"""
    print("\n📄 Testing Templates List Endpoint...")
    response = requests.get(f"{BASE_URL}/templates-public/")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Templates list retrieved successfully!")
        print(f"📋 Total templates: {data['count']}")
        
        for template in data['templates']:
            default_mark = " (Default)" if template['is_default'] else ""
            print(f"  • {template['name']}{default_mark} - {template['layout_type']}")
        
        return data['templates'][0]['id'] if data['templates'] else None
    else:
        print(f"❌ Failed to get templates list: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_request_certificate(id_docente, template_id=None):
    """Test the certificate request endpoint"""
    print(f"\n📜 Testing Certificate Request Endpoint...")
    print(f"👤 Requesting certificate for professor ID: {id_docente}")
    
    # Prepare request data
    data = {
        'id_docente': id_docente,
        'destinatario': 'A QUIEN CORRESPONDA',
        'incluir_qr': True
    }
    
    if template_id:
        data['template_id'] = template_id
        print(f"📄 Using template ID: {template_id}")
    
    response = requests.post(f"{BASE_URL}/request-public/", json=data)
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Certificate generated successfully!")
        print(f"📋 Message: {data['message']}")
        
        cert_info = data['certificate']
        print(f"🔐 Verification Code: {cert_info['verification_code']}")
        print(f"👤 Professor: {cert_info['professor_name']}")
        print(f"📄 Template: {cert_info['template_name']}")
        print(f"🔗 File URL: {cert_info['file_url']}")
        print(f"🔍 Verification URL: {cert_info['verification_url']}")
        
        return cert_info['verification_code']
    else:
        print(f"❌ Failed to generate certificate: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_verify_certificate(verification_code):
    """Test the certificate verification endpoint"""
    print(f"\n🔍 Testing Certificate Verification Endpoint...")
    print(f"🔐 Verifying certificate with code: {verification_code}")
    
    response = requests.get(f"{BASE_URL}/verify-public/", params={'code': verification_code})
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Certificate verification successful!")
        print(f"📋 Message: {data['message']}")
        print(f"✅ Valid: {data['valid']}")
        
        cert_info = data['certificate']
        print(f"👤 Professor: {cert_info['professor_name']}")
        print(f"🆔 ID Docente: {cert_info['id_docente']}")
        print(f"📄 Template: {cert_info['template_name']}")
        print(f"📅 Generated: {cert_info['generated_at']}")
        
        return True
    else:
        print(f"❌ Failed to verify certificate: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting API Endpoint Tests")
    print("=" * 50)
    
    # Test 1: API Info
    if not test_api_info():
        print("❌ API Info test failed. Make sure the server is running.")
        return
    
    # Test 2: Professors List
    id_docente = test_professors_list()
    if not id_docente:
        print("❌ Professors list test failed. Cannot proceed with certificate generation.")
        return
    
    # Test 3: Templates List
    template_id = test_templates_list()
    
    # Test 4: Request Certificate
    verification_code = test_request_certificate(id_docente, template_id)
    if not verification_code:
        print("❌ Certificate request test failed.")
        return
    
    # Test 5: Verify Certificate
    test_verify_certificate(verification_code)
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\n📚 How to use these endpoints:")
    print("1. Request a certificate: POST /api/certificates/request-public/")
    print("2. Verify a certificate: GET /api/certificates/verify-public/?code=VERIFICATION_CODE")
    print("3. List professors: GET /api/certificates/professors-public/")
    print("4. List templates: GET /api/certificates/templates-public/")
    print("5. Get API info: GET /api/certificates/api-info/")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the Django server is running on http://localhost:8000")
        print("💡 Run: python manage.py runserver")
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

