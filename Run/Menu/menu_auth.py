"""
Autenticación, registro de usuarios, vault con persistencia.
Corregido: ahora usa CredentialStore para no pedir credenciales siempre.
"""

import csv
from pathlib import Path
from typing import Optional

from Run.Config.credentials import Credentials
from Run.Config.vault_manager import VaultManager
from Run.Config.dev_mode_manager import DevModeManager
from Run.Config.credential_store import CredentialStore
from Run.Utils.input_utils import get_flexible_input
from Run.Utils.logger import SystemLogger


class MenuAuth:
    """Gestiona autenticación y registro de usuarios con persistencia."""
    
    def __init__(self, vault: VaultManager, dev_mode: DevModeManager, logger: SystemLogger):
        self.vault = vault
        self.dev_mode = dev_mode
        self.logger = logger
        self._current_country: Optional[str] = None
        self._cached_creds: Optional[dict] = None
    
    def set_country(self, country_code: str):
        """Establece el país actual para autenticación."""
        self._current_country = country_code.upper()
        self._cached_creds = None  # Limpiar cache
    
    def has_credentials_for_country(self, country_code: str = None) -> bool:
        """Verifica si hay credenciales para un país específico."""
        if country_code is None:
            country_code = self._current_country or "GT"
        return CredentialStore.has_credentials(country_code)
    
    def _load_credentials_to_cache(self, creds: dict):
        """Carga credenciales al sistema y cache local."""
        self._cached_creds = creds
        
        # Cargar al sistema de credenciales global
        Credentials.reload_from_vault()
    
    def authenticate(self, country_code: str = None) -> bool:
        """
        Autenticación con credenciales persistentes.
        Solo pide credenciales si no existen o son inválidas.
        
        Args:
            country_code: Código de país (GT, CR). Si None, usa el actual.
        
        Returns:
            True si autenticado, False si no
        """
        # Modo desarrollador desbloqueado
        if not self.dev_mode.is_locked():
            print("\n🔓 [MODO DESARROLLADOR: DESBLOQUEADO]")
            print("⚡ Acceso directo sin autenticación")
            return True
        
        if country_code is None:
            country_code = self._current_country or "GT"
        
        print(f"\n🔒 [MODO DESARROLLADOR: BLOQUEADO]")
        print(f"🌎 Autenticando para: {country_code}")
        
        # 1. Verificar si hay credenciales guardadas
        if self.has_credentials_for_country(country_code):
            creds = CredentialStore.get_credentials(country_code)
            if creds:
                print("🔐 Credenciales encontradas. Validando...")
                if self.vault.validate_db_connection(
                    creds['db_user'], creds['db_pass'],
                    creds.get('host', 'localhost'), 
                    creds.get('db_name', 'db_pacifiko')
                ):
                    print("✅ Conexión DB exitosa")
                    self._load_credentials_to_cache(creds)
                    self.logger.info(f"Autenticado para {country_code} con credenciales guardadas")
                    return True
                else:
                    print("⚠️ Credenciales guardadas no son válidas. Serán reemplazadas.")
        
        # 2. No hay credenciales válidas → solicitar nuevas
        return self._interactive_auth(country_code)
    
    def _interactive_auth(self, country_code: str) -> bool:
        """
        Autenticación interactiva cuando no hay credenciales válidas.
        
        Args:
            country_code: Código de país para las credenciales
        """
        intentos = 0
        while intentos < 3:
            print("\n" + "=" * 40)
            print(f"     ACCESO AL SISTEMA LTV - {country_code}".center(40))
            print("=" * 40)
            print("1. 🔐 Ingresar con credenciales")
            print("2. 👤 Registrar nuevo usuario")
            print("q. ❌ Salir")
            print("=" * 40)
            
            option = input("\n👉 Opción: ").strip().lower()
            
            if option == '1':
                user = input("Usuario: ").strip()
                password = input("Contraseña: ").strip()
                
                creds = self.vault.get_credentials(user, password)
                if creds:
                    # Guardar credenciales para el país
                    creds['country'] = country_code
                    CredentialStore.save_credentials(country_code, creds)
                    self._load_credentials_to_cache(creds)
                    print("✅ Autenticación exitosa")
                    self.logger.info(f"Usuario autenticado para {country_code}: {user}")
                    return True
                else:
                    intentos += 1
                    print(f"❌ Credenciales incorrectas. Intentos restantes: {3 - intentos}")
            
            elif option == '2':
                if self.setup_new_user(country_code):
                    return True
                else:
                    intentos += 1
                    print(f"❌ Registro fallido. Intentos restantes: {3 - intentos}")
            
            elif option == 'q':
                return False
            else:
                print("❌ Opción inválida")
        
        print("❌ Demasiados intentos fallidos. Saliendo...")
        return False
    
    def setup_new_user(self, country_code: str = None) -> bool:
        """Flujo de registro de nuevo usuario para un país específico."""
        if country_code is None:
            country_code = self._current_country or "GT"
        
        print("\n" + "=" * 50)
        print(f"   REGISTRO DE NUEVO USUARIO - {country_code}".center(50))
        print("=" * 50)
        
        print("\n📌 Credenciales de Base de Datos:")
        db_user = input("Usuario DB: ").strip()
        db_pass = input("Contraseña DB: ").strip()
        db_host = input("Host DB [localhost]: ").strip() or "localhost"
        db_name = input("Nombre DB [db_pacifiko]: ").strip() or "db_pacifiko"
        
        print("\n👤 Credenciales de acceso (alias):")
        alias_user = input("Usuario alias: ").strip()
        alias_pass = input("Contraseña alias: ").strip()
        
        print("\n🔐 Configuración SSH (opcional, Enter para omitir):")
        ssh_cmd = input("Comando SSH: ").strip()
        
        creds = {
            'db_user': db_user,
            'db_pass': db_pass,
            'alias_user': alias_user,
            'alias_pass': alias_pass,
            'ssh_cmd': ssh_cmd if ssh_cmd else "",
            'host': db_host,
            'db_name': db_name,
            'country': country_code
        }
        
        try:
            rows = []
            vault_path = self.vault.vault_path
            
            if vault_path.exists():
                with open(vault_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            
            # Buscar si ya existe para este país
            for i, row in enumerate(rows):
                if row.get('alias_user') == alias_user:
                    rows[i] = creds
                    break
            else:
                rows.append(creds)
            
            with open(vault_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['country', 'db_user', 'db_pass', 
                                                        'alias_user', 'alias_pass', 
                                                        'ssh_cmd', 'host', 'db_name'])
                writer.writeheader()
                writer.writerows(rows)
            
            # Guardar en almacenamiento persistente
            CredentialStore.save_credentials(country_code, creds)
            
            print("\n✅ Usuario registrado exitosamente")
            self._load_credentials_to_cache(creds)
            return True
            
        except Exception as e:
            print(f"❌ Error guardando credenciales: {e}")
            return False
    
    def has_credentials(self) -> bool:
        """Verifica si hay credenciales configuradas (legacy)."""
        return self.vault.get_first_credentials() is not None
    
    def get_current_country(self) -> Optional[str]:
        """Retorna el país actual."""
        return self._current_country