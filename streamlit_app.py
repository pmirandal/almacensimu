import streamlit as st
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Control de Almacén FAMED",
    page_icon="📦",
    layout="centered"
)


# =========================================================
# ESTILOS
# =========================================================

st.markdown(
    """
    <style>

        .main {
            max-width: 900px;
            margin: auto;
        }

        h1 {
            text-align: center;
        }

        .subtitulo {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# CONEXIÓN CON GOOGLE SHEETS
# =========================================================

@st.cache_resource
def conectar_google_sheets():

    credentials_info = json.loads(
        os.environ["GOOGLE_CREDENTIALS"]
    )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        credentials_info,
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open(
        "Almacén FAMED"
    )

    stock_sheet = spreadsheet.worksheet("STOCK")
    in_sheet = spreadsheet.worksheet("IN")
    out_sheet = spreadsheet.worksheet("OUT")

    return stock_sheet, in_sheet, out_sheet


# =========================================================
# CONECTAR
# =========================================================

try:

    stock_sheet, in_sheet, out_sheet = (
        conectar_google_sheets()
    )

except Exception as e:

    st.error(
        "No se pudo conectar con Google Sheets."
    )

    st.code(str(e))

    st.stop()


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def normalizar_codigo(codigo):
    """
    Los códigos ahora son alfanuméricos.

    Ejemplos:

        m0001  -> M0001
        M0001  -> M0001
        M0002  -> M0002

    No convierte el código a número.
    """

    if codigo is None:
        return ""

    return str(codigo).strip().upper()


def convertir_entero(valor):
    """
    Convierte valores numéricos de Google Sheets.

    Si la celda está vacía devuelve 0.
    """

    if valor is None:
        return 0

    valor = str(valor).strip()

    if valor == "":
        return 0

    try:
        return int(float(valor))

    except (ValueError, TypeError):
        return 0


# =========================================================
# OBTENER STOCK
# =========================================================

@st.cache_data(ttl=10)
def obtener_stock():

    return stock_sheet.get_all_records()


# =========================================================
# BUSCAR PRODUCTO
# =========================================================

def buscar_producto(codigo):

    codigo_buscado = normalizar_codigo(codigo)

    if not codigo_buscado:
        return None

    registros = obtener_stock()

    for registro in registros:

        codigo_registro = normalizar_codigo(
            registro.get("COD", "")
        )

        if codigo_registro == codigo_buscado:

            return registro

    return None


# =========================================================
# BUSCAR FILA EN STOCK
# =========================================================

def buscar_fila_stock(codigo):

    codigo_buscado = normalizar_codigo(codigo)

    registros = stock_sheet.get_all_records()

    for numero_fila, registro in enumerate(
        registros,
        start=2
    ):

        codigo_registro = normalizar_codigo(
            registro.get("COD", "")
        )

        if codigo_registro == codigo_buscado:

            return numero_fila, registro

    return None, None


# =========================================================
# ENCABEZADO
# =========================================================

st.title("📦 Control de Almacén FAMED")

st.markdown(
    '<p class="subtitulo">'
    'Control de stock, ingresos y salidas'
    '</p>',
    unsafe_allow_html=True
)


# =========================================================
# MENÚ PRINCIPAL
# =========================================================

opcion = st.radio(
    "Selecciona una opción",
    [
        "🔎 Consultar stock",
        "➕ Registrar ingreso",
        "➖ Registrar salida"
    ],
    horizontal=True
)


# =========================================================
# CONSULTAR STOCK
# =========================================================

if opcion == "🔎 Consultar stock":

    st.subheader("Consultar stock")

    codigo = st.text_input(
        "Código del artículo",
        placeholder="Ej. M0001",
        max_chars=10
    )

    consultar = st.button(
        "Consultar",
        use_container_width=True
    )

    if consultar:

        codigo = normalizar_codigo(codigo)

        if not codigo:

            st.warning(
                "Por favor, ingresa un código."
            )

            st.stop()

        producto = buscar_producto(codigo)

        if producto is None:

            st.error(
                f"❌ No se encontró el código "
                f"{codigo}."
            )

        else:

            codigo_real = normalizar_codigo(
                producto.get("COD", "")
            )

            item = str(
                producto.get("ITEM", "")
            ).strip()

            ubicacion = str(
                producto.get("UBIC", "")
            ).strip()

            stock_n = convertir_entero(
                producto.get("STOCK_N")
            )

            ingresos = convertir_entero(
                producto.get("IN")
            )

            salidas = convertir_entero(
                producto.get("OUT")
            )

            stock_final = convertir_entero(
                producto.get("STOCK_F")
            )

            st.success(
                "Artículo encontrado"
            )

            st.markdown("---")

            st.write(
                f"**Código:** {codigo_real}"
            )

            st.write(
                f"**Artículo:** {item}"
            )

            st.write(
                f"**Ubicación:** {ubicacion}"
            )

            st.markdown("---")

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Stock inicial",
                    stock_n
                )

            with col2:

                st.metric(
                    "Ingresos",
                    ingresos
                )

            with col3:

                st.metric(
                    "Salidas",
                    salidas
                )

            st.markdown("---")

            st.metric(
                "📦 STOCK ACTUAL",
                stock_final
            )


# =========================================================
# REGISTRAR INGRESO
# =========================================================

elif opcion == "➕ Registrar ingreso":

    st.subheader("Registrar ingreso")

    codigo = st.text_input(
        "Código del artículo",
        placeholder="Ej. M0001",
        max_chars=10
    )

    codigo = normalizar_codigo(codigo)

    if codigo:

        producto = buscar_producto(codigo)

        if producto is None:

            st.error(
                f"❌ No se encontró el código "
                f"{codigo}."
            )

        else:

            codigo_real = normalizar_codigo(
                producto.get("COD", "")
            )

            item = str(
                producto.get("ITEM", "")
            ).strip()

            ubicacion = str(
                producto.get("UBIC", "")
            ).strip()

            stock_actual = convertir_entero(
                producto.get("STOCK_F")
            )

            st.info(
                f"**{codigo_real} — {item}**"
            )

            st.write(
                f"Ubicación: **{ubicacion}**"
            )

            st.metric(
                "📦 Stock actual",
                stock_actual
            )

            st.markdown("---")

            cantidad = st.number_input(
                "Cantidad a ingresar",
                min_value=1,
                step=1,
                value=1
            )

            destino = st.selectbox(
                "Destino",
                [
                    "FAEST",
                    "FAMED",
                    "FAENF",
                    "Otro"
                ]
            )

            registrar = st.button(
                "➕ Registrar ingreso",
                use_container_width=True
            )

            if registrar:

                cantidad = int(cantidad)

                # -----------------------------------------
                # DATOS DEL MOVIMIENTO
                # -----------------------------------------

                fecha = datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                )

                nueva_fila = [
                    fecha,
                    codigo_real,
                    item,
                    cantidad,
                    destino,
                    cantidad
                ]

                try:

                    # -------------------------------------
                    # REGISTRAR EN HOJA IN
                    # -------------------------------------

                    in_sheet.append_row(
                        nueva_fila,
                        value_input_option="USER_ENTERED"
                    )

                    # -------------------------------------
                    # LIMPIAR CACHÉ
                    # -------------------------------------

                    obtener_stock.clear()

                    st.success(
                        "✅ Ingreso registrado correctamente."
                    )

                    st.info(
                        f"**Fecha y hora:** {fecha}\n\n"
                        f"**Artículo:** {item}\n\n"
                        f"**Código:** {codigo_real}\n\n"
                        f"**Cantidad retirada:** {cantidad}\n\n"
                        f"**Destino:** {destino}"
                    )

                    #st.rerun()

                except Exception as e:

                    st.error(
                        "❌ Ocurrió un error al registrar "
                        "el ingreso."
                    )

                    st.code(str(e))


# =========================================================
# REGISTRAR SALIDA
# =========================================================

elif opcion == "➖ Registrar salida":

    st.subheader("Registrar salida")

    codigo = st.text_input(
        "Código del artículo",
        placeholder="Ej. M0001",
        max_chars=10
    )

    codigo = normalizar_codigo(codigo)

    if codigo:

        producto = buscar_producto(codigo)

        if producto is None:

            st.error(
                f"❌ No se encontró el código "
                f"{codigo}."
            )

        else:

            codigo_real = normalizar_codigo(
                producto.get("COD", "")
            )

            item = str(
                producto.get("ITEM", "")
            ).strip()

            ubicacion = str(
                producto.get("UBIC", "")
            ).strip()

            stock_actual = convertir_entero(
                producto.get("STOCK_F")
            )

            st.info(
                f"**{codigo_real} — {item}**"
            )

            st.write(
                f"Ubicación: **{ubicacion}**"
            )

            st.metric(
                "📦 Stock disponible",
                stock_actual
            )

            st.markdown("---")

            if stock_actual <= 0:

                st.error(
                    "❌ Este artículo no tiene "
                    "stock disponible."
                )

            else:

                cantidad = st.number_input(
                    "Cantidad a retirar",
                    min_value=1,
                    max_value=stock_actual,
                    step=1,
                    value=1
                )

                destino = st.selectbox(
                    "Destino",
                    [
                        "FAEST",
                        "FAMED",
                        "FAENF",
                        "Otro"
                    ]
                )

                registrar = st.button(
                    "➖ Registrar salida",
                    use_container_width=True
                )

                if registrar:

                    cantidad = int(cantidad)

                    # -------------------------------------
                    # VOLVER A LEER STOCK REAL
                    # -------------------------------------

                    fila_stock, registro_actual = (
                        buscar_fila_stock(codigo_real)
                    )

                    if fila_stock is None:

                        st.error(
                            "❌ No se encontró el artículo "
                            "en la hoja STOCK."
                        )

                        st.stop()

                    # -------------------------------------
                    # LEER STOCK_F ACTUAL
                    # -------------------------------------

                    stock_actual_real = convertir_entero(
                        registro_actual.get("STOCK_F")
                    )

                    # -------------------------------------
                    # VALIDAR STOCK
                    # -------------------------------------

                    if cantidad > stock_actual_real:

                        st.error(
                            "❌ Stock insuficiente."
                        )

                        st.warning(
                            f"Stock disponible actualmente: "
                            f"**{stock_actual_real}**"
                        )

                        st.stop()

                    # -------------------------------------
                    # DATOS DEL MOVIMIENTO
                    # -------------------------------------

                    fecha = datetime.now(
                        ZoneInfo("America/Lima")
                    ).strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )

                    nueva_fila = [
                        fecha,
                        codigo_real,
                        item,
                        cantidad,
                        destino,
                        cantidad
                    ]

                    try:

                        # ---------------------------------
                        # REGISTRAR EN HOJA OUT
                        # ---------------------------------

                        out_sheet.append_row(
                            nueva_fila,
                            value_input_option="USER_ENTERED"
                        )

                        # ---------------------------------
                        # LIMPIAR CACHÉ
                        # ---------------------------------

                        obtener_stock.clear()

                        st.success(
                            "✅ Salida registrada correctamente."
                        )

                        st.info(
                            f"**Fecha y hora:** {fecha}\n\n"
                            f"**Artículo:** {item}\n\n"
                            f"**Código:** {codigo_real}\n\n"
                            f"**Cantidad retirada:** {cantidad}\n\n"
                            f"**Destino:** {destino}"
                        )               

                        #st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ Ocurrió un error al registrar "
                            "la salida."
                        )

                        st.code(str(e))