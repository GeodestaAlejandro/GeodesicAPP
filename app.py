from __future__ import annotations

import math
from dataclasses import dataclass
import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import hmac

# =========================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (FRONTEND AMIGABLE)
# =========================================================
st.set_page_config(
    page_title="Geodesia Lab | Plataforma Geodésica",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS corregidos para evitar conflictos de color en el sidebar
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    h1, h2, h3 { color: #0f172a !important; font-family: 'Inter', -apple-system, sans-serif; font-weight: 700; }
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: white; padding: 1.8rem; border-radius: 12px; margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 { color: #ffffff !important; margin: 0; font-size: 2.2rem; }
    .main-header p { color: #94a3b8; margin: 0.4rem 0 0 0; font-size: 1rem; }
    div[data-testid="stMetric"] {
        background-color: #ffffff; border: 1px solid #e2e8f0; padding: 1rem 1.2rem;
        border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetric"] label { color: #64748b !important; font-weight: 600; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #0284c7 !important; font-weight: 700; }
    .stButton > button {
        background: #0284c7; color: white; border-radius: 8px; border: none;
        padding: 0.5rem 1.2rem; font-weight: 600; transition: all 0.2s ease; width: 100%;
    }
    .stButton > button:hover { background: #0369a1; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25); }
    
    /* Corrección de visibilidad en el Sidebar sin afectar menús desplegables */
    section[data-testid="stSidebar"] { background-color: #0f172a; }
    section[data-testid="stSidebar"] .stMarkdown p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label { color: #f1f5f9 !important; }
</style>
""", unsafe_allow_html=True)


# =========================
# 2. AUTENTICACIÓN
# =========================
def require_login():
    if st.session_state.get("authenticated", True):
        return

    st.markdown("""
        <div style="max-width: 450px; margin: 80px auto; padding: 30px; background: white; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);">
            <h2 style="text-align: center; margin-bottom: 8px;">🔐 Acceso Privado</h2>
            <p style="text-align: center; color: #64748b; font-size: 0.95rem; margin-bottom: 24px;">Ingresa tus credenciales para acceder al laboratorio geodésico.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Usuario").strip()
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar Sesión")

    if submitted:
        users_section = st.secrets.get("users", {})
        users = {str(k): str(v) for k, v in dict(users_section).items()}
        valid_password = users.get(username)

        if isinstance(valid_password, str) and hmac.compare_digest(password, valid_password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("⚠️ Usuario o contraseña incorrectos.")

    st.stop()

# require_login()  # Descomenta si usas st.secrets


# =========================
# 3. BASE DE DATOS Y MODELO
# =========================
ELLIPSOIDS = {
    "WGS84": {"a": 6378137.0, "b": 6356752.314245},
    "GRS80": {"a": 6378137.0, "b": 6356752.314140},
    "WGS72": {"a": 6378135.0, "b": 6356750.520016},
    "Clarke1866": {"a": 6378206.4, "b": 6356583.8},
    "Clarke1880": {"a": 6378249.145, "b": 6356514.86955},
    "International1924": {"a": 6378388.0, "b": 6356911.946},
    "Airy1830": {"a": 6377563.396, "b": 6356256.909},
    "Bessel1841": {"a": 6377397.155, "b": 6356078.963},
    "Krassovsky1940": {"a": 6378245.0, "b": 6356863.019},
    "Everest1830": {"a": 6377276.345, "b": 6356075.413}
}

MARGIN_HEIGHT = 10000.0

@dataclass(frozen=True)
class Ellipsoid:
    name: str
    a: float
    b: float

    @property
    def f(self) -> float: return (self.a - self.b) / self.a

    @property
    def inv_f(self) -> float:
        f = self.f
        return float("inf") if abs(f) < 1e-18 else 1.0 / f

    @property
    def e2(self) -> float: return (self.a**2 - self.b**2) / self.a**2

    @property
    def ep2(self) -> float: return (self.a**2 - self.b**2) / self.b**2

    @property
    def limit_xy(self) -> float: return self.a + MARGIN_HEIGHT

    @property
    def limit_z(self) -> float: return self.b + MARGIN_HEIGHT

def get_ellipsoid(name: str) -> Ellipsoid:
    data = ELLIPSOIDS[name]
    return Ellipsoid(name=name, a=float(data["a"]), b=float(data["b"]))


# =========================
# 4. VALIDACIONES Y NÚCLEO
# =========================
EPS = 1e-15

def deg_to_rad(v: float) -> float: return math.radians(v)
def rad_to_deg(v: float) -> float: return math.degrees(v)

def prime_vertical_radius(lat_rad: float, ell: Ellipsoid) -> float:
    s = math.sin(lat_rad)
    return ell.a / math.sqrt(1.0 - ell.e2 * s * s)

def meridian_radius(lat_rad: float, ell: Ellipsoid) -> float:
    s = math.sin(lat_rad)
    return ell.a * (1.0 - ell.e2) / ((1.0 - ell.e2 * s * s) ** 1.5)

def trapezoidal_integral(x_values, y_values) -> float:
    total = 0.0
    for i in range(len(x_values) - 1):
        dx = x_values[i + 1] - x_values[i]
        total += 0.5 * (y_values[i] + y_values[i + 1]) * dx
    return float(total)

def meridian_arc_between(lat1_deg: float, lat2_deg: float, ell: Ellipsoid, n: int = 4000) -> float:
    phi1, phi2 = deg_to_rad(lat1_deg), deg_to_rad(lat2_deg)
    phis = np.linspace(phi1, phi2, n)
    values = np.array([meridian_radius(phi, ell) for phi in phis], dtype=float)
    return abs(trapezoidal_integral(phis, values))

def geodetic_quadrilateral(lat1_deg: float, lon1_deg: float, lat2_deg: float, lon2_deg: float, ell: Ellipsoid) -> dict:
    south, north = min(lat1_deg, lat2_deg), max(lat1_deg, lat2_deg)
    west, east = min(lon1_deg, lon2_deg), max(lon1_deg, lon2_deg)
    
    s_rad, n_rad = deg_to_rad(south), deg_to_rad(north)
    dlon = deg_to_rad(east - west)

    s_par = prime_vertical_radius(s_rad, ell) * math.cos(s_rad) * dlon
    n_par = prime_vertical_radius(n_rad, ell) * math.cos(n_rad) * dlon
    m_len = meridian_arc_between(south, north, ell)

    phis = np.linspace(s_rad, n_rad, 2000)
    integrand = np.array([meridian_radius(phi, ell) * prime_vertical_radius(phi, ell) * math.cos(phi) for phi in phis])
    area_m2 = abs(dlon * trapezoidal_integral(phis, integrand))

    return {
        "south_parallel_length": s_par,
        "north_parallel_length": n_par,
        "west_meridian_length": m_len,
        "east_meridian_length": m_len,
        "area_m2": area_m2,
        "area_km2": area_m2 / 1e6,
        "vertices": [
            {"lat": south, "lon": west}, {"lat": south, "lon": east},
            {"lat": north, "lon": east}, {"lat": north, "lon": west},
            {"lat": south, "lon": west}
        ]
    }


# =========================
# 5. CÁLCULOS TOPOGRÁFICOS (TRISECCIÓN Y BISECCIÓN)
# =========================
def resolver_triseccion_tienstra(ea, na, eb, nb, ec, nc, alpha, beta, gamma):
    """Método de Tienstra para Trisección (Resección)[cite: 1]"""
    def ang(e1, n1, e2, n2, e3, n3):
        a2 = (e3-e2)**2 + (n3-n2)**2
        b2 = (e1-e3)**2 + (n1-n3)**2
        c2 = (e2-e1)**2 + (n2-n1)**2
        if a2 == 0 or b2 == 0 or c2 == 0: return 0
        return math.acos(max(-1.0, min(1.0, (b2 + c2 - a2) / (2 * math.sqrt(b2) * math.sqrt(c2)))))

    A = ang(ea, na, eb, nb, ec, nc)
    B = ang(eb, nb, ec, nc, ea, na)
    C = ang(ec, nc, ea, na, eb, nb)

    try:
        wA = 1.0 / (1.0/math.tan(A) - 1.0/math.tan(math.radians(alpha)))
        wB = 1.0 / (1.0/math.tan(B) - 1.0/math.tan(math.radians(beta)))
        wC = 1.0 / (1.0/math.tan(C) - 1.0/math.tan(math.radians(gamma)))
        
        sum_w = wA + wB + wC
        ep = (wA * ea + wB * eb + wC * ec) / sum_w
        np_coord = (wA * na + wB * nb + wC * nc) / sum_w
        return ep, np_coord
    except:
        return None, None

def resolver_biseccion(ea, na, eb, nb, alpha_deg, beta_deg):
    """Método de Bisección (Intersección directa desde dos estaciones A y B)"""
    dE = eb - ea
    dN = nb - na
    az_ab = math.atan2(dE, dN)
    d_ab = math.hypot(dE, dN)
    
    if d_ab == 0:
        return None, None

    alpha = math.radians(alpha_deg)
    beta = math.radians(beta_deg)

    sum_ang = alpha + beta
    if abs(math.sin(sum_ang)) < 1e-6:
        return None, None

    dist_ap = d_ab * math.sin(beta) / math.sin(sum_ang)
    az_ap = az_ab + alpha

    ep = ea + dist_ap * math.sin(az_ap)
    np_coord = na + dist_ap * math.cos(az_ap)
    return ep, np_coord


# =========================
# 6. FIGURAS PLOTLY REFINADAS
# =========================
def fig_meridian_ellipse(ell: Ellipsoid) -> go.Figure:
    t = np.linspace(0, 2 * math.pi, 360)
    x, z = ell.a * np.cos(t), ell.b * np.sin(t)
    fig = go.Figure(go.Scatter(x=x, y=z, mode="lines", line=dict(color="#0284c7", width=3), name="Elipse"))
    fig.update_layout(
        title=f"Elipse Meridiana - {ell.name}",
        xaxis_title="Eje X (m)", yaxis_title="Eje Z (m)",
        template="plotly_white", height=450,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def fig_mapa_2d(pts_dict, title="Mapa 2D"):
    fig = go.Figure()
    for name, coords in pts_dict.items():
        if coords[0] is not None:
            color = "#ef4444" if "Calculado" in name else "#0f172a"
            fig.add_trace(go.Scatter(x=[coords[0]], y=[coords[1]], mode="markers+text", 
                                     marker=dict(size=12, color=color), text=[name], textposition="top center", name=name))
    fig.update_layout(title=title, template="plotly_white", xaxis_title="Este (E)", yaxis_title="Norte (N)", height=500)
    return fig

def fig_perfil_elevacion(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Distancia_Acumulada'], y=df['Cota_Ajustada'], mode='lines+markers',
                             line=dict(color="#10b981", width=3), marker=dict(size=8, color="#065f46"), name="Perfil del Terreno"))
    fig.update_layout(title="Perfil de Nivelación Geodésica", xaxis_title="Distancia Acumulada (m)",
                      yaxis_title="Cota (m.s.n.m.)", template="plotly_white", height=450)
    return fig


# =========================
# 7. NAVEGACIÓN Y ESTRUCTURA DE LA APP
# =========================

st.markdown("""
<div class="main-header">
    <h1>🌍 Geodesia Lab</h1>
    <p>Plataforma interactiva para cálculos, transformaciones espaciales y geometría elipsoidal.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuración Global")
    ellipsoid_name = st.selectbox("Elipsoide de referencia:", list(ELLIPSOIDS.keys()), index=0)
    ell = get_ellipsoid(ellipsoid_name)

    st.markdown("---")
    st.markdown("### 📌 Módulos de Cálculo")
    module = st.radio(
        "Selecciona un módulo:",
        [
            "1. Parámetros del Elipsoide",
            "2. Elipse Meridiana",
            "3. Geodésicas → Cartesianas (ECEF)",
            "4. Cartesianas (ECEF) → Geodésicas",
            "5. Arco de Paralelo",
            "6. Cuadrilátero Geodésico y Área",
            "7. Trisección y Bisección",
            "8. Nivelación Diferencial Geodésica"
        ]
    )

    st.markdown("---")
    st.caption(f"👤 **Usuario:** `{st.session_state.get('username', 'Demo')}`")


# =========================
# CONTENIDO POR MÓDULOS
# =========================

if module == "1. Parámetros del Elipsoide":
    st.subheader("📐 Geometría del Elipsoide Seleccionado")
    col1, col2, col3 = st.columns(3)
    col1.metric("Semieje Mayor (a)", f"{ell.a:,.3f} m")
    col2.metric("Semieje Menor (b)", f"{ell.b:,.3f} m")
    col3.metric("Achatamiento (f)", f"{ell.f:.8f}")

elif module == "7. Trisección y Bisección":
    st.subheader("📍 Trisección y Bisección Topográfica")
    tab_tri, tab_bi = st.tabs(["Trisección (3 Puntos)", "Bisección (2 Puntos)"])
    
    with tab_tri:
        st.markdown("### Trisección (Método de Tienstra)")
        datum_tri = st.selectbox("Sistema de Coordenadas", ["Planas Cartesianas Locales", "MAGNA-SIRGAS (Bogotá)"], key="dat_tri")
        
        with st.form("form_triseccion"):
            c1, c2, c3 = st.columns(3)
            na = c1.number_input("Norte A", value=1000.0)
            ea = c1.number_input("Este A", value=1000.0)
            nb = c2.number_input("Norte B", value=1500.0)
            eb = c2.number_input("Este B", value=2000.0)
            nc = c3.number_input("Norte C", value=800.0)
            ec = c3.number_input("Este C", value=2500.0)
            
            st.markdown("**Ángulos medidos desde P (en grados decimales)**")
            ca, cb, cc = st.columns(3)
            alpha = ca.number_input("Ángulo α (Hacia A)", value=45.0)
            beta = cb.number_input("Ángulo β (Hacia B)", value=60.0)
            gamma = cc.number_input("Ángulo γ (Hacia C)", value=75.0)
            
            btn_tri = st.form_submit_button("Calcular Trisección")
            
        if btn_tri:
            ep, np_coord = resolver_triseccion_tienstra(ea, na, eb, nb, ec, nc, alpha, beta, gamma)
            if ep and np_coord:
                st.success("✅ Cálculo exitoso")
                m1, m2 = st.columns(2)
                m1.metric("Norte P ($N_P$)", f"{np_coord:,.3f} m")
                m2.metric("Este P ($E_P$)", f"{ep:,.3f} m")
                pts = {"A": (ea, na), "B": (eb, nb), "C": (ec, nc), "Punto P (Calculado)": (ep, np_coord)}
                st.plotly_chart(fig_mapa_2d(pts, f"Mapa 2D Trisección - {datum_tri}"), use_container_width=True)
            else:
                st.error("Geometría colineal o ángulos inválidos.")

    with tab_bi:
        st.markdown("### Bisección (Intersección Directa desde dos Estaciones)")
        datum_bi = st.selectbox("Sistema de Coordenadas", ["Planas Cartesianas Locales", "MAGNA-SIRGAS (Bogotá)"], key="dat_bi")
        
        with st.form("form_biseccion"):
            c1, c2 = st.columns(2)
            na = c1.number_input("Norte Estación A", value=1000.0, key="bi_na")
            ea = c1.number_input("Este Estación A", value=1000.0, key="bi_ea")
            nb = c2.number_input("Norte Estación B", value=1500.0, key="bi_nb")
            eb = c2.number_input("Este Estación B", value=2000.0, key="bi_eb")
            
            cb1, cb2 = st.columns(2)
            alpha_bi = cb1.number_input("Ángulo α en Estación A (°)", value=50.0)
            beta_bi = cb2.number_input("Ángulo β en Estación B (°)", value=55.0)
            
            btn_bi = st.form_submit_button("Calcular Bisección")
            
        if btn_bi:
            ep, np_coord = resolver_biseccion(ea, na, eb, nb, alpha_bi, beta_bi)
            if ep and np_coord:
                st.success("✅ Cálculo de bisección exitoso")
                m1, m2 = st.columns(2)
                m1.metric("Norte P ($N_P$)", f"{np_coord:,.3f} m")
                m2.metric("Este P ($E_P$)", f"{ep:,.3f} m")
                pts = {"Estación A": (ea, na), "Estación B": (eb, nb), "Punto P (Calculado)": (ep, np_coord)}
                st.plotly_chart(fig_mapa_2d(pts, f"Mapa 2D Bisección - {datum_bi}"), use_container_width=True)
            else:
                st.error("Error geométrico en los ángulos o estaciones coincidentes.")

elif module == "8. Nivelación Diferencial Geodésica":
    st.subheader("📏 Nivelación Diferencial Geodésica")
    st.markdown("Ingresa los datos de la cartera topográfica[cite: 1].")

    if "df_nivelacion" not in st.session_state:
        st.session_state.df_nivelacion = pd.DataFrame({
            "Punto": ["BM-1", "1", "2", "3", "BM-2"],
            "Distancia_Armado": [0.0, 20.0, 25.0, 15.0, 30.0],
            "Vista_Atras": [1.250, 1.420, 0.0, 1.100, 0.0],
            "Vista_Intermedia": [0.0, 0.0, 1.350, 0.0, 0.0],
            "Vista_Adelante": [0.0, 1.150, 0.0, 1.480, 1.200],
            "Cota_Inicial": [2600.0, 0.0, 0.0, 0.0, 0.0]
        })

    df_edit = st.data_editor(st.session_state.df_nivelacion, num_rows="dynamic", use_container_width=True)

    if st.button("Calcular Cartera y Perfil"):
        df = df_edit.copy()
        cota_actual = df.loc[0, "Cota_Inicial"]
        hi_actual = cota_actual + df.loc[0, "Vista_Atras"]
        
        cotas_sb = [cota_actual]
        cotas_hi = [cota_actual]
        
        for i in range(1, len(df)):
            v_atras = df.loc[i, "Vista_Atras"]
            v_inter = df.loc[i, "Vista_Intermedia"]
            v_adel = df.loc[i, "Vista_Adelante"]
            
            lectura_evaluar = v_adel if v_adel > 0 else v_inter
            lectura_anterior = df.loc[i-1, "Vista_Atras"] if df.loc[i-1, "Vista_Intermedia"] == 0 and df.loc[i-1, "Vista_Adelante"] == 0 else (df.loc[i-1, "Vista_Intermedia"] if df.loc[i-1, "Vista_Intermedia"] > 0 else df.loc[i-1, "Vista_Adelante"])

            delta = lectura_anterior - lectura_evaluar
            cota_actual += delta
            cotas_sb.append(cota_actual)

            cota_por_hi = hi_actual - lectura_evaluar
            cotas_hi.append(cota_por_hi)
            
            if v_atras > 0:
                hi_actual = cota_por_hi + v_atras

        df["Cota_Calc_SB"] = cotas_sb
        df["Cota_Calc_HI"] = cotas_hi
        df["Cota_Ajustada"] = cotas_hi
        df["Distancia_Acumulada"] = df["Distancia_Armado"].cumsum()

        st.success("✅ Cálculos procesados correctamente.")
        st.dataframe(df[["Punto", "Distancia_Acumulada", "Cota_Calc_SB", "Cota_Calc_HI"]], use_container_width=True)
        st.plotly_chart(fig_perfil_elevacion(df), use_container_width=True)