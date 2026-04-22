"""
Manejo seguro de credenciales - CON SOPORTE MULTI-PAÍS
"""

import csv
import subprocess
from pathlib import Path
from typing import Optional, Dict, List


class VaultManager:
    """Manejo seguro de credenciales por país."""
    
    def __init__(self):
        self.vault_path = Path(__file__).parent / "data_xlsx" / "credentials_vault.csv"
        self._ensure_vault_exists()
    
    def _ensure_vault_exists(self):
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.vault_path.exists():
            with open(self.vault_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['country', 'db_user', 'db_pass', 'alias_user', 'alias_pass', 
                               'ssh_cmd', 'host', 'db_name'])
    
    def validate_db_connection(self, user: str, password: str, host: str, database: str) -> bool:
        """Valida conexión a BD."""
        try:
            import socket
            socket.setdefaulttimeout(5)
            
            import pymysql
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                connect_timeout=5
            )
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            connection.close()
            return True
        except ImportError:
            print("⚠️ pymysql no instalado. Saltando validación BD.")
            return True
        except Exception as e:
            print(f"⚠️ BD no disponible: {e}")
            respuesta = input("¿Continuar de todas formas? (s/n): ").strip().lower()
            return respuesta in ['s', 'si', 'sí', 'yes', 'y']
    
    def validate_ssh_connection(self, ssh_cmd: str) -> bool:
        """Valida conexión SSH."""
        if not ssh_cmd or ssh_cmd == "xxx":
            return True
        
        try:
            result = subprocess.run(
                ['ssh', '-q', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', ssh_cmd, 'exit'],
                timeout=6,
                capture_output=True
            )
            return result.returncode == 0
        except Exception:
            print("⚠️ SSH no disponible. Continuando en modo local.")
            return True
    
    def save_credentials(self, credentials: Dict) -> bool:
        """Guarda credenciales para un país específico."""
        self.validate_db_connection(
            credentials['db_user'],
            credentials['db_pass'],
            credentials.get('host', 'localhost'),
            credentials.get('db_name', 'db_pacifiko')
        )
        
        try:
            rows = []
            exists = False
            
            if self.vault_path.exists():
                with open(self.vault_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            
            country = credentials.get('country', 'GT')
            alias = credentials.get('alias_user', '')
            
            for i, row in enumerate(rows):
                if row.get('country') == country and row.get('alias_user') == alias:
                    rows[i] = credentials
                    exists = True
                    break
            
            if not exists:
                rows.append(credentials)
            
            with open(self.vault_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['country', 'db_user', 'db_pass', 'alias_user', 
                                                       'alias_pass', 'ssh_cmd', 'host', 'db_name'])
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✅ Credenciales guardadas para: {country} - {alias}")
            return True
        except Exception as e:
            print(f"❌ Error guardando vault: {e}")
            return False
    
    def get_credentials(self, country: str, user: str, password: str) -> Optional[Dict]:
        """Obtiene credenciales por país y usuario."""
        if not self.vault_path.exists():
            return None
        
        with open(self.vault_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('country') != country:
                    continue
                if (row['db_user'] == user and row['db_pass'] == password) or \
                   (row['alias_user'] == user and row['alias_pass'] == password):
                    return row
        return None
    
    def get_first_credentials(self, country: Optional[str] = None) -> Optional[Dict]:
        """
        Obtiene el primer registro del vault para un país.
        
        Args:
            country: Código de país (GT, CR). Si None, retorna primero disponible.
        """
        if not self.vault_path.exists():
            return None
        
        with open(self.vault_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if country:
                for row in rows:
                    if row.get('country') == country:
                        return row
                return None
            
            return rows[0] if rows else None
    
    def get_all_countries(self) -> List[str]:
        """Retorna lista de países con credenciales configuradas."""
        if not self.vault_path.exists():
            return []
        
        countries = set()
        with open(self.vault_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('country'):
                    countries.add(row['country'])
        return sorted(list(countries))