"""
Almacenamiento persistente de credenciales.
Corrige el bug de "siempre pide credenciales".
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict
from cryptography.fernet import Fernet


class CredentialStore:
    """Almacena credenciales de forma persistente y segura."""
    
    STORE_DIR = Path(__file__).parent / "secure"
    STORE_FILE = STORE_DIR / "credentials.enc"
    KEY_FILE = STORE_DIR / ".key"
    
    @classmethod
    def _get_key(cls) -> bytes:
        """Obtiene o crea clave de cifrado."""
        cls.STORE_DIR.mkdir(parents=True, exist_ok=True)
        
        if cls.KEY_FILE.exists():
            with open(cls.KEY_FILE, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(cls.KEY_FILE, 'wb') as f:
                f.write(key)
            return key
    
    @classmethod
    def _get_cipher(cls) -> Fernet:
        return Fernet(cls._get_key())
    
    @classmethod
    def save_credentials(cls, country_code: str, credentials: Dict) -> bool:
        """Guarda credenciales para un país."""
        try:
            cipher = cls._get_cipher()
            
            # Cargar existentes
            all_creds = cls._load_all_encrypted()
            all_creds[country_code.upper()] = credentials
            
            # Guardar
            encrypted = cipher.encrypt(json.dumps(all_creds).encode())
            cls.STORE_FILE.write_bytes(encrypted)
            return True
        except Exception as e:
            print(f"❌ Error guardando credenciales: {e}")
            return False
    
    @classmethod
    def _load_all_encrypted(cls) -> Dict:
        """Carga todas las credenciales cifradas."""
        if not cls.STORE_FILE.exists():
            return {}
        
        try:
            cipher = cls._get_cipher()
            encrypted = cls.STORE_FILE.read_bytes()
            decrypted = cipher.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception:
            return {}
    
    @classmethod
    def get_credentials(cls, country_code: str) -> Optional[Dict]:
        """Obtiene credenciales para un país."""
        all_creds = cls._load_all_encrypted()
        return all_creds.get(country_code.upper())
    
    @classmethod
    def has_credentials(cls, country_code: str) -> bool:
        """Verifica si hay credenciales para un país."""
        return cls.get_credentials(country_code) is not None
    
    @classmethod
    def clear(cls):
        """Elimina todas las credenciales almacenadas."""
        if cls.STORE_FILE.exists():
            cls.STORE_FILE.unlink()