import pandas as pd
from django.core.management.base import BaseCommand
from certificates.models import CoursesHistory
from datetime import datetime
import numpy as np


class Command(BaseCommand):
    help = 'Import courses history from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        excel_file = options['excel_file']

        try:
            df = pd.read_excel(excel_file)

            # Validate required columns
            required_columns = ['ID_Docente', 'Profesor', 'Periodo', 'Materia', 'Clave', 'NRC', 'Fecha_Inicio',
                                'Fecha_Fin', 'Hr_Cont']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self.stdout.write(self.style.ERROR(f'Missing columns: {", ".join(missing_columns)}'))
                return

            # Import data
            imported_count = 0
            error_count = 0

            for _, row in df.iterrows():
                try:
                    # Handle dates properly
                    fecha_inicio = pd.to_datetime(row['Fecha_Inicio']).date()
                    fecha_fin = pd.to_datetime(row['Fecha_Fin']).date()

                    # Handle potential NaN values
                    id_docente = str(row['ID_Docente']) if pd.notna(row['ID_Docente']) else ''
                    profesor = str(row['Profesor']) if pd.notna(row['Profesor']) else ''
                    periodo = str(row['Periodo']) if pd.notna(row['Periodo']) else ''
                    materia = str(row['Materia']) if pd.notna(row['Materia']) else ''
                    clave = str(row['Clave']) if pd.notna(row['Clave']) else ''
                    nrc = str(row['NRC']) if pd.notna(row['NRC']) else ''
                    hr_cont = int(row['Hr_Cont']) if pd.notna(row['Hr_Cont']) else 0

                    CoursesHistory.objects.update_or_create(
                        id_docente=id_docente,
                        nrc=nrc,
                        periodo=periodo,
                        defaults={
                            'profesor': profesor,
                            'materia': materia,
                            'clave': clave,
                            'fecha_inicio': fecha_inicio,
                            'fecha_fin': fecha_fin,
                            'hr_cont': hr_cont
                        }
                    )
                    imported_count += 1
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.WARNING(f'Error importing row: {e}'))
                    continue

            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_count} records'))
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'Failed to import {error_count} records'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
