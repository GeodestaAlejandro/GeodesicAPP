from __future__ import annotations

import math
from dataclasses import dataclass
import re
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import hmac

def require_login():
    if st.session_state.get("authenticated", False):
        return

    st.title("Acceso privado")
    st.write("Ingresa tu usuario y contraseña.")

    with st.form("login_form"):
        username = st.text_input("Usuario").strip()
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        users_section = st.secrets.get("users", {})
        users = {str(k): str(v) for k, v in dict(users_section).items()}
        valid_password = users.get(username)

        if isinstance(valid_password, str) and hmac.compare_digest(password, valid_password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.stop()

require_login()

# =========================
# CONFIG APP
# =========================
st.set_page_config(
    page_title="Mini App Geodésica",
    page_icon="🌍",
    layout="wide",
)

# =========================
# DATOS BASE
# =========================
ELLIPSOIDS = {
    "WGS84": {
        "a": 6378137.0,
        "b": 6356752.314245
    },
    "GRS80": {
        "a": 6378137.0,
        "b": 6356752.314140
    },
    "WGS72": {
        "a": 6378135.0,
        "b": 6356750.520016
    },
    "Clarke1866": {
        "a": 6378206.4,
        "b": 6356583.8
    },
    "Clarke1880": {
        "a": 6378249.145,
        "b": 6356514.86955
    },
    "International1924": {
        "a": 6378388.0,
        "b": 6356911.946
    },
    "Airy1830": {
        "a": 6377563.396,
        "b": 6356256.909
    },
    "Bessel1841": {
        "a": 6377397.155,
        "b": 6356078.963
    },
    "Krassovsky1940": {
        "a": 6378245.0,
        "b": 6356863.019
    },
    "Everest1830": {
        "a": 6377276.345,
        "b": 6356075.413
    }
}

MARGIN_HEIGHT = 10000.0


# =========================
# MODELO DEL ELIPSOIDE
# =========================
@dataclass(frozen=True)
class Ellipsoid:
    name: str
    a: float
    b: float

    @property
    def f(self) -> float:
        return (self.a - self.b) / self.a

    @property
    def inv_f(self) -> float:
        f = self.f
        return float("inf") if abs(f) < 1e-18 else 1.0 / f

    @property
    def e2(self) -> float:
        return (self.a**2 - self.b**2) / self.a**2

    @property
    def ep2(self) -> float:
        return (self.a**2 - self.b**2) / self.b**2

    @property
    def limit_xy(self) -> float:
        return self.a + MARGIN_HEIGHT

    @property
    def limit_z(self) -> float:
        return self.b + MARGIN_HEIGHT


def get_ellipsoid(name: str) -> Ellipsoid:
    data = ELLIPSOIDS[name]
    return Ellipsoid(name=name, a=float(data["a"]), b=float(data["b"]))


# =========================
# VALIDACIÓN
# =========================

EPS = 1e-15


def is_zero(value: float, eps: float = EPS) -> bool:
    return abs(value) <= eps


def parse_required_float(
    label: str,
    raw_value: str,
    errors: list[str],
    min_value: float | None = None,
    max_value: float | None = None,
    forbid_zero: bool = False,
) -> float | None:
    text = raw_value.strip()

    if text == "":
        errors.append(f"• {label}: el campo está vacío.")
        return None

    try:
        value = float(text.replace(",", "."))
    except ValueError:
        errors.append(f"• {label}: debe ser un número válido.")
        return None

    if not math.isfinite(value):
        errors.append(f"• {label}: no puede ser NaN ni infinito.")
        return None

    if forbid_zero and is_zero(value):
        errors.append(f"• {label}: el valor 0 no está permitido.")
        return None

    if min_value is not None and value < min_value:
        errors.append(f"• {label}: debe ser ≥ {min_value}.")
    if max_value is not None and value > max_value:
        errors.append(f"• {label}: debe ser ≤ {max_value}.")

    return value


def parse_optional_float(
    label: str,
    raw_value: str,
    errors: list[str],
    min_value: float | None = None,
    max_value: float | None = None,
    forbid_zero: bool = False,
) -> float | None:
    text = raw_value.strip()

    if text == "":
        return None

    try:
        value = float(text.replace(",", "."))
    except ValueError:
        errors.append(f"• {label}: debe ser un número válido.")
        return None

    if not math.isfinite(value):
        errors.append(f"• {label}: no puede ser NaN ni infinito.")
        return None

    if forbid_zero and is_zero(value):
        errors.append(f"• {label}: el valor 0 no está permitido.")
        return None

    if min_value is not None and value < min_value:
        errors.append(f"• {label}: debe ser ≥ {min_value}.")
    if max_value is not None and value > max_value:
        errors.append(f"• {label}: debe ser ≤ {max_value}.")

    return value


def parse_required_int(
    label: str,
    raw_value: str,
    errors: list[str],
    min_value: int | None = None,
    max_value: int | None = None,
) -> int | None:
    text = raw_value.strip()

    if text == "":
        errors.append(f"• {label}: el campo está vacío.")
        return None

    try:
        value = int(text)
    except ValueError:
        errors.append(f"• {label}: debe ser un entero válido.")
        return None

    if value == 0:
        errors.append(f"• {label}: el valor 0 no está permitido.")
        return None

    if min_value is not None and value < min_value:
        errors.append(f"• {label}: debe ser ≥ {min_value}.")
    if max_value is not None and value > max_value:
        errors.append(f"• {label}: debe ser ≤ {max_value}.")

    return value


def parse_angle(
    label: str,
    raw_value: str,
    errors: list[str],
    angle_type: str,   # "lat" o "lon"
    forbid_zero: bool = True,
) -> float | None:
    """
    Acepta:
    - Decimal: 4.6, -74.08175
    - GMS: 4 36 0 N
    - GMS: 74° 04' 54.3" W
    - GMS: -74 4 54.3
    """
    text = raw_value.strip()

    if text == "":
        errors.append(f"• {label}: el campo está vacío.")
        return None

    cleaned = text.upper().replace(",", ".")
    cleaned = re.sub(r"[°º'’′\"”″]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    tokens = cleaned.split(" ")

    hemispheres = [t for t in tokens if t in {"N", "S", "E", "W"}]
    if len(hemispheres) > 1:
        errors.append(f"• {label}: solo se permite un hemisferio.")
        return None

    hemisphere = hemispheres[0] if hemispheres else None
    numeric_tokens = [t for t in tokens if t not in {"N", "S", "E", "W"}]

    if len(numeric_tokens) not in (1, 2, 3):
        errors.append(
            f"• {label}: formato inválido. Usa decimal (4.6) o GMS (4 36 0 N)."
        )
        return None

    try:
        first_number = float(numeric_tokens[0])
    except ValueError:
        errors.append(f"• {label}: el valor angular no es válido.")
        return None

    if not math.isfinite(first_number):
        errors.append(f"• {label}: no puede ser NaN ni infinito.")
        return None

    numeric_sign = -1.0 if first_number < 0 else 1.0

    if len(numeric_tokens) == 1:
        value_abs = abs(first_number)
        minutes = 0.0
        seconds = 0.0
    else:
        try:
            degrees = float(numeric_tokens[0])
            minutes = float(numeric_tokens[1])
            seconds = float(numeric_tokens[2]) if len(numeric_tokens) == 3 else 0.0
        except ValueError:
            errors.append(f"• {label}: grados, minutos y segundos deben ser numéricos.")
            return None

        if not all(math.isfinite(v) for v in [degrees, minutes, seconds]):
            errors.append(f"• {label}: no puede contener NaN ni infinito.")
            return None

        if minutes < 0 or minutes >= 60:
            errors.append(f"• {label}: los minutos deben estar entre 0 y 59.999...")
            return None

        if seconds < 0 or seconds >= 60:
            errors.append(f"• {label}: los segundos deben estar entre 0 y 59.999...")
            return None

        value_abs = abs(degrees) + (minutes / 60.0) + (seconds / 3600.0)

    if hemisphere is not None:
        if angle_type == "lat" and hemisphere not in {"N", "S"}:
            errors.append(f"• {label}: para latitud solo se permite N o S.")
            return None

        if angle_type == "lon" and hemisphere not in {"E", "W"}:
            errors.append(f"• {label}: para longitud solo se permite E o W.")
            return None

        hemi_sign = -1.0 if hemisphere in {"S", "W"} else 1.0

        if numeric_sign < 0 and hemi_sign > 0:
            errors.append(
                f"• {label}: el signo negativo contradice el hemisferio {hemisphere}."
            )
            return None

        sign = hemi_sign
    else:
        sign = numeric_sign

    value = sign * value_abs

    limit = 90.0 if angle_type == "lat" else 180.0
    if abs(value) > limit:
        errors.append(f"• {label}: fuera del rango permitido ±{limit}°.")
        return None

    if forbid_zero and is_zero(value):
        errors.append(f"• {label}: el valor 0 no está permitido.")
        return None

    return value


def validate_ecef_values(x: float, y: float, z: float, ell: Ellipsoid, errors: list[str]) -> None:
    if abs(x) > ell.limit_xy:
        errors.append(f"• X: fuera del rango terrestre razonable (±{ell.limit_xy:.3f} m).")
    if abs(y) > ell.limit_xy:
        errors.append(f"• Y: fuera del rango terrestre razonable (±{ell.limit_xy:.3f} m).")
    if abs(z) > ell.limit_z:
        errors.append(f"• Z: fuera del rango terrestre razonable (±{ell.limit_z:.3f} m).")

    r = math.sqrt(x * x + y * y + z * z)

    if r <= EPS:
        errors.append("• El vector ECEF no puede ser nulo.")
    if r < 6_000_000:
        errors.append("• El punto ECEF parece demasiado cerca del centro de la Tierra.")
    if r > 7_000_000:
        errors.append("• El punto ECEF parece fuera del rango terrestre razonable para esta demo.")


def show_errors(errors: list[str]) -> None:
    if errors:
        st.error("Se encontraron errores en la entrada:\n\n" + "\n".join(errors))
        
# =========================
# NÚCLEO GEODÉSICO
# =========================
def deg_to_rad(value: float) -> float:
    return math.radians(value)


def rad_to_deg(value: float) -> float:
    return math.degrees(value)


def prime_vertical_radius(lat_rad: float, ell: Ellipsoid) -> float:
    sin_lat = math.sin(lat_rad)
    return ell.a / math.sqrt(1.0 - ell.e2 * sin_lat * sin_lat)


def meridian_radius(lat_rad: float, ell: Ellipsoid) -> float:
    sin_lat = math.sin(lat_rad)
    return ell.a * (1.0 - ell.e2) / ((1.0 - ell.e2 * sin_lat * sin_lat) ** 1.5)


def geodetic_to_ecef(lat_deg: float, lon_deg: float, h_m: float, ell: Ellipsoid) -> tuple[float, float, float]:
    lat = deg_to_rad(lat_deg)
    lon = deg_to_rad(lon_deg)

    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)

    N = prime_vertical_radius(lat, ell)

    X = (N + h_m) * cos_lat * cos_lon
    Y = (N + h_m) * cos_lat * sin_lon
    Z = (N * (1.0 - ell.e2) + h_m) * sin_lat
    return X, Y, Z


def ecef_to_geodetic(
    x: float,
    y: float,
    z: float,
    ell: Ellipsoid,
    tol: float = 1e-12,
    max_iter: int = 15,
) -> tuple[float, float, float, int]:
    p = math.hypot(x, y)

    if p < 1e-12:
        lat = math.copysign(math.pi / 2.0, z)
        lon = 0.0
        h = abs(z) - ell.b
        return rad_to_deg(lat), rad_to_deg(lon), h, 0

    lon = math.atan2(y, x)

    # aproximación inicial tipo Bowring
    theta = math.atan2(z * ell.a, p * ell.b)
    sin_theta = math.sin(theta)
    cos_theta = math.cos(theta)
    lat = math.atan2(
        z + ell.ep2 * ell.b * sin_theta**3,
        p - ell.e2 * ell.a * cos_theta**3,
    )

    iterations = 0
    for i in range(max_iter):
        iterations = i + 1
        N = prime_vertical_radius(lat, ell)
        cos_lat = math.cos(lat)

        if abs(cos_lat) < 1e-15:
            h = abs(z) - ell.b
        else:
            h = p / cos_lat - N

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


def generate_meridian_ellipse_points(ell: Ellipsoid, samples: int = 360) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0.0, 2.0 * math.pi, samples + 1)
    x = ell.a * np.cos(t)
    z = ell.b * np.sin(t)
    return x, z


def normalize_delta_lon(lon1_deg: float, lon2_deg: float) -> float:
    d = deg_to_rad(lon2_deg - lon1_deg)
    while d <= -math.pi:
        d += 2.0 * math.pi
    while d > math.pi:
        d -= 2.0 * math.pi
    return abs(d)


def parallel_arc_length(lat_deg: float, lon1_deg: float, lon2_deg: float, ell: Ellipsoid) -> tuple[float, float]:
    lat = deg_to_rad(lat_deg)
    dlon = normalize_delta_lon(lon1_deg, lon2_deg)
    N = prime_vertical_radius(lat, ell)
    length = N * math.cos(lat) * dlon
    return length, rad_to_deg(dlon)


def meridian_arc_between(lat1_deg: float, lat2_deg: float, ell: Ellipsoid, n: int = 4000) -> float:
    phi1 = deg_to_rad(lat1_deg)
    phi2 = deg_to_rad(lat2_deg)

    phis = np.linspace(phi1, phi2, n)
    values = np.array([meridian_radius(phi, ell) for phi in phis], dtype=float)

    return abs(trapezoidal_integral(phis, values))

def trapezoidal_integral(x_values, y_values) -> float:
    if len(x_values) != len(y_values):
        raise ValueError("La integración trapezoidal requiere arreglos del mismo tamaño.")

    total = 0.0
    for i in range(len(x_values) - 1):
        dx = x_values[i + 1] - x_values[i]
        total += 0.5 * (y_values[i] + y_values[i + 1]) * dx

    return float(total)

def geodetic_quadrilateral(
    lat1_deg: float,
    lon1_deg: float,
    lat2_deg: float,
    lon2_deg: float,
    ell: Ellipsoid,
) -> dict:
    south = min(lat1_deg, lat2_deg)
    north = max(lat1_deg, lat2_deg)
    west = min(lon1_deg, lon2_deg)
    east = max(lon1_deg, lon2_deg)

    if abs(lat1_deg - lat2_deg) < EPS:
        raise ValueError("Las latitudes no pueden ser iguales para formar un cuadrilátero.")
    if abs(lon1_deg - lon2_deg) < EPS:
        raise ValueError("Las longitudes no pueden ser iguales para formar un cuadrilátero.")
    if abs(lon1_deg - lon2_deg) > 180.0:
        raise ValueError("Esta versión no soporta cuadriláteros que crucen el antimeridiano.")
    if abs(abs(lat1_deg) - 90.0) < EPS or abs(abs(lat2_deg) - 90.0) < EPS:
        raise ValueError("No se permiten vértices exactamente en los polos para esta demo.")

    south_rad = deg_to_rad(south)
    north_rad = deg_to_rad(north)
    dlon = deg_to_rad(east - west)

    south_parallel = prime_vertical_radius(south_rad, ell) * math.cos(south_rad) * dlon
    north_parallel = prime_vertical_radius(north_rad, ell) * math.cos(north_rad) * dlon
    meridian_len = meridian_arc_between(south, north, ell)

    phis = np.linspace(south_rad, north_rad, 5000)
    integrand = np.array(
        [
            meridian_radius(phi, ell) * prime_vertical_radius(phi, ell) * math.cos(phi)
            for phi in phis
        ],
        dtype=float,
    )
    area_m2 = abs(dlon * trapezoidal_integral(phis, integrand))

    vertices = [
        {"lat": south, "lon": west},
        {"lat": south, "lon": east},
        {"lat": north, "lon": east},
        {"lat": north, "lon": west},
        {"lat": south, "lon": west},
    ]

    return {
        "south_parallel_length": south_parallel,
        "north_parallel_length": north_parallel,
        "west_meridian_length": meridian_len,
        "east_meridian_length": meridian_len,
        "area_m2": area_m2,
        "area_km2": area_m2 / 1_000_000.0,
        "vertices": vertices,
    }


# =========================
# FIGURAS
# =========================

# =========================
# FIGURAS
# =========================

def visual_height_for_plot(
    h_m: float,
    scale: float = 80.0,
    min_visible: float = 15000.0,
    max_visible: float = 250000.0,
) -> float:
    """
    Exagera la altura solo para visualización.
    No cambia el cálculo geodésico real.
    """
    if abs(h_m) < 1e-12:
        return 0.0

    sign = 1.0 if h_m >= 0.0 else -1.0
    return sign * min(max(abs(h_m) * scale, min_visible), max_visible)


def camera_from_point(x: float, y: float, z: float) -> dict:
    v = np.array([x, y, z], dtype=float)
    n = float(np.linalg.norm(v))

    if n < 1e-12:
        return dict(eye=dict(x=1.6, y=1.4, z=1.1))

    u = v / n
    z_axis = np.array([0.0, 0.0, 1.0], dtype=float)

    side = np.cross(z_axis, u)
    side_norm = float(np.linalg.norm(side))
    if side_norm < 1e-12:
        side = np.array([1.0, 0.0, 0.0], dtype=float)
    else:
        side = side / side_norm

    up = np.cross(u, side)
    up_norm = float(np.linalg.norm(up))
    if up_norm > 1e-12:
        up = up / up_norm
    else:
        up = np.array([0.0, 0.0, 1.0], dtype=float)

    eye = 1.8 * u + 0.55 * side + 0.35 * up

    return dict(
        eye=dict(x=float(eye[0]), y=float(eye[1]), z=float(eye[2])),
        up=dict(x=float(up[0]), y=float(up[1]), z=float(up[2])),
        center=dict(x=0.0, y=0.0, z=0.0),
    )


def build_local_ellipsoid_patch(
    lat_deg: float,
    lon_deg: float,
    ell: Ellipsoid,
    span_lat_deg: float = 0.8,
    samples: int = 60,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    span_lat_deg = max(0.15, float(span_lat_deg))
    cos_lat = max(abs(math.cos(math.radians(lat_deg))), 0.20)
    span_lon_deg = span_lat_deg / cos_lat

    lat_vals = np.linspace(
        max(-89.9, lat_deg - span_lat_deg),
        min(89.9, lat_deg + span_lat_deg),
        samples,
    )
    lon_vals = np.linspace(
        lon_deg - span_lon_deg,
        lon_deg + span_lon_deg,
        samples,
    )

    lon_grid, lat_grid = np.meshgrid(lon_vals, lat_vals)
    return geodetic_array_to_ecef(lat_grid, lon_grid, ell, h=0.0)


def cube_ranges_from_arrays(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    extra_points: list[tuple[float, float, float]] | None = None,
) -> tuple[list[float], list[float], list[float]]:
    xs = [float(np.min(x)), float(np.max(x))]
    ys = [float(np.min(y)), float(np.max(y))]
    zs = [float(np.min(z)), float(np.max(z))]

    if extra_points:
        xs.extend(float(p[0]) for p in extra_points)
        ys.extend(float(p[1]) for p in extra_points)
        zs.extend(float(p[2]) for p in extra_points)

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    zmin, zmax = min(zs), max(zs)

    span = max(xmax - xmin, ymax - ymin, zmax - zmin, 1.0)
    half = span * 0.62

    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    zmid = 0.5 * (zmin + zmax)

    return (
        [xmid - half, xmid + half],
        [ymid - half, ymid + half],
        [zmid - half, zmid + half],
    )

def compute_axis_range(
    values: list[float],
    min_pad: float,
    clamp: tuple[float, float] | None = None,
) -> list[float]:
    valid = [float(v) for v in values if v is not None and math.isfinite(v)]
    if not valid:
        return [-1.0, 1.0]

    vmin = min(valid)
    vmax = max(valid)
    span = vmax - vmin
    pad = max(min_pad, span * 0.15)

    low = vmin - pad
    high = vmax + pad

    if clamp is not None:
        low = max(clamp[0], low)
        high = min(clamp[1], high)

        if low >= high:
            center = min(max(valid[0], clamp[0]), clamp[1])
            low = max(clamp[0], center - min_pad)
            high = min(clamp[1], center + min_pad)

            if low >= high:
                low, high = clamp

    return [low, high]


def compute_cube_ranges(
    points: list[tuple[float, float, float]],
) -> tuple[list[float], list[float], list[float]]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    zmin, zmax = min(zs), max(zs)

    span = max(xmax - xmin, ymax - ymin, zmax - zmin, 1.0)
    half = span * 0.55

    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    zmid = 0.5 * (zmin + zmax)

    return (
        [xmid - half, xmid + half],
        [ymid - half, ymid + half],
        [zmid - half, zmid + half],
    )


def build_shortest_parallel_path(
    lat: float,
    lon1: float,
    lon2: float,
    samples: int = 180,
) -> tuple[list[float | None], list[float | None]]:
    delta = lon2 - lon1
    while delta <= -180.0:
        delta += 360.0
    while delta > 180.0:
        delta -= 360.0

    raw_lons = np.linspace(lon1, lon1 + delta, samples)
    wrapped = ((raw_lons + 180.0) % 360.0) - 180.0

    lons_plot: list[float | None] = []
    lats_plot: list[float | None] = []

    prev = None
    for lon in wrapped:
        lon_f = float(lon)

        if prev is not None and abs(lon_f - prev) > 180.0:
            lons_plot.append(None)
            lats_plot.append(None)

        lons_plot.append(lon_f)
        lats_plot.append(float(lat))
        prev = lon_f

    return lons_plot, lats_plot


def fig_meridian_ellipse(x: np.ndarray, z: np.ndarray, ell: Ellipsoid) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=z,
            mode="lines",
            name="Elipse meridiana",
            line=dict(color="#1f77b4", width=3),
            hovertemplate="X: %{x:,.3f} m<br>Z: %{y:,.3f} m<extra></extra>",
        )
    )
    fig.update_layout(
        title=f"Elipse meridiana - {ell.name}",
        template="plotly_white",
        xaxis=dict(title="Eje X (m)", zeroline=True),
        yaxis=dict(title="Eje Z (m)", zeroline=True, scaleanchor="x", scaleratio=1),
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def fig_geodetic_point(lat: float, lon: float, title: str) -> go.Figure:
    lon_range = compute_axis_range([lon], min_pad=1.0, clamp=(-180.0, 180.0))
    lat_range = compute_axis_range([lat], min_pad=1.0, clamp=(-90.0, 90.0))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[lon],
            y=[lat],
            mode="markers+text",
            text=["Punto"],
            textposition="top center",
            marker=dict(size=12, color="crimson"),
            hovertemplate="Longitud: %{x:.8f}°<br>Latitud: %{y:.8f}°<extra></extra>",
            showlegend=False,
        )
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
        xaxis=dict(title="Longitud (deg)", range=lon_range, zeroline=True),
        yaxis=dict(title="Latitud (deg)", range=lat_range, zeroline=True),
        height=450,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def fig_ecef_point(x: float, y: float, z: float, title: str) -> go.Figure:
    x_range, y_range, z_range = compute_cube_ranges([(0.0, 0.0, 0.0), (x, y, z)])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter3d(
            x=[0.0, x],
            y=[0.0, y],
            z=[0.0, z],
            mode="lines",
            line=dict(color="#1f77b4", width=6),
            name="Vector ECEF",
            hovertemplate="X: %{x:,.3f} m<br>Y: %{y:,.3f} m<br>Z: %{z:,.3f} m<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[0.0],
            y=[0.0],
            z=[0.0],
            mode="markers+text",
            text=["O"],
            textposition="top center",
            marker=dict(size=5, color="black"),
            name="Origen",
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[x],
            y=[y],
            z=[z],
            mode="markers+text",
            text=["P"],
            textposition="top center",
            marker=dict(size=6, color="crimson"),
            name="Punto",
        )
    )

    fig.update_layout(
        title=title,
        template="plotly_white",
        scene=dict(
            aspectmode="cube",
            xaxis=dict(title="X (m)", range=x_range),
            yaxis=dict(title="Y (m)", range=y_range),
            zaxis=dict(title="Z (m)", range=z_range),
        ),
        height=550,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig


def fig_parallel_arc(lat: float, lon1: float, lon2: float) -> go.Figure:
    lons, lats = build_shortest_parallel_path(lat, lon1, lon2)
    finite_lons = [v for v in lons if v is not None]

    lon_range = compute_axis_range(finite_lons, min_pad=2.0, clamp=(-180.0, 180.0))
    lat_range = compute_axis_range([lat], min_pad=1.0, clamp=(-90.0, 90.0))

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=lons,
            y=lats,
            mode="lines+markers",
            connectgaps=False,
            line=dict(color="#2ca02c", width=3),
            marker=dict(size=5),
            name="Arco de paralelo",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[lon1, lon2],
            y=[lat, lat],
            mode="markers+text",
            text=["Inicio", "Fin"],
            textposition="top center",
            marker=dict(size=9, color=["#1f77b4", "#d62728"]),
            showlegend=False,
        )
    )

    fig.update_layout(
        title="Representación 2D del arco de paralelo",
        template="plotly_white",
        xaxis=dict(title="Longitud (deg)", range=lon_range, zeroline=True),
        yaxis=dict(title="Latitud (deg)", range=lat_range, zeroline=True),
        height=450,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def fig_quadrilateral(vertices: list[dict]) -> go.Figure:
    lons = [v["lon"] for v in vertices]
    lats = [v["lat"] for v in vertices]

    lon_range = compute_axis_range(lons, min_pad=0.3, clamp=(-180.0, 180.0))
    lat_range = compute_axis_range(lats, min_pad=0.3, clamp=(-90.0, 90.0))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=lons,
            y=lats,
            mode="lines+markers",
            fill="toself",
            fillcolor="rgba(148, 103, 189, 0.20)",
            line=dict(color="#9467bd", width=3),
            marker=dict(size=7),
            name="Cuadrilátero",
            hovertemplate="Lon: %{x:.8f}°<br>Lat: %{y:.8f}°<extra></extra>",
        )
    )
    fig.update_layout(
        title="Cuadrilátero geodésico",
        template="plotly_white",
        xaxis=dict(title="Longitud (deg)", range=lon_range, zeroline=True),
        yaxis=dict(
            title="Latitud (deg)",
            range=lat_range,
            zeroline=True,
            scaleanchor="x",
            scaleratio=1,
        ),
        height=450,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig

def geodetic_array_to_ecef(lat_deg, lon_deg, ell: Ellipsoid, h=0.0):
    lat = np.radians(np.asarray(lat_deg, dtype=float))
    lon = np.radians(np.asarray(lon_deg, dtype=float))
    h = np.asarray(h, dtype=float)

    sin_lat = np.sin(lat)
    cos_lat = np.cos(lat)
    sin_lon = np.sin(lon)
    cos_lon = np.cos(lon)

    N = ell.a / np.sqrt(1.0 - ell.e2 * sin_lat * sin_lat)

    X = (N + h) * cos_lat * cos_lon
    Y = (N + h) * cos_lat * sin_lon
    Z = (N * (1.0 - ell.e2) + h) * sin_lat
    return X, Y, Z


def generate_ellipsoid_surface(ell: Ellipsoid, n_lon: int = 90, n_lat: int = 45):
    lon = np.linspace(-180.0, 180.0, n_lon)
    lat = np.linspace(-90.0, 90.0, n_lat)
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    return geodetic_array_to_ecef(lat_grid, lon_grid, ell, h=0.0)


def ellipsoid_scene(ell: Ellipsoid) -> dict:
    xy_limit = ell.a + 150000.0
    z_limit = ell.b + 150000.0
    return dict(
        aspectmode="data",
        xaxis=dict(title="X (m)", range=[-xy_limit, xy_limit]),
        yaxis=dict(title="Y (m)", range=[-xy_limit, xy_limit]),
        zaxis=dict(title="Z (m)", range=[-z_limit, z_limit]),
        camera=dict(eye=dict(x=1.5, y=1.35, z=0.95)),
    )


def add_ellipsoid_surface(fig: go.Figure, ell: Ellipsoid, opacity: float = 0.60) -> None:
    ex, ey, ez = generate_ellipsoid_surface(ell)

    fig.add_trace(
        go.Surface(
            x=ex,
            y=ey,
            z=ez,
            surfacecolor=np.zeros_like(ex),
            colorscale=[[0.0, "#dce6f2"], [1.0, "#8fb3d9"]],
            showscale=False,
            opacity=opacity,
            hoverinfo="skip",
            name="Elipsoide",
        )
    )
    
def fig_point_local_zoom(lat: float, lon: float, h: float, ell: Ellipsoid, title: str) -> go.Figure:
    patch_x, patch_y, patch_z = build_local_ellipsoid_patch(lat, lon, ell)

    sx, sy, sz = geodetic_to_ecef(lat, lon, 0.0, ell)
    h_vis = visual_height_for_plot(
        h,
        scale=120.0,
        min_visible=5000.0,
        max_visible=150000.0,
    )
    px, py, pz = geodetic_to_ecef(lat, lon, h_vis, ell)

    x_range, y_range, z_range = cube_ranges_from_arrays(
        patch_x,
        patch_y,
        patch_z,
        extra_points=[(sx, sy, sz), (px, py, pz)],
    )

    fig = go.Figure()

    fig.add_trace(
        go.Surface(
            x=patch_x,
            y=patch_y,
            z=patch_z,
            surfacecolor=np.zeros_like(patch_x),
            colorscale=[[0.0, "#dce6f2"], [1.0, "#8fb3d9"]],
            showscale=False,
            opacity=0.98,
            hoverinfo="skip",
            name="Superficie local del elipsoide",
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[sx, px],
            y=[sy, py],
            z=[sz, pz],
            mode="lines",
            line=dict(color="#ff7f0e", width=10, dash="dash"),
            name="Altura (visual)",
            hovertemplate=(
                f"h real: {h:,.3f} m<br>"
                f"h visual: {h_vis:,.3f} m<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[sx],
            y=[sy],
            z=[sz],
            mode="markers+text",
            text=["S"],
            textposition="bottom center",
            marker=dict(size=6, color="#2ca02c"),
            name="Proyección",
            hovertemplate=(
                f"Lat: {lat:.8f}°<br>"
                f"Lon: {lon:.8f}°<br>"
                f"h: 0.000 m<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[px],
            y=[py],
            z=[pz],
            mode="markers+text",
            text=["P"],
            textposition="top center",
            marker=dict(size=8, color="crimson"),
            name="Punto",
            hovertemplate=(
                f"Lat: {lat:.8f}°<br>"
                f"Lon: {lon:.8f}°<br>"
                f"h real: {h:,.3f} m<br>"
                f"h visual: {h_vis:,.3f} m<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=title,
        template="plotly_white",
        scene=dict(
            aspectmode="data",
            xaxis=dict(title="X (m)", range=x_range),
            yaxis=dict(title="Y (m)", range=y_range),
            zaxis=dict(title="Z (m)", range=z_range),
            camera=dict(eye=dict(x=1.35, y=1.25, z=0.90)),
        ),
        height=650,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig


def fig_point_on_ellipsoid(lat: float, lon: float, h: float, ell: Ellipsoid, title: str) -> go.Figure:
    sx, sy, sz = geodetic_to_ecef(lat, lon, 0.0, ell)
    h_vis = visual_height_for_plot(h)
    px, py, pz = geodetic_to_ecef(lat, lon, h_vis, ell)

    fig = go.Figure()
    add_ellipsoid_surface(fig, ell, opacity=0.25)

    fig.add_trace(
        go.Scatter3d(
            x=[sx, px],
            y=[sy, py],
            z=[sz, pz],
            mode="lines",
            line=dict(color="#ff7f0e", width=8, dash="dash"),
            name="Altura (visual)",
            hovertemplate=(
                f"h real: {h:,.3f} m<br>"
                f"h visual: {h_vis:,.3f} m<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[sx],
            y=[sy],
            z=[sz],
            mode="markers+text",
            text=["S"],
            textposition="bottom center",
            marker=dict(size=5, color="#2ca02c"),
            name="Proyección sobre el elipsoide",
            hovertemplate=(
                f"Lat: {lat:.8f}°<br>"
                f"Lon: {lon:.8f}°<br>"
                f"h: 0.000 m<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[px],
            y=[py],
            z=[pz],
            mode="markers+text",
            text=["P"],
            textposition="top center",
            marker=dict(size=7, color="crimson"),
            name="Punto",
            hovertemplate=(
                f"Lat: {lat:.8f}°<br>"
                f"Lon: {lon:.8f}°<br>"
                f"h real: {h:,.3f} m<br>"
                f"h visual: {h_vis:,.3f} m<extra></extra>"
            ),
        )
    )

    scene = ellipsoid_scene(ell).copy()
    scene["camera"] = camera_from_point(sx, sy, sz)

    fig.update_layout(
        title=title,
        template="plotly_white",
        scene=scene,
        height=650,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig


def build_quadrilateral_patch(vertices: list[dict], ell: Ellipsoid, n_lat: int = 35, n_lon: int = 35, h_offset: float = 80.0):
    unique_vertices = vertices[:-1] if len(vertices) > 1 and vertices[0] == vertices[-1] else vertices

    lats = [v["lat"] for v in unique_vertices]
    lons = [v["lon"] for v in unique_vertices]

    south, north = min(lats), max(lats)
    west, east = min(lons), max(lons)

    lon_grid, lat_grid = np.meshgrid(
        np.linspace(west, east, n_lon),
        np.linspace(south, north, n_lat),
    )

    return geodetic_array_to_ecef(lat_grid, lon_grid, ell, h=h_offset)


def build_quadrilateral_boundary(vertices: list[dict], ell: Ellipsoid, samples: int = 120, h_offset: float = 120.0):
    unique_vertices = vertices[:-1] if len(vertices) > 1 and vertices[0] == vertices[-1] else vertices

    lats = [v["lat"] for v in unique_vertices]
    lons = [v["lon"] for v in unique_vertices]

    south, north = min(lats), max(lats)
    west, east = min(lons), max(lons)

    south_lons = np.linspace(west, east, samples)
    east_lats = np.linspace(south, north, samples)
    north_lons = np.linspace(east, west, samples)
    west_lats = np.linspace(north, south, samples)

    lat_path = np.concatenate([
        np.full(samples, south),
        east_lats,
        np.full(samples, north),
        west_lats,
    ])
    lon_path = np.concatenate([
        south_lons,
        np.full(samples, east),
        north_lons,
        np.full(samples, west),
    ])

    return geodetic_array_to_ecef(lat_path, lon_path, ell, h=h_offset)


def fig_quadrilateral_on_ellipsoid(vertices: list[dict], ell: Ellipsoid) -> go.Figure:
    unique_vertices = vertices[:-1] if len(vertices) > 1 and vertices[0] == vertices[-1] else vertices

    patch_x, patch_y, patch_z = build_quadrilateral_patch(unique_vertices, ell)
    edge_x, edge_y, edge_z = build_quadrilateral_boundary(unique_vertices, ell)

    corner_lats = np.array([v["lat"] for v in unique_vertices], dtype=float)
    corner_lons = np.array([v["lon"] for v in unique_vertices], dtype=float)
    corner_x, corner_y, corner_z = geodetic_array_to_ecef(corner_lats, corner_lons, ell, h=140.0)

    fig = go.Figure()
    add_ellipsoid_surface(fig, ell, opacity=0.50)

    # Parche del cuadrilátero sobre el elipsoide
    fig.add_trace(
        go.Surface(
            x=patch_x,
            y=patch_y,
            z=patch_z,
            surfacecolor=np.ones_like(patch_x),
            colorscale=[[0.0, "#9467bd"], [1.0, "#9467bd"]],
            showscale=False,
            opacity=0.92,
            hoverinfo="skip",
            name="Área del cuadrilátero",
        )
    )

    # Borde
    fig.add_trace(
        go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode="lines",
            line=dict(color="#5e3c99", width=8),
            name="Borde",
        )
    )

    # Vértices
    fig.add_trace(
        go.Scatter3d(
            x=corner_x,
            y=corner_y,
            z=corner_z,
            mode="markers+text",
            text=["V1", "V2", "V3", "V4"],
            textposition="top center",
            marker=dict(size=5, color="crimson"),
            name="Vértices",
        )
    )

    fig.update_layout(
        title=f"Cuadrilátero sobre el elipsoide {ell.name}",
        template="plotly_white",
        scene=ellipsoid_scene(ell),
        height=700,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig

# =========================
# UI
# =========================
st.title("Mini App Geodésica")
st.caption("Demo rápida standalone en Python. Salidas en grados y metros.")

st.sidebar.header("Configuración")
ellipsoid_name = st.sidebar.selectbox("Elipsoide", list(ELLIPSOIDS.keys()), index=0)
ell = get_ellipsoid(ellipsoid_name)

with st.sidebar:
    if st.session_state.get("authenticated", False):
        st.write(f"Sesión: {st.session_state.get('username', 'usuario')}")
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()

module = st.sidebar.radio(
    "Módulo",
    [
        "1. Parámetros del elipsoide",
        "2. Elipse meridiana",
        "3. Geodésicas → Cartesianas",
        "4. Cartesianas → Geodésicas",
        "5. Longitud de arco de paralelo",
        "6. Cuadrilátero geodésico y área",
    ],
)

st.sidebar.markdown("### Resumen del elipsoide")
st.sidebar.write(f"**a:** {ell.a:,.3f} m")
st.sidebar.write(f"**b:** {ell.b:,.3f} m")
st.sidebar.write(f"**e²:** {ell.e2:.12f}")


# =========================
# MÓDULO 1
# =========================
if module == "1. Parámetros del elipsoide":
    st.subheader("Parámetros del elipsoide")

    c1, c2, c3 = st.columns(3)
    c1.metric("Semieje mayor a", f"{ell.a:,.3f} m")
    c2.metric("Semieje menor b", f"{ell.b:,.3f} m")
    c3.metric("Achatamiento f", f"{ell.f:.12f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("1/f", f"{ell.inv_f:.9f}")
    c5.metric("Primera excentricidad² e²", f"{ell.e2:.12f}")
    c6.metric("Segunda excentricidad² e'²", f"{ell.ep2:.12f}")

    st.info(
    'Formatos angulares aceptados: decimal "4.6", "-74.08175" '
    'o GMS "4 36 0 N", "74° 04\' 54.3\\" W".'
)


# =========================
# MÓDULO 2
# =========================

elif module == "2. Elipse meridiana":
    st.subheader("Elipse meridiana")

    with st.form("meridian_form"):
        lat_raw = st.text_input(
            "Latitud para radios M y N (opcional: decimal o GMS)",
            "",
            placeholder='Ej: 4.6  o  4 36 0 N'
        )
        samples_raw = st.text_input("Número de muestras", "360")
        submitted = st.form_submit_button("Calcular")

    if submitted:
        errors: list[str] = []
        latitude = None

        if lat_raw.strip() != "":
            latitude = parse_angle(
                "Latitud",
                lat_raw,
                errors,
                angle_type="lat",
                forbid_zero=False,
            )

        samples = parse_required_int("Número de muestras", samples_raw, errors, 24, 2000)

        if errors:
            show_errors(errors)
        else:
            x, z = generate_meridian_ellipse_points(ell, samples)

            col1, col2 = st.columns([1, 1])

            with col1:
                st.metric("a", f"{ell.a:,.3f} m")
                st.metric("b", f"{ell.b:,.3f} m")
                st.metric("e²", f"{ell.e2:.12f}")

                if latitude is not None:
                    phi = deg_to_rad(latitude)
                    M = meridian_radius(phi, ell)
                    N = prime_vertical_radius(phi, ell)
                    st.metric("Radio meridiano M", f"{M:,.3f} m")
                    st.metric("Radio primer vertical N", f"{N:,.3f} m")

            with col2:
                st.plotly_chart(
                    fig_meridian_ellipse(x, z, ell),
                    use_container_width=True
                )


# =========================
# MÓDULO 3
# =========================

elif module == "3. Geodésicas → Cartesianas":
    st.subheader("Conversión geodésicas → cartesianas ECEF")

    with st.form("geo_to_ecef_form"):
        col1, col2, col3 = st.columns(3)
        lat_raw = col1.text_input("Latitud (decimal o GMS)", "4.6", placeholder='4.6 o 4 36 0 N')
        lon_raw = col2.text_input("Longitud (decimal o GMS)", "-74.0", placeholder='-74.0 o 74 0 0 W')
        h_raw = col3.text_input("Altura (m)", "2600")
        submitted = st.form_submit_button("Convertir")

    if submitted:
        errors: list[str] = []

        lat = parse_angle("Latitud", lat_raw, errors, angle_type="lat", forbid_zero=False)
        lon = parse_angle("Longitud", lon_raw, errors, angle_type="lon", forbid_zero=False)
        h = parse_required_float("Altura", h_raw, errors, -10000.0, 100000.0, forbid_zero=False)

        if errors:
            show_errors(errors)
        else:
            X, Y, Z = geodetic_to_ecef(lat, lon, h, ell)

            c1, c2, c3 = st.columns(3)
            c1.metric("X", f"{X:,.3f} m")
            c2.metric("Y", f"{Y:,.3f} m")
            c3.metric("Z", f"{Z:,.3f} m")

            left, right = st.columns(2)
            with left:
                st.plotly_chart(
                    fig_point_on_ellipsoid(lat, lon, h, ell, "Punto geodésico sobre el elipsoide"),
                    use_container_width=True,
                )
            with right:
                st.plotly_chart(
                    fig_ecef_point(X, Y, Z, "Vector cartesiano ECEF"),
                    use_container_width=True,
                )

# =========================
# MÓDULO 4
# =========================
elif module == "4. Cartesianas → Geodésicas":
    st.subheader("Conversión cartesianas ECEF → geodésicas")

    with st.form("ecef_to_geo_form"):
        col1, col2, col3 = st.columns(3)
        x_raw = col1.text_input("X (m)", "1749871.0")
        y_raw = col2.text_input("Y (m)", "-6111234.0")
        z_raw = col3.text_input("Z (m)", "508123.0")
        submitted = st.form_submit_button("Convertir")

    if submitted:
        errors: list[str] = []

        x = parse_required_float("X", x_raw, errors, forbid_zero=True)
        y = parse_required_float("Y", y_raw, errors, forbid_zero=True)
        z = parse_required_float("Z", z_raw, errors, forbid_zero=True)

        if x is not None and y is not None and z is not None:
            validate_ecef_values(x, y, z, ell, errors)

        if errors:
            show_errors(errors)
        else:
            lat, lon, h, iterations = ecef_to_geodetic(x, y, z, ell)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Latitud", f"{lat:.10f} deg")
            c2.metric("Longitud", f"{lon:.10f} deg")
            c3.metric("Altura", f"{h:,.3f} m")
            c4.metric("Iteraciones", str(iterations))

            left, right = st.columns(2)
            tabs = st.tabs(["ECEF", "Elipsoide global", "Zoom local"])

            with tabs[0]:
                st.plotly_chart(
                    fig_ecef_point(x, y, z, "Punto cartesiano ECEF 3D"),
                    use_container_width=True,
                )

            with tabs[1]:
                st.plotly_chart(
                    fig_point_on_ellipsoid(lat, lon, h, ell, "Resultado geodésico sobre el elipsoide"),
                    use_container_width=True,
                )

            with tabs[2]:
                st.plotly_chart(
                    fig_point_local_zoom(lat, lon, h, ell, "Zoom local: altura y proyección"),
                    use_container_width=True,
                )
                if abs(h) > EPS:
                    st.caption(
                        f"Visualización con exageración vertical: h real = {h:,.3f} m, "
                        f"h visual = {visual_height_for_plot(h):,.3f} m."
                    )
                else:
                    st.caption("Como h = 0, el punto coincide exactamente con su proyección sobre el elipsoide.")
            with right:
                st.plotly_chart(
                    fig_point_on_ellipsoid(lat, lon, h, ell, "Resultado geodésico sobre el elipsoide"),
                    use_container_width=True,
                )


# =========================
# MÓDULO 5
# =========================
elif module == "5. Longitud de arco de paralelo":
    st.subheader("Longitud de arco de paralelo")

    with st.form("parallel_arc_form"):
        col1, col2, col3 = st.columns(3)
        lat_raw = col1.text_input("Latitud (decimal o GMS)", "4.6", placeholder='4.6 o 4 36 0 N')
        lon1_raw = col2.text_input("Longitud inicial (decimal o GMS)", "-74.2", placeholder='-74.2 o 74 12 0 W')
        lon2_raw = col3.text_input("Longitud final (decimal o GMS)", "-73.8", placeholder='-73.8 o 73 48 0 W')
        submitted = st.form_submit_button("Calcular")

    if submitted:
        errors: list[str] = []

        lat = parse_angle("Latitud", lat_raw, errors, angle_type="lat", forbid_zero=False)
        lon1 = parse_angle("Longitud inicial", lon1_raw, errors, angle_type="lon", forbid_zero=False)
        lon2 = parse_angle("Longitud final", lon2_raw, errors, angle_type="lon", forbid_zero=False)

        if lat is not None and abs(abs(lat) - 90.0) < EPS:
            errors.append("• Latitud: no se permite ±90° en el arco de paralelo.")
        if lon1 is not None and lon2 is not None and abs(lon1 - lon2) < EPS:
            errors.append("• La longitud inicial y final no pueden ser iguales.")

        if errors:
            show_errors(errors)
        else:
            arc, dlon = parallel_arc_length(lat, lon1, lon2, ell)

            c1, c2 = st.columns(2)
            c1.metric("ΔLongitud", f"{dlon:.10f} deg")
            c2.metric("Longitud de arco", f"{arc:,.3f} m")

            st.plotly_chart(
                fig_parallel_arc(lat, lon1, lon2),
                use_container_width=True,
            )


# =========================
# MÓDULO 6
# =========================
elif module == "6. Cuadrilátero geodésico y área":
    st.subheader("Cuadrilátero geodésico y área")

    with st.form("quadrilateral_form"):
        row1 = st.columns(2)
        row2 = st.columns(2)

        lat1_raw = row1[0].text_input("Latitud 1 (decimal o GMS)", "4.4", placeholder='4.4 o 4 24 0 N')
        lon1_raw = row1[1].text_input("Longitud 1 (decimal o GMS)", "-74.2", placeholder='-74.2 o 74 12 0 W')
        lat2_raw = row2[0].text_input("Latitud 2 (decimal o GMS)", "4.8", placeholder='4.8 o 4 48 0 N')
        lon2_raw = row2[1].text_input("Longitud 2 (decimal o GMS)", "-73.8", placeholder='-73.8 o 73 48 0 W')

        submitted = st.form_submit_button("Calcular")

    if submitted:
        errors: list[str] = []

        lat1 = parse_angle("Latitud 1", lat1_raw, errors, angle_type="lat", forbid_zero=False)
        lon1 = parse_angle("Longitud 1", lon1_raw, errors, angle_type="lon", forbid_zero=False)
        lat2 = parse_angle("Latitud 2", lat2_raw, errors, angle_type="lat", forbid_zero=False)
        lon2 = parse_angle("Longitud 2", lon2_raw, errors, angle_type="lon", forbid_zero=False)

        if lat1 is not None and lat2 is not None and abs(lat1 - lat2) < EPS:
            errors.append("• Las latitudes no pueden ser iguales.")
        if lon1 is not None and lon2 is not None and abs(lon1 - lon2) < EPS:
            errors.append("• Las longitudes no pueden ser iguales.")
        if lon1 is not None and lon2 is not None and abs(lon2 - lon1) > 180.0:
            errors.append("• Esta demo no admite cuadriláteros que crucen el antimeridiano.")
        if lat1 is not None and abs(abs(lat1) - 90.0) < EPS:
            errors.append("• Latitud 1: no se permiten polos exactos.")
        if lat2 is not None and abs(abs(lat2) - 90.0) < EPS:
            errors.append("• Latitud 2: no se permiten polos exactos.")

        if errors:
            show_errors(errors)
        else:
            try:
                result = geodetic_quadrilateral(lat1, lon1, lat2, lon2, ell)

                c1, c2, c3 = st.columns(3)
                c1.metric("Paralelo sur", f"{result['south_parallel_length']:,.3f} m")
                c2.metric("Paralelo norte", f"{result['north_parallel_length']:,.3f} m")
                c3.metric("Área", f"{result['area_m2']:,.3f} m²")

                c4, c5, c6 = st.columns(3)
                c4.metric("Meridiano oeste", f"{result['west_meridian_length']:,.3f} m")
                c5.metric("Meridiano este", f"{result['east_meridian_length']:,.3f} m")
                c6.metric("Área", f"{result['area_km2']:,.6f} km²")

                st.plotly_chart(
                    fig_quadrilateral_on_ellipsoid(result["vertices"], ell),
                    use_container_width=True,
                )

                with st.expander("Vértices"):
                    st.json(result["vertices"])

            except ValueError as exc:
                st.error(str(exc))