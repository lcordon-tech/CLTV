#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema LTV Pacifiko v6.0 - MULTI-PAÍS
Entry point principal con selector de país al inicio.
"""

import sys
import os
import traceback
from pathlib import Path

# Configurar path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Run.Config.paths import Paths
from Run.Config.credentials import Credentials
from Run.Country.country_loader import CountryLoader
from Run.Country.country_selector import CountrySelector
from Run.Country.country_context import CountryContext
from Run.FX.fx_engine import FXEngine
from Run.Menu.menu_controller import MenuController
from Run.Utils.logger import SystemLogger


def main():
    """Punto de entrada principal - MULTI-PAÍS"""
    logger = SystemLogger()
    logger.info("=" * 60)
    logger.info("INICIANDO SISTEMA LTV v6.0 - MULTI-PAÍS")
    logger.info("=" * 60)
    
    try:
        # ========== 1. SELECCIONAR PAÍS ==========
        selector = CountrySelector()
        
        if not selector.has_countries():
            print("❌ No hay configuraciones de países disponibles")
            sys.exit(1)
        
        country_code = selector.select()
        country_config = CountryLoader.load_country(country_code)
        
        if not country_config:
            print(f"❌ Error cargando configuración para {country_code}")
            sys.exit(1)
        
        # Guardar en variable de entorno
        os.environ["LTV_COUNTRY"] = country_config.code
        os.environ["LTV_COUNTRY_START_DATE"] = str(country_config.cohort_start_year)
        os.environ["LTV_COUNTRY_END_DATE"] = str(country_config.cohort_end_year)
        os.environ["LTV_DEFAULT_FX_RATE"] = str(country_config.default_fx_rate)
        
        print(f"\n🌎 País seleccionado: {country_config.name} ({country_config.code})")
        print(f"📅 Cohortes desde: {country_config.cohort_start_year}")
        print(f"💱 Moneda: {country_config.currency} | FX default: {country_config.default_fx_rate}")
        
        # ========== 2. CARGAR CREDENCIALES DEL PAÍS ==========
        if not Credentials.load_for_country(country_config.code):
            logger.warning(f"No se encontraron credenciales para {country_config.code}")
            print(f"\n⚠️ No hay credenciales configuradas para {country_config.name}")
            print("   Por favor, configura las credenciales primero.")
            
            from Run.Menu.menu_auth import MenuAuth
            from Run.Config.vault_manager import VaultManager
            from Run.Config.dev_mode_manager import DevModeManager
            
            vault = VaultManager()
            dev_mode = DevModeManager()
            auth = MenuAuth(vault, dev_mode, logger)
            auth.set_country(country_config.code)
            
            if auth.setup_new_user(country_config.code):
                Credentials.load_for_country(country_config.code)
            else:
                print("❌ No se pudo configurar el usuario. Saliendo...")
                sys.exit(1)
        
        # ========== 3. CONFIGURAR RUTAS ==========
        paths = Paths.get_production_paths(country_config.code)
        logger.info(f"📂 Directorio base: {paths.base_path}")
        logger.info(f"📂 Inputs: {paths.inputs_dir}")
        
        # ========== 4. CREAR CONTEXTO DE PAÍS ==========
        country_context = CountryContext(
            code=country_config.code,
            name=country_config.name,
            currency=country_config.currency,
            default_fx_rate=country_config.default_fx_rate,
            cohort_start_year=country_config.cohort_start_year,
            cohort_end_year=country_config.cohort_end_year
        )
        
        # ========== 5. INICIALIZAR FX ENGINE ==========
        fx_path = paths.inputs_dir / paths.fx_file
        fx_engine = FXEngine(country_context, fx_path)
        
        # ========== 6. CREAR CONTROLADOR Y EJECUTAR ==========
        # ⭐ AHORA CON 3 ARGUMENTOS: paths, country_context, fx_engine
        controller = MenuController(paths, country_context, fx_engine)
        success = controller.run()
        
        logger.info(f"Sistema finalizado con código: {0 if success else 1}")
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Sistema interrumpido por el usuario")
        logger.info("KeyboardInterrupt - sistema detenido")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        logger.error(f"Error fatal: {e}", exc_info=True)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()