# Archivo: Run/Menu/menu_controller.py
# Versión v11.0 - MULTI-PAÍS CON CAMBIO DE PAÍS EN RUNTIME

import os
import signal
import sys
from pathlib import Path
from typing import List, Optional

RUN_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RUN_PATH not in sys.path:
    sys.path.insert(0, RUN_PATH)

from Run.Config.paths import Paths, PathsConfig
from Run.Config.vault_manager import VaultManager
from Run.Config.dev_mode_manager import DevModeManager
from Run.Config.credential_store import CredentialStore
from Run.Country.country_loader import CountryLoader
from Run.Country.country_selector import CountrySelector
from Run.Country.country_context import CountryContext
from Run.FX.fx_engine import FXEngine
from Run.Menu.menu_auth import MenuAuth
from Run.Menu.menu_config import MenuConfig
from Run.Menu.menu_executor import MenuExecutor
from Run.Core.cohort_context_manager import CohortContextManager
from Run.Utils.logger import SystemLogger
from Run.Utils.input_utils import get_flexible_input


class MenuController:
    """Orquestador principal - MULTI-PAÍS CON CAMBIO DINÁMICO"""
    
    MODE_CHANGE_COUNTRY = '0'
    MODE_FULL = '1'
    MODE_DR_ONLY = '2'
    MODE_MODEL = '3'
    MODE_QUERY = '4'
    MODE_CONFIG = '5'
    MODE_QUIT = 'q'
    
    SUBMODE_MODEL_COMPLETE = '1'
    SUBMODE_MODEL_GENERAL = '2'
    SUBMODE_CATEGORY = '3'
    SUBMODE_SUBCATEGORY = '4'
    SUBMODE_BRAND = '5'
    SUBMODE_PRODUCT = '6'
    SUBMODE_SPECIAL = '7'
    SUBMODE_HEAVY_ONLY = '8'
    
    DIM_CATEGORY = '1'
    DIM_SUBCATEGORY = '2'
    DIM_BRAND = '3'
    DIM_PRODUCT = '4'
    
    def __init__(self, paths: PathsConfig, country_context: CountryContext, fx_engine: FXEngine):
        self.paths = paths
        self.country_context = country_context
        self.fx_engine = fx_engine
        self.logger = SystemLogger()
        
        self.vault = VaultManager()
        self.dev_mode = DevModeManager()
        
        self.auth = MenuAuth(self.vault, self.dev_mode, self.logger)
        self.auth.set_country(country_context.code)
        
        self.config = MenuConfig(paths, self.logger)
        self.executor = MenuExecutor(paths, self.logger, country_context, fx_engine)
        
        self._cohort_context = None
        signal.signal(signal.SIGINT, self._graceful_shutdown_handler)
    
    def _get_cohort_context(self) -> CohortContextManager:
        if self._cohort_context is None:
            supuestos_path = self.paths.inputs_dir / self.paths.supuestos_file
            self._cohort_context = CohortContextManager(supuestos_path, self.country_context)
        return self._cohort_context
    
    def _graceful_shutdown_handler(self, signum, frame):
        print("\n\n⚠️ Interrupción detectada. Cerrando conexiones...")
        self.logger.info("Ctrl+C detectado - iniciando shutdown graceful")
        self.executor.ssh_manager.stop()
    
    def _validate_input_files(self) -> bool:
        input_dir = self.paths.inputs_dir
        required_files = [self.paths.sois_file, self.paths.supuestos_file, self.paths.catalogo_file]
        
        missing = []
        for file in required_files:
            full_path = input_dir / file
            if not full_path.exists():
                missing.append(file)
        
        if missing:
            print(f"\n❌ Archivos faltantes en {input_dir}:")
            for f in missing:
                print(f"   • {f}")
            print("\n📌 Opciones:")
            print("   1. Colocar los archivos en la carpeta indicada")
            print("   2. Cambiar carpeta de entrada (opción en Configuraciones)")
            return False
        
        print(f"✅ Archivos Excel encontrados ({len(required_files)}/{len(required_files)})")
        return True
    
    def _validate_pre_conditions(self) -> bool:
        print("\n" + "🔍 VALIDACIÓN PRE-OPERACIONAL".center(60, "-"))
        
        if not self._validate_input_files():
            return False
        
        print(f"🌎 País activo: {self.country_context.name} ({self.country_context.code})")
        print(f"💱 Tipo de cambio base: {self.country_context.default_fx_rate}")
        
        test_file = self.paths.results_base / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print("✅ Permisos de escritura OK")
        except Exception:
            print(f"❌ No se puede escribir en {self.paths.results_base}")
            return False
        
        print("-" * 60)
        return True
    
    def display_main_menu(self):
        print("\n" + "=" * 60)
        print(f"      SISTEMA LTV - {self.country_context.name}".center(60))
        print("=" * 60)
        print(f"\n⚙️ CONFIGURACIÓN ACTUAL:")
        print(f"   🌎 País: {self.country_context.name} ({self.country_context.currency})")
        print(f"   📊 Agrupación: {self.config.get_grouping_mode_display()}")
        print(f"   🏷️  Modo marca: {self.config.get_brand_mode_display()}")
        print(f"   📅 Granularidad: {self.config.get_granularity_display()}")
        print(f"   📂 Input dir: {self.paths.inputs_dir}")
        print("\n" + "-" * 40)
        print("0. 🌍 Cambiar país")
        print("1. 🚀 PIPELINE COMPLETO")
        print("2. 💾 SOLO DATA REPOSITORY")
        print("3. 📊 MODELO")
        print("4. 🔍 BUSCADOR")
        print("5. ⚙️ CONFIGURACIONES")
        print("q. ❌ SALIR")
        print("=" * 60)
        return input("\n👉 Selecciona una opción: ").strip().lower()
    
    def display_model_submenu(self):
        print("\n" + "=" * 60)
        print(f"      MODELO - {self.country_context.name}".center(60))
        print("=" * 60)
        print(f"\n⚙️ Modo marca actual: {self.config.get_brand_mode_display()}")
        print(f"📅 Granularidad actual: {self.config.get_granularity_display()}")
        print("\n1. 📊 Modelo COMPLETO (Todas las dimensiones + análisis pesados)")
        print("2. 📋 Modelo GENERAL (Solo Category + Subcategory)")
        print("3. 📂 Categoría (Category)")
        print("4. 📁 Subcategoría (Subcategory)")
        print("5. 🏷️ Marca (Brand)")
        print("6. 🎯 Producto")
        print("7. 🎛️ Especial (Seleccionar dimensiones específicas)")
        print("8. 🔬 SOLO ANÁLISIS PESADOS (sin reportes multi-dimensión)")
        print("\nq. 🔙 Volver al menú principal")
        print("=" * 60)
        return input("\n👉 Selecciona una opción: ").strip().lower()
    
    def display_config_submenu(self):
        print("\n" + "=" * 60)
        print("      CONFIGURACIONES".center(60))
        print("=" * 60)
        print(f"\n1. 🔄 Modo de agrupación: {self.config.get_grouping_mode_display()}")
        print(f"2. 🏷️  Modo de análisis de marca: {self.config.get_brand_mode_display()}")
        print(f"3. 📅 Granularidad de cohortes: {self.config.get_granularity_display()}")
        print(f"4. 📂 Cambiar carpeta de ENTRADA (inputs)")
        print(f"5. 💾 Cambiar carpeta de SALIDA (resultados)")
        print(f"6. 📊 GESTIÓN DE COHORTES (agregar/editar/ver)")
        print("\nq. 🔙 Volver")
        print("=" * 60)
        return input("\n👉 Selecciona una opción: ").strip().lower()
    
    def display_special_dimensions_menu(self, selected: List[str]) -> str:
        print("\n" + "=" * 60)
        print("      SELECCIÓN DE DIMENSIONES".center(60))
        print("=" * 60)
        print(f"\n✅ Dimensiones seleccionadas: {', '.join(selected) if selected else 'NINGUNA'}")
        print("\n📂 Dimensiones disponibles:")
        print("   1. Categoría (Category)")
        print("   2. Subcategoría (Subcategory)")
        print("   3. Marca (Brand)")
        print("   4. Producto (Product)")
        print("\n   q. ✅ Ejecutar análisis con las dimensiones seleccionadas")
        print("   r. 🔄 Reiniciar selección")
        print("   b. 🔙 Volver al menú de modelo")
        print("=" * 60)
        return input("\n👉 Selecciona una opción: ").strip().lower()
    
    # ==================================================================
    # MÉTODOS DE CONFIGURACIÓN
    # ==================================================================
    
    def _select_grouping_mode(self):
        self.config.select_grouping_mode()
    
    def _select_brand_mode(self):
        self.config.select_brand_mode()
    
    def _select_granularity(self):
        self.config.select_granularity()
    
    def _select_input_folder(self):
        new_path = Paths.select_input_folder(self.country_context.code)
        if new_path:
            self.paths.inputs_dir = new_path
    
    def _select_output_folder(self):
        new_path = Paths.select_output_folder(self.country_context.code)
        if new_path:
            self.paths.results_base = new_path
    
    def _manage_cohorts(self):
        self.config.manage_cohorts_menu()
    
    # ==================================================================
    # MÉTODO PARA CAMBIAR PAÍS
    # ==================================================================
    
    def _change_country(self):
        """Cambia el país actual y reinicia el contexto sin reiniciar programa."""
        print("\n" + "=" * 60)
        print("   CAMBIAR PAÍS".center(60))
        print("=" * 60)
        
        # Detener SSH si estaba activo
        self.executor.ssh_manager.stop()
        
        # Limpiar cache de cohort context
        self._cohort_context = None
        
        # Recargar selector de país
        selector = CountrySelector()
        
        if not selector.has_countries():
            print("❌ No hay configuraciones de países disponibles")
            return
        
        new_country_code = selector.select()
        
        if new_country_code == self.country_context.code:
            print("✅ Mismo país seleccionado. No hay cambios.")
            return
        
        # Cargar nueva configuración
        country_config = CountryLoader.load_country(new_country_code)
        if not country_config:
            print(f"❌ Error cargando configuración para {new_country_code}")
            return
        
        # Crear nuevo contexto
        self.country_context = CountryContext(
            code=country_config.code,
            name=country_config.name,
            currency=country_config.currency,
            default_fx_rate=country_config.default_fx_rate,
            cohort_start_year=country_config.cohort_start_year,
            cohort_end_year=country_config.cohort_end_year
        )
        
        # Actualizar auth con nuevo país
        self.auth.set_country(new_country_code)
        
        # Recargar rutas (paths)
        self.paths = Paths.get_production_paths(new_country_code)
        
        # Recargar FXEngine
        fx_path = self.paths.inputs_dir / self.paths.fx_file
        self.fx_engine = FXEngine(self.country_context, fx_path)
        
        # Actualizar config con nuevas rutas
        self.config.paths = self.paths
        
        # Recrear executor con nuevo contexto
        self.executor = MenuExecutor(self.paths, self.logger, self.country_context, self.fx_engine)
        
        print(f"\n✅ País cambiado a: {self.country_context.name}")
        print(f"   📅 Cohortes desde: {self.country_context.cohort_start_year}")
        print(f"   💱 Moneda: {self.country_context.currency}")
        print("   🔄 Contexto reinicializado correctamente")
    
    # ==================================================================
    # MÉTODOS DE EJECUCIÓN
    # ==================================================================
    
    def _run_full_pipeline(self):
        if not self._validate_pre_conditions():
            return
        date_range = self.executor.get_date_range_from_user()
        self.executor.run_full_pipeline(
            date_range=date_range,
            grouping_mode=self.config.current_grouping_mode,
            conversion_mode=self.config.current_conversion_mode,
            granularity=self.config.current_granularity
        )
    
    def _run_dr_only(self):
        if not self._validate_pre_conditions():
            return
        date_range = self.executor.get_date_range_from_user()
        self.executor.run_dr_only(date_range)
    
    def _run_model_complete(self, date_range=None):
        self.executor.run_model_analysis(
            [1, 2, 3, 4, 5, 6], "Modelo Completo",
            date_range=date_range,
            grouping_mode=self.config.current_grouping_mode,
            conversion_mode=self.config.current_conversion_mode,
            granularity=self.config.current_granularity
        )
    
    def _run_model_general(self, date_range=None):
        self.executor.run_model_analysis(
            [1, 2], "Modelo General", only_category=True,
            date_range=date_range,
            grouping_mode=self.config.current_grouping_mode,
            conversion_mode=self.config.current_conversion_mode,
            granularity=self.config.current_granularity
        )
    
    def _run_model_category(self, date_range=None):
        self.executor.run_model_analysis(
            [1], "Categoría",
            date_range=date_range,
            grouping_mode=self.config.current_grouping_mode,
            conversion_mode=self.config.current_conversion_mode,
            granularity=self.config.current_granularity
        )
    
    def _run_model_subcategory(self, date_range=None):
        self.executor.run_model_analysis(
            [2], "Subcategoría",
            date_range=date_range,
            grouping_mode=self.config.current_grouping_mode,
            conversion_mode=self.config.current_conversion_mode,
            granularity=self.config.current_granularity
        )
    
    def _run_model_brand(self, date_range=None):
        dim_code = self.config.BRAND_MODE_TO_DIMENSION[self.config.current_brand_mode]
        dim_name = self.config.get_brand_mode_display()
        self.executor.run_model_analysis(
            [dim_code], dim_name,
            date_range=date_range,
            grouping_mode=self.config.current_grouping_mode,
            conversion_mode=self.config.current_conversion_mode,
            granularity=self.config.current_granularity
        )
    
    def _run_model_product(self, date_range=None):
        self.executor.run_model_analysis(
            [4], "Producto",
            date_range=date_range,
            grouping_mode=self.config.current_grouping_mode,
            conversion_mode=self.config.current_conversion_mode,
            granularity=self.config.current_granularity
        )
    
    def _run_special_mode(self, date_range=None):
        selected = []
        dim_map = {
            "Categoría": 1,
            "Subcategoría": 2,
            "Marca": self.config.BRAND_MODE_TO_DIMENSION[self.config.current_brand_mode],
            "Producto": 4,
        }
        
        while True:
            option = self.display_special_dimensions_menu(selected)
            
            if option == self.DIM_CATEGORY:
                if "Categoría" not in selected:
                    selected.append("Categoría")
            elif option == self.DIM_SUBCATEGORY:
                if "Subcategoría" not in selected:
                    selected.append("Subcategoría")
            elif option == self.DIM_BRAND:
                if "Marca" not in selected:
                    selected.append("Marca")
            elif option == self.DIM_PRODUCT:
                if "Producto" not in selected:
                    selected.append("Producto")
            elif option == 'r':
                selected = []
                print("\n🔄 Selección reiniciada.")
            elif option == 'q':
                if not selected:
                    print("❌ No has seleccionado ninguna dimensión.")
                    continue
                dimensions = [dim_map[name] for name in selected]
                display_name = " + ".join(selected)
                self.executor.run_model_analysis(
                    dimensions, display_name, only_category=False, date_range=date_range,
                    grouping_mode=self.config.current_grouping_mode,
                    conversion_mode=self.config.current_conversion_mode,
                    granularity=self.config.current_granularity
                )
                return
            elif option == 'b':
                return
            else:
                print("❌ Opción inválida.")
    
    def _run_heavy_analysis_only(self, date_range=None):
        self.executor.run_heavy_analysis_only(
            date_range=date_range,
            grouping_mode=self.config.current_grouping_mode,
            conversion_mode=self.config.current_conversion_mode,
            granularity=self.config.current_granularity
        )
    
    def _run_query_mode(self):
        print("\n" + "=" * 60)
        print(f"      BUSCADOR INTERACTIVO LTV - {self.country_context.name}".center(60))
        print("=" * 60)
        
        confirm = input("\n👉 ¿Continuar? (s/n): ").strip().lower()
        if confirm not in ['s', 'si', 'sí', 'yes', 'y']:
            return
        
        if not self.executor.data_ltv_has_files():
            print("\n❌ No se encontraron datos en Data_LTV")
            respuesta = input("¿Deseas ejecutar DataRepository primero? (s/n): ").strip().lower()
            if respuesta in ['s', 'si', 'sí', 'yes', 'y']:
                if not self.executor.run_dr():
                    print("❌ DataRepository falló.")
                    return
            else:
                return
        
        try:
            from Model.Domain.controller import LTVController
            from Model.Data.real_data_repository import RealDataRepository
            from Category.Utils.query_engine import DimensionQueryEngine
            from Category.Cohort.cohort_config import CohortConfig, TimeGranularity
            
            real_repo = RealDataRepository()
            raw_data = real_repo.get_orders_from_excel(
                path_or_dir=str(self.paths.data_ltv),
                country_config=self.country_context
            )
            
            ltv_engine = LTVController()
            ltv_engine.process_raw_data(raw_data)
            customers = ltv_engine.get_customers()
            
            print(f"   ✅ {len(customers)} clientes cargados en memoria")
            
            cohort_context = self._get_cohort_context()
            granularity = self.config.current_granularity
            
            ad_spend = cohort_context.get_cac_map(granularity=granularity)
            
            granularity_map = {
                "quarterly": TimeGranularity.QUARTERLY,
                "monthly": TimeGranularity.MONTHLY,
                "weekly": TimeGranularity.WEEKLY,
                "semiannual": TimeGranularity.SEMIANNUAL,
                "yearly": TimeGranularity.YEARLY,
            }
            time_granularity = granularity_map.get(granularity, TimeGranularity.QUARTERLY)
            cohort_config = CohortConfig(granularity=time_granularity)
            
            engine = DimensionQueryEngine(
                customers,
                grouping_mode=self.config.current_grouping_mode,
                conversion_mode=self.config.current_conversion_mode,
                ue_results=None,
                cohort_config=cohort_config,
                cac_map=ad_spend
            )
            
            while True:
                print("\n" + "-" * 40)
                print(f"🔍 BUSCADOR LTV - {self.country_context.name}")
                print("-" * 40)
                print("1. 📂 Buscar por CATEGORÍA")
                print("2. 📁 Buscar por SUBCATEGORÍA")
                
                if self.config.current_brand_mode == self.config.BRAND_MODE_FLAT:
                    print("3. 🏷️ Buscar por MARCA (plano)")
                else:
                    print("3. 🏷️ Buscar por MARCA (jerárquico)")
                
                print("4. 🎯 Buscar por PRODUCTO")
                print("5. 🔄 Cambiar modo de conversión")
                print("6. 📅 Cambiar granularidad de cohortes")
                print("q. 🔙 Volver al menú principal")
                print("-" * 40)
                print(f"⚙️ Modo conversión: {self.config.get_conversion_mode_display()}")
                print(f"📅 Granularidad: {self.config.get_granularity_display()}")
                
                option = input("\n👉 Opción: ").strip().lower()
                
                if option == '1':
                    engine.interactive_search(dimension="category")
                elif option == '2':
                    engine.interactive_search(dimension="subcategory")
                elif option == '3':
                    if self.config.current_brand_mode == self.config.BRAND_MODE_FLAT:
                        engine.interactive_search(dimension="brand")
                    else:
                        engine.interactive_search(dimension="subcategory_brand")
                elif option == '4':
                    engine.interactive_search(dimension="name")
                elif option == '5':
                    if engine.conversion_mode == engine.CONVERSION_CUMULATIVE:
                        engine.set_conversion_mode(engine.CONVERSION_INCREMENTAL)
                    else:
                        engine.set_conversion_mode(engine.CONVERSION_CUMULATIVE)
                    self.config.current_conversion_mode = engine.conversion_mode
                    print(f"\n✅ Modo cambiado a: {self.config.get_conversion_mode_display()}")
                elif option == '6':
                    self._change_granularity_in_query(engine)
                elif option == 'q':
                    break
                else:
                    print("❌ Opción inválida.")
                    
        except Exception as e:
            print(f"\n❌ Error al cargar datos: {e}")
            import traceback
            traceback.print_exc()
            input("\nPresiona Enter para continuar...")
    
    def _change_granularity_in_query(self, engine):
        from Category.Cohort.cohort_config import CohortConfig, TimeGranularity
        from Category.Cohort.cohort_manager import CohortManager
        
        print("\n" + "=" * 50)
        print("   CAMBIAR GRANULARIDAD DE COHORTES".center(50))
        print("=" * 50)
        print(f"Granularidad actual: {self.config.current_granularity}")
        print("\nOpciones:")
        print("   1. Trimestral (quarterly) - DEFAULT")
        print("   2. Mensual (monthly)")
        print("   3. Semanal (weekly)")
        print("   4. Semestral (semiannual)")
        print("   5. Anual (yearly)")
        print("   q. Cancelar")
        
        option = input("\n👉 Opción: ").strip()
        
        granularity_map = {
            '1': 'quarterly',
            '2': 'monthly',
            '3': 'weekly',
            '4': 'semiannual',
            '5': 'yearly',
        }
        
        if option in granularity_map:
            new_granularity = granularity_map[option]
            self.config.current_granularity = new_granularity
            self.config._save_config()
            
            time_map = {
                'quarterly': TimeGranularity.QUARTERLY,
                'monthly': TimeGranularity.MONTHLY,
                'weekly': TimeGranularity.WEEKLY,
                'semiannual': TimeGranularity.SEMIANNUAL,
                'yearly': TimeGranularity.YEARLY,
            }
            
            new_config = CohortConfig(granularity=time_map.get(new_granularity, TimeGranularity.QUARTERLY))
            
            cohort_context = self._get_cohort_context()
            new_cac_map = cohort_context.get_cac_map(granularity=new_granularity)
            
            engine.cohort_config = new_config
            engine.cohort_manager = CohortManager(new_config)
            engine.cac_map = new_cac_map
            
            print(f"✅ Granularidad cambiada a: {new_granularity}")
            input("\nPresiona Enter para continuar...")
    
    def _wait_for_user(self):
        input("\n👉 Presiona Enter para volver al menú principal...")
    
    # ==================================================================
    # MÉTODO PRINCIPAL RUN
    # ==================================================================
    
    def run(self) -> bool:
        # Autenticación con credenciales para el país actual
        if not self.auth.authenticate(self.country_context.code):
            return False
        
        if not self.executor.validate_scripts():
            return False
        
        while True:
            main_option = self.display_main_menu()
            
            if main_option == self.MODE_CHANGE_COUNTRY:
                self._change_country()
                continue
            
            elif main_option == self.MODE_FULL:
                self._run_full_pipeline()
                self._wait_for_user()
                
            elif main_option == self.MODE_DR_ONLY:
                self._run_dr_only()
                self._wait_for_user()
                
            elif main_option == self.MODE_MODEL:
                date_range = self.executor.get_date_range_from_user()
                while True:
                    model_option = self.display_model_submenu()
                    
                    if model_option == self.SUBMODE_MODEL_COMPLETE:
                        self._run_model_complete(date_range)
                        self._wait_for_user()
                    elif model_option == self.SUBMODE_MODEL_GENERAL:
                        self._run_model_general(date_range)
                        self._wait_for_user()
                    elif model_option == self.SUBMODE_CATEGORY:
                        self._run_model_category(date_range)
                        self._wait_for_user()
                    elif model_option == self.SUBMODE_SUBCATEGORY:
                        self._run_model_subcategory(date_range)
                        self._wait_for_user()
                    elif model_option == self.SUBMODE_BRAND:
                        self._run_model_brand(date_range)
                        self._wait_for_user()
                    elif model_option == self.SUBMODE_PRODUCT:
                        self._run_model_product(date_range)
                        self._wait_for_user()
                    elif model_option == self.SUBMODE_SPECIAL:
                        self._run_special_mode(date_range)
                        self._wait_for_user()
                    elif model_option == self.SUBMODE_HEAVY_ONLY:
                        self._run_heavy_analysis_only(date_range)
                        self._wait_for_user()
                    elif model_option == self.MODE_QUIT:
                        break
                    else:
                        print("❌ Opción inválida.")
                        
            elif main_option == self.MODE_QUERY:
                self._run_query_mode()
                
            elif main_option == self.MODE_CONFIG:
                while True:
                    config_option = self.display_config_submenu()
                    if config_option == '1':
                        self._select_grouping_mode()
                    elif config_option == '2':
                        self._select_brand_mode()
                    elif config_option == '3':
                        self._select_granularity()
                    elif config_option == '4':
                        self._select_input_folder()
                    elif config_option == '5':
                        self._select_output_folder()
                    elif config_option == '6':
                        self._manage_cohorts()
                    elif config_option == self.MODE_QUIT:
                        break
                    else:
                        print("❌ Opción inválida")
                        
            elif main_option == self.MODE_QUIT:
                self.executor.ssh_manager.stop()
                print("\n👋 ¡Hasta luego!")
                return True
            else:
                print("❌ Opción inválida")