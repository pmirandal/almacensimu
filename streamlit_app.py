import streamlit as st
import os
import json
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Gestión de Almacén FAMEE",
    page_icon="📦",
    layout="wide"
)

LOGO_URL = "https://raw.githubusercontent.com/pmirandal/almacensimu/b9b5b272dae6ba204d9979c02fe820f0f2981ef6/logo_final.png"

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.image(
        LOGO_URL,
        use_container_width=True
    )

    st.title(
        "Gestión de Almacén FAMEE"
    )

    if st.button(
        "🏠 Inicio",
        use_container_width=True
    ):
        st.session_state.menu = "Inicio"

    if st.button(
        "🔍 Consultar stock",
        use_container_width=True
    ):
        st.session_state.menu = "Consultar stock"

    if st.button(
        "➕ Registrar ingreso",
        use_container_width=True
    ):
        st.session_state.menu = "Registrar ingreso"

    if st.button(
        "➖ Registrar salida",
        use_container_width=True
    ):
        st.session_state.menu = "Registrar salida"

    if st.button(
        "📜 Historial",
        use_container_width=True
    ):
        st.session_state.menu = "Historial"

menu = st.session_state.get(
    "menu",
    "Inicio"
)

# =========================================================
# CONFIG ALMACENES
# =========================================================

ALMACENES = {
    "FAMED": "Almacen_FAMED_2",
    "FAENF": "Almacén FAENF"
}

# =========================================================
# GOOGLE SHEETS
# =========================================================

@st.cache_resource
def conectar_google_sheets(nombre_spreadsheet):

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

    client = gspread.authorize(
        credentials
    )

    spreadsheet = client.open(
        nombre_spreadsheet
    )

    stock_sheet = spreadsheet.worksheet(
        "STOCK"
    )

    in_sheet = spreadsheet.worksheet(
        "IN"
    )

    out_sheet = spreadsheet.worksheet(
        "OUT"
    )

    log_sheet = spreadsheet.worksheet(
        "LOG"
    )

    return (
        stock_sheet,
        in_sheet,
        out_sheet,
        log_sheet
    )

# =========================================================
# FUNCIONES
# =========================================================

def normalizar_codigo(codigo):

    if codigo is None:
        return ""

    return str(codigo).strip().upper()


def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto).strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        c
        for c in texto
        if unicodedata.category(c) != "Mn"
    )

    return texto


def convertir_entero(valor):

    try:
        return int(float(valor))
    except:
        return 0


def obtener_fecha():

    return datetime.now(
        ZoneInfo("America/Lima")
    ).strftime(
        "%d/%m/%Y %H:%M:%S"
    )

# =========================================================
# ALMACÉN
# =========================================================

if "almacen" not in st.session_state:

    st.title(
        "📦 Gestión de Almacén FAMEE"
    )

    st.subheader(
        "Selecciona el almacén"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🏥 FAMED",
            use_container_width=True
        ):

            st.session_state.almacen = (
                "FAMED"
            )

            st.rerun()

    with col2:

        if st.button(
            "🩺 FAENF",
            use_container_width=True
        ):

            st.session_state.almacen = (
                "FAENF"
            )

            st.rerun()

    st.stop()

almacen = st.session_state.almacen

nombre_spreadsheet = ALMACENES[
    almacen
]

# =========================================================
# STOCK
# =========================================================

@st.cache_data(ttl=300)
def obtener_stock(nombre_spreadsheet):

    return stock_sheet.get_all_records()


# =========================================================
# CAMBIAR ALMACÉN
# =========================================================

with st.sidebar:

    st.markdown("---")

    st.markdown(
        """
        <div style="text-align:center; font-size:14px; color:#666;">
            Recuerda que te encuentras en el almacén:
        </div>
        """,
        unsafe_allow_html=True
    )

    if almacen == "FAMED":

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:30px;
                font-weight:bold;
                color:#547BE3;
                margin-top:8px;
                margin-bottom:10px;
            ">
                🏥 FAMED
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:30px;
                font-weight:bold;
                color:#198754;
                margin-top:8px;
                margin-bottom:10px;
            ">
                🩺 FAENF
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button(
        "🔄 Cambiar almacén",
        use_container_width=True
    ):

        del st.session_state["almacen"]

        st.rerun()

try:

    (
        stock_sheet,
        in_sheet,
        out_sheet,
        log_sheet
    ) = conectar_google_sheets(
        nombre_spreadsheet
    )

except Exception as e:

    st.error(
        f"No se pudo conectar al almacén {almacen}"
    )

    st.write(type(e))

    st.code(repr(e))

    raise


# =========================================================
# BUSQUEDA
# =========================================================

def buscar_productos(texto_busqueda):

    texto_busqueda = normalizar_texto(
        texto_busqueda
    )

    registros = obtener_stock(
        nombre_spreadsheet
    )

    resultados = []

    for registro in registros:

        codigo = normalizar_codigo(
            registro.get(
                "COD",
                ""
            )
        )

        item = str(
            registro.get(
                "ITEM",
                ""
            )
        )

        if (
            texto_busqueda
            in normalizar_texto(codigo)
            or texto_busqueda
            in normalizar_texto(item)
        ):

            resultados.append(
                registro
            )

    return resultados

# =========================================================
# SELECTOR ARTICULO
# =========================================================

def selector_articulo():

    texto_busqueda = st.text_input(
        "Buscar por código o artículo",
        placeholder="Ejemplo: 800540007 o mascarilla"
    )

    if not texto_busqueda.strip():

        return None

    resultados = buscar_productos(
        texto_busqueda
    )

    if not resultados:

        st.warning(
            "No se encontraron resultados."
        )

        return None

    opciones = {}
    
    for registro in resultados:

        codigo = registro.get(
            "COD",
            ""
        )

        item = registro.get(
            "ITEM",
            ""
        )

        texto = (
            f"{codigo} — {item}"
        )

        opciones[
            texto
        ] = registro

    seleccion = st.selectbox(
        "Selecciona artículo",
        list(opciones.keys())
    )

    return opciones[
        seleccion
    ]

# =========================================================
# INICIO
# =========================================================

if menu == "Inicio":

    if almacen == "FAMED":

        st.title(
            "🏥 Bienvenido al Almacén FAMED"
        )

    else:

        st.title(
            "🩺 Bienvenido al Almacén FAENF"
        )

    registros = obtener_stock(
            nombre_spreadsheet
        )

    total_articulos = len(
        registros
    )

    con_stock = sum(
        1
        for x in registros
        if convertir_entero(
            x.get("STOCK_F")
        ) > 0
    )

    sin_stock = (
        total_articulos
        - con_stock
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Artículos",
            total_articulos
        )

    with c2:

        st.metric(
            "Con stock",
            con_stock
        )

    with c3:

        st.metric(
            "Sin stock",
            sin_stock
        )

    st.markdown("---")

    st.info(
        f"Almacén seleccionado: {almacen}"
    )

    st.markdown("---")

    st.warning(
        """
    ¿Registraste un ingreso o salida por error?

    Si necesitas corregir movimientos del almacén,
    contacta a soporte.
    """
    )

    st.link_button(
        "🚨 Contactar soporte por WhatsApp 🚨",
        "https://wa.link/0ihfly",
        use_container_width=True
    )

# =========================================================
# CONSULTAR STOCK
# =========================================================

elif menu == "Consultar stock":

    st.header(
        "Consultar stock"
    )

    producto = selector_articulo()

    if producto is not None:

        codigo_real = normalizar_codigo(
            producto.get("COD", "")
        )

        item = str(
            producto.get("ITEM", "")
        ).strip()

        ubicacion = str(
            producto.get("UBIC", "")
        ).strip()

        stock_final = convertir_entero(
            producto.get("STOCK_F")
        )

        st.success(
            "Artículo encontrado"
        )

        st.write(
            f"**Código:** {codigo_real}"
        )

        st.write(
            f"**Artículo:** {item}"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "📦 STOCK ACTUAL",
                stock_final
            )

        with col2:

            st.metric(
                "📍 UBICACIÓN",
                ubicacion
            )

# =========================================================
# REGISTRAR INGRESO
# =========================================================

elif menu == "Registrar ingreso":

    st.header(
        "Registrar ingreso"
    )

    producto = selector_articulo()

    if producto is not None:

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

        cantidad = st.number_input(
            "Cantidad a ingresar",
            min_value=1,
            step=1,
            value=1
        )

        motivo = st.selectbox(
            "Seleccionar motivo",
            [
                "Por pedido",
                "Transferencia de FAMED",
                "Transferencia de FAENF",
                "Otro motivo"
            ]
        )

        responsable = st.selectbox(
            "Responsable",
            [
                "Serafina👑",
                "Olga👑",
                "Carolay",
                "Fabritcio",
                "Jackelyn",
                "Marianela",
                "Veya",
                "Yamille",
                "Ygnacio",
                "Yenny"
            ]
        )

        if st.button(
            "Registrar ingreso",
            use_container_width=True
        ):

            fecha = obtener_fecha()

            nueva_fila = [
                fecha,
                codigo_real,
                item,
                cantidad,
                motivo,
                responsable
            ]

            try:

                stock_resultante = (
                    stock_actual + cantidad
                )

                in_sheet.append_row(
                    nueva_fila,
                    value_input_option="USER_ENTERED"
                )

                log_sheet.append_row(
                    [
                        fecha,
                        codigo_real,
                        item,
                        "INGRESO",
                        cantidad,
                        motivo,
                        responsable,
                        stock_resultante
                    ],
                    value_input_option="USER_ENTERED"
                )

                obtener_stock.clear()

                st.success(
                    "✅ Ingreso registrado correctamente."
                )

            except Exception as e:

                st.error(
                    "❌ Error registrando ingreso."
                )

                st.code(
                    str(e)
                )

# =========================================================
# REGISTRAR SALIDA
# =========================================================

elif menu == "Registrar salida":

    st.header(
        "Registrar salida"
    )

    st.warning(
        """
    Verificar que el item esté categorizado según unidad (UND) o según caja antes de retirar.

    Recuerde que no pueden abrirse cajas selladas dentro del almacén.
    """
    )

    producto = selector_articulo()

    if producto is not None:

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

        if stock_actual <= 0:

            st.error(
                "❌ Este artículo no tiene stock disponible."
            )

        else:

            cantidad = st.number_input(
                "Cantidad a retirar",
                min_value=1,
                max_value=stock_actual,
                step=1,
                value=1
            )

            motivo = st.selectbox(
                "Seleccionar motivo",
                [
                    "Consumo interno",
                    "Transferencia a FAMED",
                    "Transferencia a FAENF",
                    "Otro motivo"
                ]
            )

            responsable = st.selectbox(
                "Responsable",
                [
                    "Serafina👑",
                    "Olga👑",
                    "Carolay",
                    "Fabritcio",
                    "Jackelyn",
                    "Marianela",
                    "Veya",
                    "Yamille",
                    "Ygnacio",
                    "Yenny"                    
                ]
            )

            if st.button(
                "Registrar salida",
                use_container_width=True
            ):

                fecha = obtener_fecha()

                stock_resultante = (
                    stock_actual - cantidad
                )

                nueva_fila = [
                    fecha,
                    codigo_real,
                    item,
                    cantidad,
                    motivo,
                    responsable
                ]

                try:

                    out_sheet.append_row(
                        nueva_fila,
                        value_input_option="USER_ENTERED"
                    )

                    log_sheet.append_row(
                        [
                            fecha,
                            codigo_real,
                            item,
                            "SALIDA",
                            cantidad,
                            motivo,
                            responsable,
                            stock_resultante
                        ],
                        value_input_option="USER_ENTERED"
                    )

                    obtener_stock.clear()

                    st.success(
                        "✅ Salida registrada correctamente."
                    )

                except Exception as e:

                    st.error(
                        "❌ Error registrando salida."
                    )

                    st.code(
                        str(e)
                    )

# =========================================================
# HISTORIAL
# =========================================================

elif menu == "Historial":

    st.header(
        "Historial de movimientos"
    )

    movimientos = (
        log_sheet.get_all_records()
    )

    st.dataframe(
        movimientos,
        use_container_width=True,
        hide_index=True
    )