# Archivo: Run/Menu/menu_config.py
# Responsabilidad: Configuraciones, modos, persistencia, gestión de cohortes

import json
from pathlib import Path
from typing import List, Optional, Tuple

from Run.Config.paths import Paths, PathsConfig
from Run.Services.cohort_supuestos_manager import CohortSupuestosManager
from Run.Utils.logger import SystemLogger


class MenuConfig:
    """Gestiona configuraciones del menú (modos, persistencia, paths, cohortes)"""
    
    # Constantes de modos
    GROUPING_BEHAVIORAL = "behavioral"
    GROUPING_ENTRY_BASED = "entry_based"
    
    BRAND_MODE_FLAT = "flat"
    BRAND_MODE_HIERARCHICAL = "hierarchical"
    BRAND_MODE_DUAL = "dual"
    
    BRAND_MODE_TO_DIMENSION = {
        BRAND_MODE_FLAT: 3,
        BRAND_MODE_HIERARCHICAL: 5,
        BRAND_MODE_DUAL: 6,
    }
    
    CONVERSION_CUMULATIVE = "cumulative"
    CONVERSION_INCREMENTAL = "incremental"
    
    # Granularidades soportadas
    GRANULARITY_QUARTERLY = 'quarterly'
    GRANULARITY_MONTHLY = 'monthly'
    GRANULARITY_WEEKLY = 'weekly'
    GRANULARITY_SEMIANNUAL = 'semiannual'
    GRANULARITY_YEARLY = 'yearly'
    
    GRANULARITIES = [
        GRANULARITY_QUARTERLY,
        GRANULARITY_MONTHLY,
        GRANULARITY_WEEKLY,
        GRANULARITY_SEMIANNUAL,
        GRANULARITY_YEARLY
    ]
    
    def __init__(self, paths: PathsConfig, logger: SystemLogger):
        self.paths = paths
        self.logger = logger
        
        self.current_grouping_mode = self.GROUPING_ENTRY_BASED
        self.current_brand_mode = self.BRAND_MODE_HIERARCHICAL
        self.current_conversion_mode = self.CONVERSION_CUMULATIVE
        self.current_granularity = self.GRANULARITY_QUARTERLY  # DEFAULT
        
        self.config_file = Path(__file__).parent.parent / "Config" / "user_config.json"
        self.paths_file = Path(__file__).parent.parent / "Config" / "user_paths.json"
        
        self._load_saved_paths()
        self._load_config()
    
    def _load_saved_paths(self):
        """Carga carpetas guardadas, pero valida que pertenezcan a la versión actual."""
        try:
            if self.paths_file.exists():
                with open(self.paths_file, 'r') as f:
                    saved = json.load(f)
                
                # Obtener la versión actual (usa la carpeta base actual)
                current_base = str(self.paths.base_path)
                saved_base = saved.get("base_path", "")
                
                # Si la carpeta base cambió, ignorar rutas guardadas
                if saved_base != current_base:
                    print(f"🔄 Detectado cambio de versión/carpeta base")
                    print(f"   Anterior: {saved_base}")
                    print(f"   Actual:   {current_base}")
                    print(f"   Re-inicializando configuraciones...")
                    return  # No cargar rutas antiguas
                
                if "results_base" in saved:
                    self.paths.results_base = Path(saved["results_base"])
                if "inputs_dir" in saved:
                    self.paths.inputs_dir = Path(saved["inputs_dir"])
                    
        except Exception:
            pass
    
    def _save_paths(self):
        """Guarda las carpetas elegidas junto con la versión actual."""
        try:
            self.paths_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.paths_file, 'w') as f:
                json.dump({
                    "base_path": str(self.paths.base_path),  # NUEVO
                    "results_base": str(self.paths.results_base),
                    "inputs_dir": str(self.paths.inputs_dir)
                }, f)
        except Exception:
            pass
    
    def _load_config(self):
        """Carga configuración guardada desde archivo JSON"""
        default_config = {
            "grouping_mode": self.GROUPING_ENTRY_BASED,
            "brand_mode": self.BRAND_MODE_HIERARCHICAL,
            "conversion_mode": self.CONVERSION_CUMULATIVE,
            "granularity": self.GRANULARITY_QUARTERLY
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    saved = json.load(f)
                    self.current_grouping_mode = saved.get("grouping_mode", default_config["grouping_mode"])
                    self.current_brand_mode = saved.get("brand_mode", default_config["brand_mode"])
                    self.current_conversion_mode = saved.get("conversion_mode", default_config["conversion_mode"])
                    self.current_granularity = saved.get("granularity", default_config["granularity"])
                    return
        except Exception as e:
            self.logger.warning(f"No se pudo cargar configuración: {e}")
        
        self.current_grouping_mode = default_config["grouping_mode"]
        self.current_brand_mode = default_config["brand_mode"]
        self.current_conversion_mode = default_config["conversion_mode"]
        self.current_granularity = default_config["granularity"]
    
    def _save_config(self):
        """Guarda configuración actual a archivo JSON"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({
                    "grouping_mode": self.current_grouping_mode,
                    "brand_mode": self.current_brand_mode,
                    "conversion_mode": self.current_conversion_mode,
                    "granularity": self.current_granularity
                }, f, indent=2)
        except Exception as e:
            self.logger.warning(f"No se pudo guardar configuración: {e}")
    
    # ==================================================================
    # GETTERS PARA DISPLAYS
    # ==================================================================
    
    def get_grouping_mode_display(self) -> str:
        if self.current_grouping_mode == self.GROUPING_BEHAVIORAL:
            return "Comportamental (behavioral)"
        return "Basado en entrada (entry_based)"
    
    def get_brand_mode_display(self) -> str:
        if self.current_brand_mode == self.BRAND_MODE_FLAT:
            return "Plano (todas las compras)"
        elif self.current_brand_mode == self.BRAND_MODE_HIERARCHICAL:
            return "Jerárquico (marca dentro de subcategoría)"
        return "Dual (Subcategoría + Marca separadas)"
    
    def get_conversion_mode_display(self) -> str:
        if self.current_conversion_mode == self.CONVERSION_CUMULATIVE:
            return "Acumulativa (creciente)"
        return "Incremental (distribución)"
    
    def get_granularity_display(self) -> str:
        displays = {
            self.GRANULARITY_QUARTERLY: "Trimestral (quarterly) - DEFAULT",
            self.GRANULARITY_MONTHLY: "Mensual (monthly)",
            self.GRANULARITY_WEEKLY: "Semanal (weekly)",
            self.GRANULARITY_SEMIANNUAL: "Semestral (semiannual)",
            self.GRANULARITY_YEARLY: "Anual (yearly)"
        }
        return displays.get(self.current_granularity, "Trimestral (quarterly) - DEFAULT")
    
    # ==================================================================
    # SELECTORES INTERACTIVOS
    # ==================================================================
    
    def select_grouping_mode(self):
        print("\n" + "=" * 50)
        print("      MODO DE AGRUPACIÓN".center(50))
        print("=" * 50)
        print("\n1. 🔄 Comportamental (behavioral)")
        print("2. 🎯 Basado en entrada (entry_based)")
        print("\nq. 🔙 Volver")
        
        while True:
            option = input("\n👉 Opción (1/2/q): ").strip().lower()
            if option == '1':
                self.current_grouping_mode = self.GROUPING_BEHAVIORAL
                self._save_config()
                print("✅ Modo cambiado")
                break
            elif option == '2':
                self.current_grouping_mode = self.GROUPING_ENTRY_BASED
                self._save_config()
                print("✅ Modo cambiado")
                break
            elif option == 'q':
                break
            else:
                print("❌ Opción inválida")
    
    def select_brand_mode(self):
        print("\n" + "=" * 50)
        print("      MODO DE MARCA".center(50))
        print("=" * 50)
        print("\n1. 🏷️ Plano")
        print("2. 🔗 Jerárquico")
        print("3. 📊 Dual")
        print("\nq. 🔙 Volver")
        
        while True:
            option = input("\n👉 Opción (1/2/3/q): ").strip().lower()
            if option == '1':
                self.current_brand_mode = self.BRAND_MODE_FLAT
                self._save_config()
                print("✅ Modo cambiado")
                break
            elif option == '2':
                self.current_brand_mode = self.BRAND_MODE_HIERARCHICAL
                self._save_config()
                print("✅ Modo cambiado")
                break
            elif option == '3':
                self.current_brand_mode = self.BRAND_MODE_DUAL
                self._save_config()
                print("✅ Modo cambiado")
                break
            elif option == 'q':
                break
            else:
                print("❌ Opción inválida")
    
    def select_granularity(self):
        """Selecciona la granularidad de cohortes (DEFAULT: quarterly)"""
        print("\n" + "=" * 50)
        print("      GRANULARIDAD DE COHORTES".center(50))
        print("=" * 50)
        print(f"\n📊 Granularidad actual: {self.get_granularity_display()}")
        print("\nSelecciona la granularidad temporal:")
        print("   1. Trimestral (quarterly) - DEFAULT, compatible con modelo actual")
        print("   2. Mensual (monthly)")
        print("   3. Semanal (weekly)")
        print("   4. Semestral (semiannual)")
        print("   5. Anual (yearly)")
        print("\n💡 Los supuestos de retention y COGS se transforman automáticamente")
        print("\nq. 🔙 Volver")
        
        while True:
            option = input("\n👉 Opción (1/2/3/4/5/q): ").strip().lower()
            if option == '1':
                self.current_granularity = self.GRANULARITY_QUARTERLY
                self._save_config()
                print("✅ Granularidad cambiada a: Trimestral (quarterly)")
                break
            elif option == '2':
                self.current_granularity = self.GRANULARITY_MONTHLY
                self._save_config()
                print("✅ Granularidad cambiada a: Mensual (monthly)")
                break
            elif option == '3':
                self.current_granularity = self.GRANULARITY_WEEKLY
                self._save_config()
                print("✅ Granularidad cambiada a: Semanal (weekly)")
                break
            elif option == '4':
                self.current_granularity = self.GRANULARITY_SEMIANNUAL
                self._save_config()
                print("✅ Granularidad cambiada a: Semestral (semiannual)")
                break
            elif option == '5':
                self.current_granularity = self.GRANULARITY_YEARLY
                self._save_config()
                print("✅ Granularidad cambiada a: Anual (yearly)")
                break
            elif option == 'q':
                break
            else:
                print("❌ Opción inválida")
    
    @staticmethod
    def select_input_folder() -> Optional[Path]:
        """
        Selecciona carpeta de inputs con:
        - Browser gráfico (tkinter)
        - Entrada manual (CLI)
        - Persistencia en JSON
        """
        # 1. Intentar cargar desde JSON
        saved_path = Paths._load_saved_input_folder()
        if saved_path and saved_path.exists():
            print(f"\n📂 Carpeta de entrada guardada: {saved_path}")
            usar = input("¿Usar esta carpeta? (s/n): ").strip().lower()
            if usar in ['s', 'si', 'sí', 'yes', 'y', '']:
                return saved_path
        
        # 2. Menú de selección
        print("\n" + "=" * 50)
        print("   SELECCIONAR CARPETA DE ENTRADA".center(50))
        print("=" * 50)
        print("📁 Opciones:")
        print("   1. 📂 Seleccionar con explorador gráfico (recomendado)")
        print("   2. ⌨️  Ingresar ruta manualmente")
        print("   3. 📁 Usar carpeta DEFAULT (data_xlsx)")
        print("   4. ❌ Cancelar (usar la actual)")
        print("-" * 50)
        
        option = input("👉 Opción (1/2/3/4): ").strip()
        
        if option == '1':
            # Browser gráfico
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                folder = filedialog.askdirectory(title="Selecciona carpeta de datos LTV")
                root.destroy()
                if folder:
                    path = Path(folder)
                    Paths._save_input_folder(path)
                    print(f"✅ Carpeta seleccionada: {path}")
                    return path
                else:
                    print("⚠️ No se seleccionó ninguna carpeta")
            except Exception as e:
                print(f"⚠️ Error al abrir selector gráfico: {e}")
                print("   Usando opción manual como fallback...")
                # Fallback a entrada manual
                return Paths._manual_input_folder()
        
        elif option == '2':
            return Paths._manual_input_folder()
        
        elif option == '3':
            # Usar default
            default = Paths.get_data_xlsx_folder()
            default.mkdir(parents=True, exist_ok=True)
            Paths._save_input_folder(default)
            print(f"✅ Carpeta DEFAULT seleccionada: {default}")
            return default
        
        else:
            print("⚠️ Cancelado. Usando carpeta actual.")
            return None

    @staticmethod
    def _manual_input_folder() -> Optional[Path]:
        """Entrada manual de ruta."""
        print("\n📝 Ingresa la ruta completa de la carpeta:")
        print("   (Puedes copiar y pegar la ruta)")
        ruta = input("👉 ").strip()
        if ruta:
            path = Path(ruta)
            if path.exists():
                Paths._save_input_folder(path)
                print(f"✅ Carpeta guardada: {path}")
                return path
            else:
                print(f"❌ La ruta '{ruta}' no existe")
                crear = input("¿Crear la carpeta? (s/n): ").strip().lower()
                if crear in ['s', 'si', 'sí', 'yes', 'y']:
                    path.mkdir(parents=True, exist_ok=True)
                    Paths._save_input_folder(path)
                    print(f"✅ Carpeta creada y guardada: {path}")
                    return path
        return None

    @staticmethod
    def _load_saved_input_folder() -> Optional[Path]:
        """Carga la carpeta de inputs guardada en JSON."""
        paths_file = Paths.get_config_folder() / "user_paths.json"
        try:
            if paths_file.exists():
                with open(paths_file, 'r') as f:
                    saved = json.load(f)
                    if "inputs_dir" in saved:
                        return Path(saved["inputs_dir"])
        except Exception:
            pass
        return None

    @staticmethod
    def _save_input_folder(path: Path):
        """Guarda la carpeta de inputs en JSON."""
        paths_file = Paths.get_config_folder() / "user_paths.json"
        try:
            paths_file.parent.mkdir(parents=True, exist_ok=True)
            # Cargar existente o crear nuevo
            if paths_file.exists():
                with open(paths_file, 'r') as f:
                    saved = json.load(f)
            else:
                saved = {}
            
            saved["inputs_dir"] = str(path)
            
            with open(paths_file, 'w') as f:
                json.dump(saved, f, indent=2)
        except Exception as e:
            print(f"⚠️ No se pudo guardar la carpeta: {e}")
    
    @staticmethod
    def select_output_folder() -> Optional[Path]:
        """
        Selecciona carpeta de resultados con:
        - Browser gráfico (tkinter)
        - Entrada manual (CLI)
        - Persistencia en JSON
        """
        # 1. Intentar cargar desde JSON
        saved_path = Paths._load_saved_output_folder()
        if saved_path and saved_path.exists():
            print(f"\n📂 Carpeta de salida guardada: {saved_path}")
            usar = input("¿Usar esta carpeta? (s/n): ").strip().lower()
            if usar in ['s', 'si', 'sí', 'yes', 'y', '']:
                return saved_path
        
        # 2. Menú de selección
        print("\n" + "=" * 50)
        print("   SELECCIONAR CARPETA DE SALIDA".center(50))
        print("=" * 50)
        print("📁 Opciones:")
        print("   1. 📂 Seleccionar con explorador gráfico (recomendado)")
        print("   2. ⌨️  Ingresar ruta manualmente")
        print("   3. 📁 Usar carpeta DEFAULT (Results_LTV)")
        print("   4. ❌ Cancelar (usar la actual)")
        print("-" * 50)
        
        option = input("👉 Opción (1/2/3/4): ").strip()
        
        if option == '1':
            # Browser gráfico
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                folder = filedialog.askdirectory(title="Selecciona carpeta para RESULTADOS LTV")
                root.destroy()
                if folder:
                    path = Path(folder)
                    Paths._save_output_folder(path)
                    print(f"✅ Carpeta seleccionada: {path}")
                    return path
                else:
                    print("⚠️ No se seleccionó ninguna carpeta")
            except Exception as e:
                print(f"⚠️ Error al abrir selector gráfico: {e}")
                print("   Usando opción manual como fallback...")
                return Paths._manual_output_folder()
        
        elif option == '2':
            return Paths._manual_output_folder()
        
        elif option == '3':
            # Usar default
            default = Paths.get_project_root() / "Data_LTV" / "Results_LTV"
            default.mkdir(parents=True, exist_ok=True)
            Paths._save_output_folder(default)
            print(f"✅ Carpeta DEFAULT seleccionada: {default}")
            return default
        
        else:
            print("⚠️ Cancelado. Usando carpeta actual.")
            return None

    @staticmethod
    def _manual_output_folder() -> Optional[Path]:
        """Entrada manual de ruta para salida."""
        print("\n📝 Ingresa la ruta completa de la carpeta:")
        print("   (Puedes copiar y pegar la ruta)")
        ruta = input("👉 ").strip()
        if ruta:
            path = Path(ruta)
            path.mkdir(parents=True, exist_ok=True)
            Paths._save_output_folder(path)
            print(f"✅ Carpeta guardada: {path}")
            return path
        return None

    @staticmethod
    def _load_saved_output_folder() -> Optional[Path]:
        paths_file = Paths.get_config_folder() / "user_paths.json"
        try:
            if paths_file.exists():
                with open(paths_file, 'r') as f:
                    saved = json.load(f)
                    if "results_base" in saved:
                        return Path(saved["results_base"])
        except Exception:
            pass
        return None

    @staticmethod
    def _save_output_folder(path: Path):
        paths_file = Paths.get_config_folder() / "user_paths.json"
        try:
            paths_file.parent.mkdir(parents=True, exist_ok=True)
            if paths_file.exists():
                with open(paths_file, 'r') as f:
                    saved = json.load(f)
            else:
                saved = {}
            
            saved["results_base"] = str(path)
            
            with open(paths_file, 'w') as f:
                json.dump(saved, f, indent=2)
        except Exception as e:
            print(f"⚠️ No se pudo guardar la carpeta: {e}")
    
    # ==================================================================
    # GESTIÓN DE COHORTES (AGREGAR/EDITAR/VER)
    # ==================================================================
    
    def _get_supuestos_manager(self) -> Optional[CohortSupuestosManager]:
        """Obtiene una instancia del manager de supuestos"""
        supuestos_path = self.paths.inputs_dir / self.paths.supuestos_file
        if not supuestos_path.exists():
            print(f"❌ No se encuentra SUPUESTOS.xlsx en {supuestos_path}")
            print("   Ejecuta el pipeline al menos una vez para generarlo")
            return None
        return CohortSupuestosManager(str(supuestos_path))
    
    def _display_cohorts_summary(self, manager: CohortSupuestosManager):
        """Muestra resumen de cohortes existentes"""
        print("\n" + "-" * 50)
        print("📊 COHORTES EXISTENTES".center(50))
        print("-" * 50)
        
        for sheet_name in manager.EXPECTED_SHEETS:
            cohorts = manager.existing_cohorts.get(sheet_name, set())
            if cohorts:
                sorted_cohorts = sorted(list(cohorts), 
                                       key=lambda x: int(x[1:]) if x[1:].lstrip('-').isdigit() else -999)
                print(f"\n📋 {sheet_name}: {len(cohorts)} cohortes")
                # Mostrar primeras 10 y últimas 5
                display = sorted_cohorts[:10]
                if len(sorted_cohorts) > 15:
                    display.append("...")
                    display.extend(sorted_cohorts[-5:])
                print(f"   {', '.join(display)}")
    
    def _add_new_cohorts_interactive(self, manager: CohortSupuestosManager):
        """Agrega nuevas cohortes de forma interactiva"""
        print("\n" + "=" * 50)
        print("   AGREGAR NUEVAS COHORTES".center(50))
        print("=" * 50)
        
        # Detectar cohortes que ya existen
        all_existing = set()
        for cohorts in manager.existing_cohorts.values():
            all_existing.update(cohorts)
        
        print(f"📊 Cohortes existentes: {sorted(list(all_existing))[:20]}...")
        print("\n📝 Ingresa las cohortes que quieres agregar (ej: Q22, Q23, 2024-01)")
        print("   Puedes ingresar múltiples separadas por coma o espacio")
        print("   Deja vacío para cancelar")
        
        cohort_input = input("\n👉 Cohortes a agregar: ").strip()
        if not cohort_input:
            return
        
        # Parsear input
        new_cohorts_raw = cohort_input.replace(',', ' ').split()
        new_cohorts = [c.strip().upper() for c in new_cohorts_raw if c.strip()]
        
        # Filtrar las que ya existen
        really_new = [c for c in new_cohorts if c not in all_existing]
        
        if not really_new:
            print("⚠️ Todas las cohortes ya existen")
            return
        
        print(f"\n📌 Nuevas cohortes a agregar: {really_new}")
        
        # Preguntar por pestañas
        print("\n📋 ¿En qué pestañas quieres agregarlas?")
        print("   1. Todas (1P, 3P, FBP, TM, DS)")
        print("   2. Seleccionar manualmente")
        print("   3. Cancelar")
        
        option = input("\n👉 Opción (1/2/3): ").strip()
        
        if option == '3':
            return
        
        sheets_to_update = []
        if option == '1':
            sheets_to_update = manager.EXPECTED_SHEETS
        else:
            print("\nSelecciona pestañas (separadas por número):")
            for i, sheet in enumerate(manager.EXPECTED_SHEETS, 1):
                print(f"   {i}. {sheet}")
            sheet_input = input("\n👉 Números (ej: 1,3,5): ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in sheet_input.split(',')]
                sheets_to_update = [manager.EXPECTED_SHEETS[i] for i in indices if 0 <= i < len(manager.EXPECTED_SHEETS)]
            except:
                print("❌ Selección inválida")
                return
        
        if not sheets_to_update:
            print("❌ No se seleccionaron pestañas")
            return
        
        # Preguntar por valores
        use_defaults = input("\n¿Usar valores por defecto para retention y cogs? (s/n): ").strip().lower()
        auto_defaults = use_defaults in ['s', 'si', 'sí', 'yes', 'y']
        
        # Agregar a cada pestaña
        for sheet_name in sheets_to_update:
            print(f"\n📝 Procesando pestaña: {sheet_name}")
            new_rows = []
            for cohort in really_new:
                row = manager._prompt_for_values(cohort, sheet_name, use_defaults=auto_defaults)
                new_rows.append(row)
            if new_rows:
                manager._append_to_excel(sheet_name, new_rows)
        
        print("\n✅ Cohortes agregadas exitosamente")
        manager._load_existing_cohorts()
    
    def _edit_cohort_values(self, manager: CohortSupuestosManager):
        """Edita valores de una cohorte existente"""
        print("\n" + "=" * 50)
        print("   EDITAR SUPUESTOS DE COHORTE".center(50))
        print("=" * 50)
        
        # Mostrar pestañas disponibles
        print("\n📋 Pestañas disponibles:")
        for i, sheet in enumerate(manager.EXPECTED_SHEETS, 1):
            cohort_count = len(manager.existing_cohorts.get(sheet, set()))
            print(f"   {i}. {sheet} ({cohort_count} cohortes)")
        
        sheet_choice = input("\n👉 Selecciona pestaña (número): ").strip()
        try:
            sheet_idx = int(sheet_choice) - 1
            if sheet_idx < 0 or sheet_idx >= len(manager.EXPECTED_SHEETS):
                raise ValueError
            sheet_name = manager.EXPECTED_SHEETS[sheet_idx]
        except:
            print("❌ Selección inválida")
            return
        
        # Mostrar cohortes de esa pestaña
        cohorts = sorted(manager.existing_cohorts.get(sheet_name, set()))
        if not cohorts:
            print(f"⚠️ No hay cohortes en {sheet_name}")
            return
        
        print(f"\n📊 Cohortes en {sheet_name}:")
        for i, cohort in enumerate(cohorts[:30], 1):
            print(f"   {i}. {cohort}")
        if len(cohorts) > 30:
            print(f"   ... y {len(cohorts) - 30} más")
        
        cohort_choice = input("\n👉 Selecciona cohorte (nombre o número): ").strip().upper()
        
        # Determinar cohorte seleccionada
        selected_cohort = None
        if cohort_choice.isdigit():
            idx = int(cohort_choice) - 1
            if 0 <= idx < len(cohorts):
                selected_cohort = cohorts[idx]
        else:
            if cohort_choice in cohorts:
                selected_cohort = cohort_choice
        
        if not selected_cohort:
            print(f"❌ Cohorte '{cohort_choice}' no encontrada")
            return
        
        # Obtener valores actuales
        current_values = manager.get_cohort_supuestos(selected_cohort, sheet_name)
        if not current_values:
            print(f"❌ No se encontraron valores para {selected_cohort}")
            return
        
        print(f"\n📝 Editando cohorte {selected_cohort} en pestaña {sheet_name}")
        print(f"   Valores actuales:")
        print(f"   - cogs: {current_values.get('cogs', 'N/A')}")
        print(f"   - retention: {current_values.get('retention', 'N/A')}")
        
        # Solicitar nuevos valores
        new_cogs = input(f"\n👉 Nuevo COGS (Enter para mantener {current_values.get('cogs', 'N/A')}): ").strip()
        new_retention = input(f"👉 Nueva Retention (Enter para mantener {current_values.get('retention', 'N/A')}): ").strip()
        
        # Actualizar en Excel
        try:
            import pandas as pd
            from openpyxl import load_workbook
            
            df = pd.read_excel(manager.supuestos_path, sheet_name=sheet_name)
            df['cohort'] = df['cohort'].astype(str).str.strip().str.upper()
            
            mask = df['cohort'] == selected_cohort
            if new_cogs:
                df.loc[mask, 'cogs'] = float(new_cogs)
            if new_retention:
                df.loc[mask, 'retention'] = float(new_retention)
            
            with pd.ExcelWriter(manager.supuestos_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                # Preservar otras hojas
                excel_file = pd.ExcelFile(manager.supuestos_path)
                for sheet in excel_file.sheet_names:
                    if sheet != sheet_name:
                        df_sheet = pd.read_excel(manager.supuestos_path, sheet_name=sheet)
                        df_sheet.to_excel(writer, sheet_name=sheet, index=False)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"✅ Cohorte {selected_cohort} actualizada")
            manager._load_existing_cohorts()
            
        except Exception as e:
            print(f"❌ Error al actualizar: {e}")
    
    def manage_cohorts_menu(self):
        """Menú principal de gestión de cohortes"""
        manager = self._get_supuestos_manager()
        if not manager:
            return
        
        while True:
            print("\n" + "=" * 50)
            print("   GESTIÓN DE COHORTES".center(50))
            print("=" * 50)
            print("\n1. 📋 Ver cohortes existentes")
            print("2. ➕ Agregar nuevas cohortes")
            print("3. ✏️ Editar valores de cohorte")
            print("4. 🔄 Validar estructura del archivo")
            print("\nq. 🔙 Volver")
            print("=" * 50)
            
            option = input("\n👉 Opción: ").strip().lower()
            
            if option == '1':
                self._display_cohorts_summary(manager)
                input("\nPresiona Enter para continuar...")
            elif option == '2':
                self._add_new_cohorts_interactive(manager)
                input("\nPresiona Enter para continuar...")
            elif option == '3':
                self._edit_cohort_values(manager)
                input("\nPresiona Enter para continuar...")
            elif option == '4':
                warnings = manager.validate_supuestos_file()
                for w in warnings:
                    print(w)
                input("\nPresiona Enter para continuar...")
            elif option == 'q':
                break
            else:
                print("❌ Opción inválida")