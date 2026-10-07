from __future__ import annotations

import math
from dataclasses import dataclass
import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import hmac
import os
import urllib.request
import tarfile

# --- IMPORTACIÓN SEGURA PARA EVITAR CAÍDAS EN LA NUBE ---
try:
    from geographiclib.geoid import Geoid
    HAS_GEOGRAPHICLIB = True
except ImportError:
    HAS_GEOGRAPHICLIB = False
# =========================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (FRONTEND AMIGABLE)
# =========================================================
st.set_page_config(
    page_title="Geodesia Lab | Plataforma Geodésica",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para modernizar la interfaz
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
    section[data-testid="stSidebar"] { background-color: #0f172a; }
    section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
</style>
""", unsafe_allow_html=True)


# =========================
# 2. AUTENTICACIÓN
# =========================
def require_login():
    if st.session_state.get("authenticated", False):
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

require_login()


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

def is_zero(value: float, eps: float = EPS) -> bool: return abs(value) <= eps

def parse_required_float(label: str, raw_value: str, errors: list[str], min_value: float | None = None, max_value: float | None = None, forbid_zero: bool = False) -> float | None:
    text = raw_value.strip()
    if text == "":
        errors.append(f"• **{label}**: El campo está vacío.")
        return None
    try:
        value = float(text.replace(",", "."))
    except ValueError:
        errors.append(f"• **{label}**: Debe ser un número válido.")
        return None
    if not math.isfinite(value):
        errors.append(f"• **{label}**: No puede ser NaN ni infinito.")
        return None
    if forbid_zero and is_zero(value):
        errors.append(f"• **{label}**: El valor 0 no está permitido.")
        return None
    if min_value is not None and value < min_value:
        errors.append(f"• **{label}**: Debe ser ≥ {min_value}.")
    if max_value is not None and value > max_value:
        errors.append(f"• **{label}**: Debe ser ≤ {max_value}.")
    return value

def parse_required_int(label: str, raw_value: str, errors: list[str], min_value: int | None = None, max_value: int | None = None) -> int | None:
    text = raw_value.strip()
    if text == "":
        errors.append(f"• **{label}**: El campo está vacío.")
        return None
    try:
        value = int(text)
    except ValueError:
        errors.append(f"• **{label}**: Debe ser un entero válido.")
        return None
    if value == 0:
        errors.append(f"• **{label}**: El valor 0 no está permitido.")
        return None
    if min_value is not None and value < min_value:
        errors.append(f"• **{label}**: Debe ser ≥ {min_value}.")
    if max_value is not None and value > max_value:
        errors.append(f"• **{label}**: Debe ser ≤ {max_value}.")
    return value

def parse_angle(label: str, raw_value: str, errors: list[str], angle_type: str, forbid_zero: bool = True) -> float | None:
    text = raw_value.strip()
    if text == "":
        errors.append(f"• **{label}**: El campo está vacío.")
        return None

    cleaned = text.upper().replace(",", ".")
    cleaned = re.sub(r"[°º'’′\"”″]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    tokens = cleaned.split(" ")
    hemispheres = [t for t in tokens if t in {"N", "S", "E", "W"}]
    if len(hemispheres) > 1:
        errors.append(f"• **{label}**: Solo se permite un hemisferio.")
        return None

    hemisphere = hemispheres[0] if hemispheres else None
    numeric_tokens = [t for t in tokens if t not in {"N", "S", "E", "W"}]

    if len(numeric_tokens) not in (1, 2, 3):
        errors.append(f"• **{label}**: Formato inválido. Usa decimal (ej. 4.6) o GMS (ej. 4 36 0 N).")
        return None

    try:
        first_number = float(numeric_tokens[0])
    except ValueError:
        errors.append(f"• **{label}**: El valor angular no es válido.")
        return None

    if not math.isfinite(first_number):
        errors.append(f"• **{label}**: No puede ser NaN ni infinito.")
        return None

    numeric_sign = -1.0 if first_number < 0 else 1.0

    if len(numeric_tokens) == 1:
        value_abs = abs(first_number)
    else:
        try:
            degrees = float(numeric_tokens[0])
            minutes = float(numeric_tokens[1])
            seconds = float(numeric_tokens[2]) if len(numeric_tokens) == 3 else 0.0
        except ValueError:
            errors.append(f"• **{label}**: Grados, minutos y segundos deben ser numéricos.")
            return None

        if minutes < 0 or minutes >= 60 or seconds < 0 or seconds >= 60:
            errors.append(f"• **{label}**: Minutos y segundos deben estar en el rango [0, 59.99].")
            return None

        value_abs = abs(degrees) + (minutes / 60.0) + (seconds / 3600.0)

    if hemisphere is not None:
        if angle_type == "lat" and hemisphere not in {"N", "S"}:
            errors.append(f"• **{label}**: Para latitud solo se permite N o S.")
            return None
        if angle_type == "lon" and hemisphere not in {"E", "W"}:
            errors.append(f"• **{label}**: Para longitud solo se permite E o W.")
            return None

        hemi_sign = -1.0 if hemisphere in {"S", "W"} else 1.0
        if numeric_sign < 0 and hemi_sign > 0:
            errors.append(f"• **{label}**: El signo negativo contradice el hemisferio {hemisphere}.")
            return None
        sign = hemi_sign
    else:
        sign = numeric_sign

    value = sign * value_abs
    limit = 90.0 if angle_type == "lat" else 180.0
    if abs(value) > limit:
        errors.append(f"• **{label}**: Fuera del rango permitido ±{limit}°.")
        return None

    if forbid_zero and is_zero(value):
        errors.append(f"• **{label}**: El valor 0 no está permitido.")
        return None

    return value

def validate_ecef_values(x: float, y: float, z: float, ell: Ellipsoid, errors: list[str]) -> None:
    if abs(x) > ell.limit_xy or abs(y) > ell.limit_xy or abs(z) > ell.limit_z:
        errors.append("• **ECEF**: Coordenadas fuera del rango terrestre del elipsoide seleccionado.")
    r = math.sqrt(x * x + y * y + z * z)
    if r < 6_000_000 or r > 7_000_000:
        errors.append("• **ECEF**: El punto debe estar cerca de la superficie terrestre (rango 6,000 - 7,000 km).")

def show_errors(errors: list[str]) -> None:
    if errors:
        st.error("#### ⚠️ Corrige los siguientes errores en el formulario:\n\n" + "\n".join(errors))

# Cálculos geodésicos
def deg_to_rad(v: float) -> float: return math.radians(v)
def rad_to_deg(v: float) -> float: return math.degrees(v)

def prime_vertical_radius(lat_rad: float, ell: Ellipsoid) -> float:
    s = math.sin(lat_rad)
    return ell.a / math.sqrt(1.0 - ell.e2 * s * s)

def meridian_radius(lat_rad: float, ell: Ellipsoid) -> float:
    s = math.sin(lat_rad)
    return ell.a * (1.0 - ell.e2) / ((1.0 - ell.e2 * s * s) ** 1.5)

def geodetic_to_ecef(lat_deg: float, lon_deg: float, h_m: float, ell: Ellipsoid) -> tuple[float, float, float]:
    lat, lon = deg_to_rad(lat_deg), deg_to_rad(lon_deg)
    N = prime_vertical_radius(lat, ell)
    X = (N + h_m) * math.cos(lat) * math.cos(lon)
    Y = (N + h_m) * math.cos(lat) * math.sin(lon)
    Z = (N * (1.0 - ell.e2) + h_m) * math.sin(lat)
    return X, Y, Z

def ecef_to_geodetic(x: float, y: float, z: float, ell: Ellipsoid, tol: float = 1e-12, max_iter: int = 15) -> tuple[float, float, float, int]:
    p = math.hypot(x, y)
    if p < 1e-12:
        lat = math.copysign(math.pi / 2.0, z)
        return rad_to_deg(lat), 0.0, abs(z) - ell.b, 0

    lon = math.atan2(y, x)
    theta = math.atan2(z * ell.a, p * ell.b)
    lat = math.atan2(z + ell.ep2 * ell.b * math.sin(theta)**3, p - ell.e2 * ell.a * math.cos(theta)**3)

    iterations = 0
    for i in range(max_iter):
        iterations = i + 1
        N = prime_vertical_radius(lat, ell)
        cos_lat = math.cos(lat)
        h = abs(z) - ell.b if abs(cos_lat) < 1e-15 else p / cos_lat - N
        denom = p * (1.0 - ell.e2 * N / (N + h))
        lat_new = math.atan2(z, denom)
        if abs(lat_new - lat) < tol:
            lat = lat_new
            break
        lat = lat_new

    N = prime_vertical_radius(lat, ell)
    cos_lat = math.cos(lat)
    h = abs(z) - ell.b if abs(cos_lat) < 1e-15 else p / cos_lat - N
    return rad_to_deg(lat), rad_to_deg(lon), h, iterations

def parallel_arc_length(lat_deg: float, lon1_deg: float, lon2_deg: float, ell: Ellipsoid) -> tuple[float, float]:
    lat = deg_to_rad(lat_deg)
    dlon = deg_to_rad(lon2_deg - lon1_deg)
    dlon = (dlon + math.pi) % (2 * math.pi) - math.pi
    dlon_abs = abs(dlon)
    N = prime_vertical_radius(lat, ell)
    return N * math.cos(lat) * dlon_abs, rad_to_deg(dlon_abs)

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
# 5. CÁLCULOS TOPOGRÁFICOS (TRISECCIÓN Y NIVELACIÓN)
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

def fig_ecef_3d(x: float, y: float, z: float, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(x=[0, x], y=[0, y], z=[0, z], mode="lines+markers", line=dict(color="#0284c7", width=6), marker=dict(size=[3, 7], color=["#0f172a", "#ef4444"])))
    fig.update_layout(
        title=title, template="plotly_white",
        scene=dict(xaxis_title="X (m)", yaxis_title="Y (m)", zaxis_title="Z (m)", aspectmode="cube"),
        height=500, margin=dict(l=0, r=0, t=40, b=0)
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

@st.cache_resource(show_spinner=False)
def load_geoid():
    # Definimos dónde guardará Streamlit Cloud los archivos de la malla
    geoids_dir = os.path.join(os.getcwd(), 'geoids')
    model_name = 'egm2008-5'
    model_file = os.path.join(geoids_dir, f"{model_name}.pgm")
    
    # Si el archivo no existe en el servidor de la nube, lo descargamos
    if not os.path.exists(model_file):
        with st.spinner("🌍 Descargando modelo EGM2008 (40MB) en el servidor... Esto tomará unos segundos (solo ocurre la primera vez)."):
            url = f"https://sourceforge.net/projects/geographiclib/files/geoids-distrib/{model_name}.tar.bz2/download"
            tar_path = os.path.join(os.getcwd(), f"{model_name}.tar.bz2")
            
            # Descargar archivo
            urllib.request.urlretrieve(url, tar_path)
            
            # Extraer el contenido (geographiclib por defecto extrae en una carpeta 'geoids')
            with tarfile.open(tar_path, "r:bz2") as tar:
                tar.extractall(path=os.getcwd())
                
            # Limpiar el archivo comprimido para ahorrar RAM/Disco en la nube
            os.remove(tar_path)
            
    # Le indicamos a geographiclib que busque en la carpeta local recién creada
    return Geoid(model_name, path=geoids_dir)

def fig_geoide_3d_real(lat_pt=None, lon_pt=None, ell=None):
    geoid = load_geoid()
    
    # Malla global (resolución de 5 grados para fluidez web)
    lons = np.linspace(-180, 180, 73)
    lats = np.linspace(-90, 90, 37)
    Lon, Lat = np.meshgrid(lons, lats)
    
    # Calcular el N exacto con EGM2008
    N_real = np.zeros_like(Lon)
    for i in range(Lat.shape[0]):
        for j in range(Lat.shape[1]):
            N_real[i, j] = geoid(Lat[i, j], Lon[i, j])
            
    phi = np.radians(Lat)
    theta = np.radians(Lon)
    
    # Escala de la "Papa" Clásica: 
    # El geoide real es ±100m. A escala 1:1 es visualmente una esfera perfecta.
    # El estándar de visualización científica (Potsdam) exagera N por 15,000 para revelar la forma.
    EXAG_FIJA = 15000 
    R_base = ell.a if ell else 6378137.0
    R_def = R_base + N_real * EXAG_FIJA
    
    X = R_def * np.cos(phi) * np.cos(theta)
    Y = R_def * np.cos(phi) * np.sin(theta)
    Z = R_def * np.sin(phi)
    
    fig = go.Figure()
    
    # Renderizado de la superficie con relieve acentuado
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z, 
        surfacecolor=N_real, 
        colorscale='Jet',  # Paleta clásica de mapas gravitacionales
        colorbar_title="N (m) - EGM2008",
        name="Geoide EGM2008",
        opacity=1.0,
        lighting=dict(ambient=0.4, diffuse=0.8, roughness=0.4, specular=0.3, fresnel=0.2) # Realza el volumen
    ))
    
    # Marcador topográfico
    if lat_pt is not None and lon_pt is not None:
        n_pt = geoid(lat_pt, lon_pt)
        phi_pt = math.radians(lat_pt)
        theta_pt = math.radians(lon_pt)
        
        r_pt = R_base + n_pt * EXAG_FIJA
        xp = r_pt * math.cos(phi_pt) * math.cos(theta_pt)
        yp = r_pt * math.cos(phi_pt) * math.sin(theta_pt)
        zp = r_pt * math.sin(phi_pt)
        
        fig.add_trace(go.Scatter3d(
            x=[xp], y=[yp], z=[zp],
            mode='markers+text',
            marker=dict(size=8, color='#ffffff', symbol='circle', line=dict(color='#000000', width=2)),
            text=[f"N Exacto: {n_pt:.3f} m"],
            textposition="top center",
            name="Tu Ubicación"
        ))
        
    fig.update_layout(
        title="El Geoide Terrestre (Modelo EGM2008)",
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            aspectmode='data', camera=dict(eye=dict(x=1.3, y=1.3, z=0.6))
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        template="plotly_dark"
    )
    return fig, n_pt if 'n_pt' in locals() else None
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
            "8. Nivelación Diferencial Geodésica",
            "9. Visualizador del Geoide 3D (La Papa)"
        ]
    )

    st.markdown("---")
    st.caption(f"👤 **Usuario:** `{st.session_state.get('username', 'Demo')}`")
    if st.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()


# =========================
# CONTENIDO POR MÓDULOS
# =========================

if module == "1. Parámetros del Elipsoide":
    st.subheader("📐 Geometría del Elipsoide Seleccionado")
    tab1, tab2 = st.tabs(["📊 Métricas Principales", "ℹ️ Formatos Angulares Soportados"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        col1.metric("Semieje Mayor (a)", f"{ell.a:,.3f} m")
        col2.metric("Semieje Menor (b)", f"{ell.b:,.3f} m")
        col3.metric("Achatamiento (f)", f"{ell.f:.8f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Inverso Achatamiento (1/f)", f"{ell.inv_f:,.4f}")
        col5.metric("1ra Excentricidad² (e²)", f"{ell.e2:.8f}")
        col6.metric("2da Excentricidad² (e'²)", f"{ell.ep2:.8f}")

    with tab2:
        st.info("""
        **Formatos aceptados para latitud y longitud en todos los módulos:**
        * **Grados Decimales:** `4.6`, `-74.08175`
        * **Grados, Minutos y Segundos (GMS):** `4 36 0 N`, `74° 04' 54.3" W`
        """)

elif module == "2. Elipse Meridiana":
    st.subheader("🌐 Análisis de la Elipse Meridiana")
    
    with st.form("meridian_form"):
        lat_raw = st.text_input("Latitud para calcular radios M y N (opcional):", placeholder="Ej: 4.6 o 4 36 0 N")
        submitted = st.form_submit_button("Calcular Radios")

    errors = []
    lat = parse_angle("Latitud", lat_raw, errors, "lat", forbid_zero=False) if lat_raw.strip() else None

    col_m1, col_m2 = st.columns([1, 1.2])
    with col_m1:
        st.plotly_chart(fig_meridian_ellipse(ell), use_container_width=True)
    
    with col_m2:
        if lat is not None:
            phi = deg_to_rad(lat)
            M = meridian_radius(phi, ell)
            N = prime_vertical_radius(phi, ell)
            st.success(f"**Latitud analizada:** {lat:.6f}°")
            st.metric("Radio Meridiano (M)", f"{M:,.3f} m")
            st.metric("Radio Gran Normal / Primer Vertical (N)", f"{N:,.3f} m")
        else:
            st.info("Ingresa una latitud en el formulario para calcular los radios de curvatura $M$ y $N$.")

elif module == "3. Geodésicas → Cartesianas (ECEF)":
    st.subheader("📍 Conversión: Geodésicas a Cartesianas ECEF")

    with st.form("geo2ecef"):
        c1, c2, c3 = st.columns(3)
        lat_raw = c1.text_input("Latitud", "4.6", help="Decimal o GMS")
        lon_raw = c2.text_input("Longitud", "-74.0", help="Decimal o GMS")
        h_raw = c3.text_input("Altura elipsoidal h (m)", "2600")
        submitted = st.form_submit_button("Convertir a ECEF")

    if submitted:
        errors = []
        lat = parse_angle("Latitud", lat_raw, errors, "lat", forbid_zero=False)
        lon = parse_angle("Longitud", lon_raw, errors, "lon", forbid_zero=False)
        h = parse_required_float("Altura", h_raw, errors)

        if errors:
            show_errors(errors)
        else:
            X, Y, Z = geodetic_to_ecef(lat, lon, h, ell)
            st.markdown("#### Resultado en Coordenadas Cartesianas (ECEF)")
            m1, m2, m3 = st.columns(3)
            m1.metric("X (m)", f"{X:,.3f}")
            m2.metric("Y (m)", f"{Y:,.3f}")
            m3.metric("Z (m)", f"{Z:,.3f}")
            st.plotly_chart(fig_ecef_3d(X, Y, Z, "Vector ECEF 3D"), use_container_width=True)

elif module == "4. Cartesianas (ECEF) → Geodésicas":
    st.subheader("🔄 Conversión: Cartesianas ECEF a Geodésicas")

    with st.form("ecef2geo"):
        c1, c2, c3 = st.columns(3)
        x_raw = c1.text_input("X (m)", "1749871.0")
        y_raw = c2.text_input("Y (m)", "-6111234.0")
        z_raw = c3.text_input("Z (m)", "508123.0")
        submitted = st.form_submit_button("Convertir a Geodésicas")

    if submitted:
        errors = []
        x = parse_required_float("X", x_raw, errors)
        y = parse_required_float("Y", y_raw, errors)
        z = parse_required_float("Z", z_raw, errors)

        if x and y and z:
            validate_ecef_values(x, y, z, ell, errors)

        if errors:
            show_errors(errors)
        else:
            lat, lon, h, iters = ecef_to_geodetic(x, y, z, ell)
            st.markdown("#### Coordenadas Geodésicas Calculadas")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Latitud (°)", f"{lat:.8f}")
            m2.metric("Longitud (°)", f"{lon:.8f}")
            m3.metric("Altura h (m)", f"{h:,.3f}")
            m4.metric("Iteraciones", str(iters))

elif module == "5. Arco de Paralelo":
    st.subheader("📏 Longitud de Arco de Paralelo")

    with st.form("parallel_form"):
        c1, c2, c3 = st.columns(3)
        lat_raw = c1.text_input("Latitud del paralelo", "4.6")
        lon1_raw = c2.text_input("Longitud inicial", "-74.2")
        lon2_raw = c3.text_input("Longitud final", "-73.8")
        submitted = st.form_submit_button("Calcular Distancia")

    if submitted:
        errors = []
        lat = parse_angle("Latitud", lat_raw, errors, "lat", forbid_zero=False)
        lon1 = parse_angle("Longitud inicial", lon1_raw, errors, "lon", forbid_zero=False)
        lon2 = parse_angle("Longitud final", lon2_raw, errors, "lon", forbid_zero=False)

        if errors:
            show_errors(errors)
        else:
            arc_len, dlon = parallel_arc_length(lat, lon1, lon2, ell)
            m1, m2 = st.columns(2)
            m1.metric("ΔLongitud (°)", f"{dlon:.6f}")
            m2.metric("Longitud del Arco (m)", f"{arc_len:,.3f}")

elif module == "6. Cuadrilátero Geodésico y Área":
    st.subheader("🗺️ Cuadrilátero Geodésico y Cálculo de Área")

    with st.form("quad_form"):
        r1_1, r1_2 = st.columns(2)
        lat1_raw = r1_1.text_input("Latitud Punto 1", "4.4")
        lon1_raw = r1_2.text_input("Longitud Punto 1", "-74.2")
        
        r2_1, r2_2 = st.columns(2)
        lat2_raw = r2_1.text_input("Latitud Punto 2", "4.8")
        lon2_raw = r2_2.text_input("Longitud Punto 2", "-73.8")
        submitted = st.form_submit_button("Calcular Área y Geometría")

    if submitted:
        errors = []
        lat1 = parse_angle("Latitud 1", lat1_raw, errors, "lat", forbid_zero=False)
        lon1 = parse_angle("Longitud 1", lon1_raw, errors, "lon", forbid_zero=False)
        lat2 = parse_angle("Latitud 2", lat2_raw, errors, "lat", forbid_zero=False)
        lon2 = parse_angle("Longitud 2", lon2_raw, errors, "lon", forbid_zero=False)

        if errors:
            show_errors(errors)
        else:
            res = geodetic_quadrilateral(lat1, lon1, lat2, lon2, ell)
            c1, c2 = st.columns(2)
            c1.metric("Área en m²", f"{res['area_m2']:,.2f}")
            c2.metric("Área en km²", f"{res['area_km2']:,.4f}")

            with st.expander("Ver Vértices del Cuadrilátero"):
                st.json(res["vertices"])

elif module == "7. Trisección y Bisección":
    st.subheader("📍 Trisección y Bisección Topográfica")
    tab_tri, tab_bi = st.tabs(["Trisección (3 Puntos)", "Bisección (2 Puntos)"])
    
    with tab_tri:
        st.markdown("### Trisección (Método de Tienstra, Cassini, Collins)")
        metodo_tri = st.selectbox("Método de cálculo", ["Tienstra (Baricéntrico)", "Cassini", "Collins"])
        datum_tri = st.selectbox("Sistema de Coordenadas", ["Planas Cartesianas Locales", "MAGNA-SIRGAS (Bogotá)"])
        
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
            
            btn_tri = st.form_submit_button("Calcular Coordenadas P")
            
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
                st.error("Geometría colineal o ángulos inválidos. Revisa los datos de entrada.")

    with tab_bi:
        st.info("La bisección o intersección directa permite hallar las coordenadas de un punto visado desde dos estaciones conocidas.")

elif module == "8. Nivelación Diferencial Geodésica":
    st.subheader("📏 Nivelación Diferencial Geodésica")
    st.markdown("Ingresa los datos de la cartera topográfica. El sistema calculará las cotas por el método de **Subes y Bajas** y **Altura de Instrumento (HI)**[cite: 1].")

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

        st.success("✅ Cálculos procesados correctamente (Ambos métodos convergen).")
        st.dataframe(df[["Punto", "Distancia_Acumulada", "Cota_Calc_SB", "Cota_Calc_HI"]], use_container_width=True)
        st.plotly_chart(fig_perfil_elevacion(df), use_container_width=True)
        
elif module == "9. Visualizador del Geoide 3D (La Papa)":
    st.subheader("🥔 Visualizador del Geoide ('La Papa')")
    st.markdown("Representación 3D del campo de gravedad terrestre (EGM2008). s).")

    with st.form("geoid_form"):
        # Solo dos columnas, quitamos el slider de exageración
        c1, c2 = st.columns(2)
        lat_raw = c1.text_input("Latitud", "4.60", help="Latitud de la coordenada")
        lon_raw = c2.text_input("Longitud", "-74.08", help="Longitud de la coordenada")
        submitted = st.form_submit_button("Renderizar Geoide")

    if submitted:
        errors = []
        lat = parse_angle("Latitud", lat_raw, errors, "lat", forbid_zero=False)
        lon = parse_angle("Longitud", lon_raw, errors, "lon", forbid_zero=False)
        
        if errors:
            show_errors(errors)
        else:
            fig, n_exacto = fig_geoide_3d_real(lat, lon, ell)
            
            st.metric(
                label=f"Ondulación Geoidal (N) en [{lat:.4f}°, {lon:.4f}°]", 
                value=f"{n_exacto:.4f} m",
                delta="Precisión EGM2008",
                delta_color="off"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.info("💡 **Dato Geodésico:** A escala 1:1, la Tierra es visualmente indistinguible de una esfera perfecta. El modelo 3D superior utiliza la deformación estándar de 15,000x para hacer perceptible la forma real del campo gravitatorio ('La Papa').")