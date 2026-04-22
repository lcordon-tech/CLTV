import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PathsConfig:
    base_path: Path
    code_path: Path
    data_ltv: Path
    inputs_dir: Path
    results_base: Path
    country: str = "GT"
    sois_file: str = "SOIS.xlsx"
    supuestos_file: str = "SUPUESTOS.xlsx"
    catalogo_file: str = "catalogLTV.xlsx"
    cac_file: str = "CAC.xlsx"
    fx_file: str = "TIPO_DE_CAMBIO.xlsx"
    
    def __post_init__(self):
        for folder in [self.data_ltv, self.inputs_dir, self.results_base]:
            folder.mkdir(parents=True, exist_ok=True)
    
    def to_env_dict(self, current_run_folder: Optional[Path] = None) -> dict:
        env = {
            "LTV_PATH_CONTROL": str(self.data_ltv),
            "LTV_INPUT_DIR": str(self.inputs_dir),
            "LTV_SOIS_FILE": self.sois_file,
            "LTV_SUPUESTOS_FILE": self.supuestos_file,
            "LTV_CATALOGO_FILE": self.catalogo_file,
            "LTV_CAC_FILE": self.cac_file,
            "LTV_FX_FILE": self.fx_file,
            "LTV_COUNTRY": self.country,
        }
        if current_run_folder:
            env["LTV_OUTPUT_DIR"] = str(current_run_folder)
        return env
    
    def resolve(self):
        self.data_ltv.mkdir(parents=True, exist_ok=True)
        self.inputs_dir.mkdir(parents=True, exist_ok=True)
        self.results_base.mkdir(parents=True, exist_ok=True)
        return self


class Paths:
    @staticmethod
    def get_project_root() -> Path:
        return Path(__file__).parent.parent.parent
    
    @staticmethod
    def get_config_folder() -> Path:
        return Path(__file__).parent
    
    @staticmethod
    def get_data_xlsx_folder() -> Path:
        return Paths.get_config_folder() / "data_xlsx"
    
    @staticmethod
    def get_recovery_fallback(timestamp: str = None) -> Path:
        from datetime import datetime
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Path.home() / "Downloads" / f"LTV_Recovery_{timestamp}"
    
    @staticmethod
    def _get_paths_file(country: str = "GT") -> Path:
        return Paths.get_config_folder() / f"user_paths_{country}.json"
    
    @staticmethod
    def _load_saved_input_folder(country: str = "GT") -> Optional[Path]:
        paths_file = Paths._get_paths_file(country)
        try:
            if paths_file.exists():
                with open(paths_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    if "inputs_dir" in saved:
                        return Path(saved["inputs_dir"])
        except Exception:
            pass
        return None
    
    @staticmethod
    def _save_input_folder(path: Path, country: str = "GT"):
        paths_file = Paths._get_paths_file(country)
        try:
            paths_file.parent.mkdir(parents=True, exist_ok=True)
            if paths_file.exists():
                with open(paths_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
            else:
                saved = {}
            
            saved["inputs_dir"] = str(path)
            
            with open(paths_file, 'w', encoding='utf-8') as f:
                json.dump(saved, f, indent=2)
        except Exception as e:
            print(f"⚠️ No se pudo guardar la carpeta de entrada: {e}")
    
    @staticmethod
    def _load_saved_output_folder(country: str = "GT") -> Optional[Path]:
        paths_file = Paths._get_paths_file(country)
        try:
            if paths_file.exists():
                with open(paths_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    if "results_base" in saved:
                        return Path(saved["results_base"])
        except Exception:
            pass
        return None
    
    @staticmethod
    def _save_output_folder(path: Path, country: str = "GT"):
        paths_file = Paths._get_paths_file(country)
        try:
            paths_file.parent.mkdir(parents=True, exist_ok=True)
            if paths_file.exists():
                with open(paths_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
            else:
                saved = {}
            
            saved["results_base"] = str(path)
            
            with open(paths_file, 'w', encoding='utf-8') as f:
                json.dump(saved, f, indent=2)
        except Exception as e:
            print(f"⚠️ No se pudo guardar la carpeta de salida: {e}")
    
    @staticmethod
    def get_production_paths(country: str = "GT") -> PathsConfig:
        root = Paths.get_project_root()
        base = root / f"Data_LTV_{country}"
        
        saved_inputs = Paths._load_saved_input_folder(country)
        if saved_inputs and saved_inputs.exists():
            inputs_dir = saved_inputs
        else:
            inputs_dir = Paths.get_data_xlsx_folder()
        
        saved_results = Paths._load_saved_output_folder(country)
        if saved_results and saved_results.exists():
            results_base = saved_results
        else:
            results_base = base / "Results_LTV"
        
        return PathsConfig(
            base_path=base,
            code_path=root,
            data_ltv=base / "Data_LTV",
            inputs_dir=inputs_dir,
            results_base=results_base,
            country=country
        )
    
    @staticmethod
    def select_input_folder(country: str = "GT") -> Optional[Path]:
        saved_path = Paths._load_saved_input_folder(country)
        if saved_path and saved_path.exists():
            print(f"\n📂 Carpeta de entrada guardada: {saved_path}")
            usar = input("¿Usar esta carpeta? (s/n): ").strip().lower()
            if usar in ['s', 'si', 'sí', 'yes', 'y', '']:
                return saved_path
        
        print("\n" + "=" * 50)
        print(f"   SELECCIONAR CARPETA DE ENTRADA ({country})".center(50))
        print("=" * 50)
        print("📁 Opciones:")
        print("   1. Usar carpeta DEFAULT (data_xlsx)")
        print("   2. Ingresar ruta manualmente")
        print("   3. Cancelar (usar la actual)")
        print("-" * 50)
        
        option = input("👉 Opción (1/2/3): ").strip()
        
        if option == '1':
            default = Paths.get_data_xlsx_folder()
            default.mkdir(parents=True, exist_ok=True)
            Paths._save_input_folder(default, country)
            print(f"✅ Carpeta DEFAULT seleccionada: {default}")
            return default
        elif option == '2':
            print("\n📝 Ingresa la ruta completa de la carpeta:")
            ruta = input("👉 ").strip()
            if ruta:
                path = Path(ruta)
                if path.exists():
                    Paths._save_input_folder(path, country)
                    print(f"✅ Carpeta guardada: {path}")
                    return path
                else:
                    crear = input("¿Crear la carpeta? (s/n): ").strip().lower()
                    if crear in ['s', 'si', 'sí', 'yes', 'y']:
                        path.mkdir(parents=True, exist_ok=True)
                        Paths._save_input_folder(path, country)
                        print(f"✅ Carpeta creada y guardada: {path}")
                        return path
        return None
    
    @staticmethod
    def select_output_folder(country: str = "GT") -> Optional[Path]:
        saved_path = Paths._load_saved_output_folder(country)
        if saved_path and saved_path.exists():
            print(f"\n📂 Carpeta de salida guardada: {saved_path}")
            usar = input("¿Usar esta carpeta? (s/n): ").strip().lower()
            if usar in ['s', 'si', 'sí', 'yes', 'y', '']:
                return saved_path
        
        print("\n" + "=" * 50)
        print(f"   SELECCIONAR CARPETA DE SALIDA ({country})".center(50))
        print("=" * 50)
        print("📁 Opciones:")
        print("   1. Usar carpeta DEFAULT (Results_LTV)")
        print("   2. Ingresar ruta manualmente")
        print("   3. Cancelar (usar la actual)")
        print("-" * 50)
        
        option = input("👉 Opción (1/2/3): ").strip()
        
        if option == '1':
            default = Paths.get_project_root() / f"Data_LTV_{country}" / "Results_LTV"
            default.mkdir(parents=True, exist_ok=True)
            Paths._save_output_folder(default, country)
            print(f"✅ Carpeta DEFAULT seleccionada: {default}")
            return default
        elif option == '2':
            print("\n📝 Ingresa la ruta completa de la carpeta:")
            ruta = input("👉 ").strip()
            if ruta:
                path = Path(ruta)
                path.mkdir(parents=True, exist_ok=True)
                Paths._save_output_folder(path, country)
                print(f"✅ Carpeta guardada: {path}")
                return path
        return None