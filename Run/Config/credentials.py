"""
Centraliza todas las credenciales del sistema - CON SOPORTE MULTI-PAÍS
"""
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from .vault_manager import VaultManager


@dataclass
class DBCredentials:
    user: str
    password: str
    host: str
    database: str
    country: str = "GT"
    
    def to_env_dict(self) -> dict:
        return {
            "DB_USER": self.user,
            "DB_PASSWORD": self.password,
            "DB_HOST": self.host,
            "DB_NAME": self.database,
            "LTV_COUNTRY": self.country
        }


@dataclass
class SSHCredentials:
    command: str
    enabled: bool = True
    wait_seconds: int = 5
    
    def get_command(self) -> Optional[str]:
        return self.command if self.enabled else None


class Credentials:
    _vault = VaultManager()
    _cached_db: Optional[DBCredentials] = None
    _cached_ssh: Optional[SSHCredentials] = None
    _current_country: Optional[str] = None
    
    @staticmethod
    def reload_from_vault(country: Optional[str] = None):
        """
        Recarga credenciales desde el vault para un país específico.
        
        Args:
            country: Código de país (GT, CR). Si None, usa el primero disponible.
        """
        creds = Credentials._vault.get_first_credentials(country)
        if creds:
            Credentials._current_country = creds.get('country', 'GT')
            Credentials._cached_db = DBCredentials(
                user=creds['db_user'],
                password=creds['db_pass'],
                host=creds.get('host', 'localhost'),
                database=creds.get('db_name', 'db_pacifiko'),
                country=Credentials._current_country
            )
            
            ssh_cmd = creds.get('ssh_cmd', '')
            Credentials._cached_ssh = SSHCredentials(
                command=ssh_cmd,
                enabled=bool(ssh_cmd),
                wait_seconds=5
            )
            return True
        return False
    
    @staticmethod
    def load_for_country(country: str) -> bool:
        """Carga credenciales específicas para un país."""
        return Credentials.reload_from_vault(country)
    
    @staticmethod
    def get_db_credentials() -> DBCredentials:
        if Credentials._cached_db is None:
            if not Credentials.reload_from_vault():
                raise Exception("No hay credenciales configuradas. Ejecuta setup primero.")
        return Credentials._cached_db
    
    @staticmethod
    def get_ssh_credentials() -> SSHCredentials:
        if Credentials._cached_ssh is None:
            Credentials.reload_from_vault()
        return Credentials._cached_ssh if Credentials._cached_ssh else SSHCredentials(command="", enabled=False)
    
    @staticmethod
    def get_current_country() -> Optional[str]:
        return Credentials._current_country
    
    @staticmethod
    def get_backup_credentials() -> dict:
        return {
            "backup_path": str(Path(__file__).parent.parent / "backups"),
            "retention_days": 30
        }