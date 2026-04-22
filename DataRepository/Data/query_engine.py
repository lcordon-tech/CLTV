import pandas as pd
from sqlalchemy import create_engine

class QueryEngine:
    """
    Responsabilidad: Gestionar la conexión a MySQL y extraer la data 
    cruda de órdenes aplicando la lógica de negocio de Pacifiko.
    """
    
    def __init__(self, user, password, host, db):
        self.engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{db}")
        
        # Query parametrizada (sin fechas hardcodeadas)
        self.LTV_QUERY = """
            WITH order_base AS (  
                SELECT
                    o1.payment_code,
                    o1.shipping_method,
                    o1.order_id,
                    o1.parent_order_id,
                    o1.order_status_id,
                    o1.customer_id,
                    o1.bank
                FROM db_pacifiko.oc_order o1
                WHERE o1.parent_order_id IS NULL OR o1.parent_order_id != 0
            ),
            fecha_real AS (
                SELECT
                    order_id,
                    MIN(date_added) AS fecha_colocada
                FROM db_pacifiko.oc_order_history
                WHERE order_status_id IN (1, 2, 13)
                GROUP BY 1
            ),
            product_ref AS (      
                SELECT DISTINCT
                    p.product_id,
                    p.product_pid,
                    p.cost
                FROM db_pacifiko.oc_product p
                WHERE p.product_merchant_code = 'PAC1'
                OR (p.product_merchant_code = '' AND p.product_merchant_type = 'S')
            ),
            order_status_desc AS (
                SELECT DISTINCT
                    os.order_status_id,
                    os.name AS order_status_name
                FROM db_pacifiko.oc_order_status os
                WHERE os.language_id = 2
            ),
            vendor_commission_dedup AS (
                SELECT
                    pvc.order_id,
                    pvc.product_id,
                    MAX(pvc.commission_percent) AS commission_percent
                FROM db_pacifiko.oc_purpletree_vendor_commissions pvc
                GROUP BY pvc.order_id, pvc.product_id
            )
            SELECT
                fr.fecha_colocada,
                ob.customer_id,
                ob.payment_code,
                ob.shipping_method,
                op.order_id,
                op.product_id,
                pr.product_pid,
                op.quantity,
                op.cost AS cost_order_table,
                op.price,
                pr.cost AS cost_product_table,
                CASE
                    WHEN op.cost IS NOT NULL AND op.cost > 0 THEN op.cost
                    ELSE pr.cost
                END AS cost_item,
                ob.bank,
                osd.order_status_name,
                COALESCE(vcd.commission_percent, 0) AS commission_percent
            FROM db_pacifiko.oc_order_product op
            JOIN order_base ob ON ob.order_id = op.order_id
            LEFT JOIN fecha_real fr ON fr.order_id = ob.order_id
            LEFT JOIN product_ref pr ON pr.product_id = op.product_id
            JOIN order_status_desc osd ON osd.order_status_id = ob.order_status_id
            LEFT JOIN vendor_commission_dedup vcd ON vcd.order_id = op.order_id 
                AND vcd.product_id = op.product_id
            WHERE ob.order_status_id IN (1, 2, 3, 5, 9, 14, 15, 17, 18, 19, 20, 21, 29, 30, 34, 50)
            AND op.order_product_status_id NOT IN (9, 15, 2, 4, 19, 33, 35, 36, 37, 38, 39, 43, 44, 45)
            AND fr.fecha_colocada BETWEEN %(start_date)s AND %(end_date)s
            ORDER BY fr.fecha_colocada ASC;
        """

    def fetch_orders(self, start_date=None, end_date=None) -> pd.DataFrame:
        """
        Ejecuta la conexión y descarga la data en un DataFrame.
        
        Args:
            start_date: datetime o str 'YYYY-MM-DD' (filtro inicio)
            end_date: datetime o str 'YYYY-MM-DD' (filtro fin)
        """
        try:
            # Valores por defecto (comportamiento original)
            if start_date is None:
                start_date = '2020-01-01'
            if end_date is None:
                end_date = '2030-12-31'  # Futuro extensible
            
            # Convertir a string si es datetime
            if hasattr(start_date, 'strftime'):
                start_date = start_date.strftime('%Y-%m-%d')
            if hasattr(end_date, 'strftime'):
                end_date = end_date.strftime('%Y-%m-%d')
            
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
            
            print(f"🔍 Conectando a la Base de Datos...")
            print(f"📅 Rango consultado: {start_date} → {end_date}")
            df = pd.read_sql(self.LTV_QUERY, self.engine, params=params)
            
            if df.empty:
                print("⚠️ La consulta se ejecutó pero no devolvió filas.")
                return pd.DataFrame()
            
            print(f"✅ Descarga exitosa: {len(df)} filas obtenidas.")
            return df
        except Exception as e:
            print(f"❌ Error crítico en QueryEngine: {e}")
            return pd.DataFrame()