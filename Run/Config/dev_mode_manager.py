import csv
from pathlib import Path

class DevModeManager:
    """Control del modo desarrollador"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent / "dev_mode.csv"
        self._ensure_config()
    
    def _ensure_config(self):
        """Asegura que existe el archivo de configuración con valores por defecto"""
        if not self.config_path.exists():
            with open(self.config_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['dev_mode_locked', 'false'])
        else:
            # Verificar que el archivo tiene contenido válido
            try:
                with open(self.config_path, 'r') as f:
                    reader = csv.reader(f)
                    first_row = next(reader, None)
                    if not first_row or len(first_row) < 2:
                        # Archivo corrupto, recrear
                        self._recreate_config()
            except StopIteration:
                # Archivo vacío, recrear
                self._recreate_config()
    
    def _recreate_config(self):
        """Recrea el archivo de configuración"""
        with open(self.config_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['dev_mode_locked', 'false'])
    
    def is_locked(self) -> bool:
        """Retorna si el modo desarrollo está bloqueado"""
        try:
            with open(self.config_path, 'r') as f:
                reader = csv.reader(f)
                # Saltar header si existe
                first_row = next(reader, None)
                if not first_row:
                    return False
                # Si la primera fila tiene 'dev_mode_locked', es header
                if first_row[0] == 'dev_mode_locked':
                    second_row = next(reader, ['false'])
                    return second_row[0].lower() == 'true'
                else:
                    # Formato sin header
                    return first_row[0].lower() == 'true'
        except (StopIteration, IndexError, FileNotFoundError):
            return False
    
    def set_locked(self, locked: bool, master_auth: bool = False) -> bool:
        """Cambia el estado de bloqueo (requiere autenticación real)"""
        if not master_auth:
            return False
        with open(self.config_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['dev_mode_locked', 'true' if locked else 'false'])
        return True