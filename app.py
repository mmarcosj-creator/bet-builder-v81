
import os
import json
import time
import traceback
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

import bet_builder_v8_1_robust as engine


# ============================================================
# CONFIG
# ============================================================

APP_VERSION = "V8.1 ROBUST MOBILE"
DATA_DIR = Path("app_data")
DATA_DIR.mkdir(exist_ok=True)

META_FILE = DATA_DIR / "last_run.json"
TOP_FILE = DATA_DIR / "latest_top.csv"
VAR_FILE = DATA_DIR / "latest_variants.csv"
ALL_FILE = DATA_DIR / "latest_all.csv"

# Si una ventana sigue vigente no se recalcula automáticamente.
# El usuario siempre puede pulsar "Actualizar ahora".
AUTO_REFRESH_HOURS = 12

st.set_page_config(
    page_title="Bet Builder V8.1",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
      .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1180px;
      }

      .hero {
        padding: 1.05rem 1.15rem;
        border-radius: 20px;
        border: 1px solid rgba(128,128,128,.18);
        background: linear-gradient(135deg, rgba(16,185,129,.12), rgba(59,130,246,.08));
        margin-bottom: .8rem;
      }

      .hero h1 {
        margin: 0;
        font-size: clamp(1.6rem, 6vw, 2.4rem);
        line-height: 1.05;
      }

      .hero p {
        margin: .45rem 0 0 0;
        opacity: .78;
      }

      .pill {
        display: inline-block;
        padding: .28rem .62rem;
        border-radius: 999px;
        font-weight: 750;
        font-size: .78rem;
        margin-right: .35rem;
        margin-top: .4rem;
      }

      .green { background: rgba(34,197,94,.16); color: #16a34a; }
      .amber { background: rgba(245,158,11,.18); color: #d97706; }
      .gray  { background: rgba(107,114,128,.16); color: #6b7280; }
      .blue  { background: rgba(59,130,246,.15); color: #2563eb; }
      .red   { background: rgba(239,68,68,.14); color: #dc2626; }

      .game-card {
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 18px;
        padding: .95rem 1rem;
        margin-bottom: .7rem;
        background: rgba(128,128,128,.035);
      }

      .game-title {
        font-weight: 800;
        font-size: 1.05rem;
        margin-bottom: .2rem;
      }

      .game-sub {
        opacity: .70;
        font-size: .86rem;
      }

      .kv {
        display: grid;
        grid-template-columns: repeat(2, minmax(0,1fr));
        gap: .5rem;
        margin-top: .75rem;
      }

      .kv > div {
        border-radius: 12px;
        padding: .55rem .65rem;
        background: rgba(128,128,128,.06);
      }

      .kv b {
        display:block;
        font-size: .76rem;
        opacity:.68;
        margin-bottom:.08rem;
      }

      .kv span {
        font-size: 1rem;
        font-weight: 800;
      }

      .section-title {
        font-size: 1.05rem;
        font-weight: 800;
        margin: .6rem 0 .45rem 0;
      }

      @media (min-width: 700px) {
        .kv {
          grid-template-columns: repeat(4, minmax(0,1fr));
        }
      }

      div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.14);
        border-radius: 16px;
        padding: .65rem .8rem;
        background: rgba(128,128,128,.025);
      }

      .stButton button, .stDownloadButton button {
        min-height: 46px;
        border-radius: 13px;
        font-weight: 750;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def safe_float(v, default=np.nan):
    try:
        x = float(v)
        return x if np.isfinite(x) else default
    except Exception:
        return default


def pct(v):
    x = safe_float(v)
    return "—" if pd.isna(x) else f"{x*100:.1f}%"


def num(v, digits=2):
    x = safe_float(v)
    return "—" if pd.isna(x) else f"{x:.{digits}f}"


def load_meta():
    if not META_FILE.exists():
        return {}
    try:
        return json.loads(META_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_meta(meta):
    META_FILE.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_csv(path):
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        if "Fecha" in df.columns:
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def cache_is_current(meta):
    if not meta:
        return False

    try:
        now = datetime.now(engine.TZ_PERU)
        end = pd.Timestamp(meta["window_end"]).date()
        generated = datetime.fromisoformat(meta["generated_at"])

        if generated.tzinfo is None:
            age_hours = 999
        else:
            age_hours = (now - generated).total_seconds() / 3600

        return now.date() <= end and age_hours <= AUTO_REFRESH_HOURS

    except Exception:
        return False


def run_model():
    inicio, fin = engine.ventana_objetivo()

    hist = engine.descargar_historico_total()
    ds, estados = engine.construir_dataset_v81(hist)

    schedule_index = engine.construir_schedule_index(hist)
    perfiles = engine.construir_perfil_arbitros(hist)

    context_h1 = engine.descargar_contexto_h1()

    fixtures = engine.descargar_fixtures_objetivo(inicio, fin)

    resultado, variantes = engine.pronosticar_v81(
        fixtures,
        ds,
        estados,
        perfiles,
        schedule_index,
        context_h1,
    )

    top = engine.crear_top30_v81(resultado)

    top.to_csv(TOP_FILE, index=False, encoding="utf-8-sig")
    variantes.to_csv(VAR_FILE, index=False, encoding="utf-8-sig")
    resultado.to_csv(ALL_FILE, index=False, encoding="utf-8-sig")

    # También genera el Excel técnico.
    engine.exportar_v81(
        top,
        variantes,
        resultado,
        inicio,
        fin,
    )

    meta = {
        "generated_at": datetime.now(engine.TZ_PERU).isoformat(),
        "window_start": str(pd.Timestamp(inicio).date()),
        "window_end": str(pd.Timestamp(fin).date()),
        "n_top": int(len(top)),
        "n_bets": int((top["Accion"] == "APOSTAR").sum()) if not top.empty else 0,
        "n_watch": int((top["Accion"] == "VIGILAR").sum()) if not top.empty else 0,
        "version": APP_VERSION,
    }

    save_meta(meta)

    return top, variantes, resultado, meta


def maybe_auto_generate():
    meta = load_meta()

    if cache_is_current(meta):
        return (
            load_csv(TOP_FILE),
            load_csv(VAR_FILE),
            load_csv(ALL_FILE),
            meta,
            False,
        )

    with st.status(
        "Actualizando la próxima ventana de 7 días…",
        expanded=True,
    ) as status:
        st.write("Descargando histórico y calendario…")
        top, var, all_df, meta = run_model()
        status.update(
            label="Pronósticos actualizados",
            state="complete",
            expanded=False,
        )

    return top, var, all_df, meta, True


def action_class(action):
    if action == "APOSTAR":
        return "green"
    if action == "VIGILAR":
        return "amber"
    return "gray"


def phase_label(v):
    mapping = {
        "COLD_START": "Inicio",
        "EARLY": "Temprana",
        "STABLE": "Estable",
        "LATE": "Tardía",
    }
    return mapping.get(str(v), str(v))


def render_game_card(row):
    action = str(row.get("Accion", ""))
    klass = action_class(action)

    comp = str(row.get("Competicion", ""))
    local = str(row.get("Local", ""))
    visita = str(row.get("Visitante", ""))
    fecha = row.get("Fecha", "")
    hora = str(row.get("HoraPeru", ""))

    if pd.notna(fecha):
        try:
            fecha_txt = pd.Timestamp(fecha).strftime("%d/%m")
        except Exception:
            fecha_txt = str(fecha)
    else:
        fecha_txt = ""

    variant = str(row.get("VarianteMasSegura", "—"))
    rel = pct(row.get("ReliabilityScore"))
    pbase = pct(row.get("P_BASE_Ajustada"))
    qmin = num(row.get("CuotaMinMasSegura"))

    altitude = safe_float(row.get("ElevationM"))
    alt_txt = "—" if pd.isna(altitude) else f"{altitude:.0f} m"

    html = f"""
    <div class="game-card">
      <div>
        <span class="pill {klass}">{action}</span>
        <span class="pill blue">{comp}</span>
      </div>

      <div class="game-title">{local} vs {visita}</div>
      <div class="game-sub">{fecha_txt} · {hora} PET · {variant}</div>

      <div class="kv">
        <div><b>Prob. base</b><span>{pbase}</span></div>
        <div><b>Fiabilidad</b><span>{rel}</span></div>
        <div><b>Cuota mínima</b><span>{qmin}</span></div>
        <div><b>Altitud</b><span>{alt_txt}</span></div>
      </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

    with st.expander("Ver análisis técnico"):
        c1, c2, c3 = st.columns(3)

        c1.metric("Underdog marca", pct(row.get("P_DogGol_Ajustada")))
        c2.metric("Favorito 4+ córners", pct(row.get("P_Fav4_Ajustada")))
        c3.metric("Under 4.5", pct(row.get("P_Under45_Ajustada")))

        st.caption(
            f"Fase local: {phase_label(row.get('PhaseHome'))} · "
            f"Fase visita: {phase_label(row.get('PhaseAway'))} · "
            f"Descanso: {num(row.get('DaysRestHome'),1)} / "
            f"{num(row.get('DaysRestAway'),1)} días"
        )

        notes = [
            row.get("TrendNote", ""),
            row.get("FatigueNote", ""),
            row.get("AltitudeNote", ""),
            row.get("RefereeNote", ""),
            row.get("ClimateNote", ""),
        ]

        notes = [
            str(x)
            for x in notes
            if str(x).strip()
            and str(x).lower() != "nan"
        ]

        if notes:
            st.info(" · ".join(notes))


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
      <h1>⚽ Bet Builder V8.1</h1>
      <p>Panel móvil robusto · hasta 30 oportunidades · cuota mínima 4.20</p>
      <span class="pill green">APOSTAR</span>
      <span class="pill amber">VIGILAR</span>
      <span class="pill blue">ROBUST</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD / AUTO REFRESH
# ============================================================

try:
    top, variants, all_df, meta, refreshed = maybe_auto_generate()

except Exception as e:
    st.error("No fue posible actualizar el modelo.")
    st.code(str(e))
    with st.expander("Detalle técnico"):
        st.code(traceback.format_exc())

    top = load_csv(TOP_FILE)
    variants = load_csv(VAR_FILE)
    all_df = load_csv(ALL_FILE)
    meta = load_meta()


# ============================================================
# CONTROLS
# ============================================================

left, right = st.columns([1, 1])

with left:
    if st.button(
        "🔄 Actualizar ahora",
        use_container_width=True,
        type="primary",
    ):
        try:
            with st.status(
                "Ejecutando V8.1 ROBUST…",
                expanded=True,
            ) as status:
                top, variants, all_df, meta = run_model()
                status.update(
                    label="Actualización terminada",
                    state="complete",
                    expanded=False,
                )
            st.rerun()

        except Exception as e:
            st.error(str(e))

with right:
    excel_path = Path(engine.ARCHIVO_XLSX_V81)

    if excel_path.exists():
        st.download_button(
            "📊 Descargar Excel técnico",
            data=excel_path.read_bytes(),
            file_name=excel_path.name,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )


# ============================================================
# STATUS
# ============================================================

if meta:
    start = meta.get("window_start", "—")
    end = meta.get("window_end", "—")
    generated = meta.get("generated_at", "")

    try:
        gen_txt = datetime.fromisoformat(generated).strftime("%d/%m %H:%M")
    except Exception:
        gen_txt = generated

    st.caption(
        f"Ventana: {start} → {end} · Última actualización: {gen_txt}"
    )


# ============================================================
# KPIs
# ============================================================

if not top.empty:
    c1, c2, c3, c4 = st.columns(4)

    n_bets = int((top["Accion"] == "APOSTAR").sum())
    n_watch = int((top["Accion"] == "VIGILAR").sum())
    avg_rel = pd.to_numeric(
        top["ReliabilityScore"],
        errors="coerce",
    ).mean()

    min_q = pd.to_numeric(
        top["CuotaMinMasSegura"],
        errors="coerce",
    ).min()

    c1.metric("Apostar", n_bets)
    c2.metric("Vigilar", n_watch)
    c3.metric("Fiabilidad media", pct(avg_rel))
    c4.metric("Cuota mínima", num(min_q))


# ============================================================
# FILTERS
# ============================================================

st.markdown('<div class="section-title">Partidos</div>', unsafe_allow_html=True)

if top.empty:
    st.warning(
        "No hay candidatos suficientes en esta ventana. "
        "V8.1 no rellena apuestas solo para llegar a 30."
    )

else:
    f1, f2 = st.columns(2)

    actions = ["TODOS"] + sorted(
        top["Accion"].dropna().astype(str).unique().tolist()
    )

    comps = ["TODAS"] + sorted(
        top["Competicion"].dropna().astype(str).unique().tolist()
    )

    action_sel = f1.selectbox(
        "Estado",
        actions,
    )

    comp_sel = f2.selectbox(
        "Competición",
        comps,
    )

    view = top.copy()

    if action_sel != "TODOS":
        view = view[
            view["Accion"] == action_sel
        ]

    if comp_sel != "TODAS":
        view = view[
            view["Competicion"] == comp_sel
        ]

    st.caption(
        f"Mostrando {len(view)} de {len(top)} oportunidades."
    )

    for _, row in view.iterrows():
        render_game_card(row)


# ============================================================
# VARIANTS
# ============================================================

with st.expander("🧪 Comparar variantes y cuotas"):
    if variants.empty:
        st.write("No hay variantes calculadas.")
    else:
        cols = [
            c
            for c in [
                "Fecha",
                "Competicion",
                "Local",
                "Visitante",
                "AccionPartido",
                "Variante",
                "P_Conjunta",
                "CuotaJusta",
                "CuotaMinExigida",
                "Evidencia",
            ]
            if c in variants.columns
        ]

        st.dataframe(
            variants[cols],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# INSTALL HELP
# ============================================================

with st.expander("📱 Cómo dejarlo como app en Android"):
    st.markdown(
        """
        1. Abre esta página en **Chrome**.
        2. Toca **⋮** arriba a la derecha.
        3. Elige **Añadir a pantalla de inicio**.
        4. Ponle el nombre **Bet Builder V8.1**.
        5. Desde ese icono podrás abrir el panel directamente.

        La app revisa la ventana guardada al abrirse. Si la ventana ya venció,
        genera automáticamente la siguiente. También puedes pulsar
        **Actualizar ahora** cuando quieras.
        """
    )

st.caption(
    "Modelo estadístico experimental. No garantiza beneficios. "
    "Usar solo cuando la cuota real sea ≥ la cuota mínima exigida."
)
