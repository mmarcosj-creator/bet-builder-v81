
"""
Ejecutor sin interfaz.
Útil para un cron/GitHub Actions si se desea mantener los datos
actualizados aunque nadie abra la web.
"""

import json
from pathlib import Path
from datetime import datetime

import pandas as pd

import bet_builder_v8_1_robust as engine

DATA_DIR = Path("app_data")
DATA_DIR.mkdir(exist_ok=True)


def run():
    inicio, fin = engine.ventana_objetivo()

    hist = engine.descargar_historico_total()
    ds, estados = engine.construir_dataset_v81(hist)

    schedule = engine.construir_schedule_index(hist)
    referees = engine.construir_perfil_arbitros(hist)
    h1 = engine.descargar_contexto_h1()

    fixtures = engine.descargar_fixtures_objetivo(inicio, fin)

    result, variants = engine.pronosticar_v81(
        fixtures,
        ds,
        estados,
        referees,
        schedule,
        h1,
    )

    top = engine.crear_top30_v81(result)

    top.to_csv(DATA_DIR / "latest_top.csv", index=False, encoding="utf-8-sig")
    variants.to_csv(
        DATA_DIR / "latest_variants.csv",
        index=False,
        encoding="utf-8-sig",
    )
    result.to_csv(DATA_DIR / "latest_all.csv", index=False, encoding="utf-8-sig")

    engine.exportar_v81(
        top,
        variants,
        result,
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
    }

    (DATA_DIR / "last_run.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    run()
