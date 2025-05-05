# tasks.py
from celery import shared_task
import subprocess
import os


@shared_task
def execute_script(script_name, parameters):
    """Execute pre-approved scripts safely"""
    # Whitelist of allowed scripts
    ALLOWED_SCRIPTS = {
        'generate_report': '/path/to/scripts/generate_report.py',
        'process_data': '/path/to/scripts/process_data.py',
    }

    if script_name not in ALLOWED_SCRIPTS:
        return {'error': 'Script not allowed'}

    script_path = ALLOWED_SCRIPTS[script_name]

    try:
        result = subprocess.run(
            ['python', script_path] + parameters,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        return {
            'output': result.stdout,
            'error': result.stderr,
            'return_code': result.returncode
        }
    except Exception as e:
        return {'error': str(e)}