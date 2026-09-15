
# Bet Builder V8.1 ROBUST Mobile

## Qué es

Interfaz móvil para el motor `bet_builder_v8_1_robust.py`.

Incluye:

- actualización automática cuando vence la ventana de 7 días;
- botón **Actualizar ahora**;
- máximo 30 oportunidades, sin forzar apuestas;
- tarjetas visuales APOSTAR / VIGILAR;
- probabilidad BASE, fiabilidad, cuota mínima y contexto;
- comparación de variantes;
- descarga del Excel técnico;
- soporte para un refresco programado diario mediante GitHub Actions.

## Ejecutar en PC

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usarlo desde el teléfono

La opción recomendada es alojarlo en Streamlit Community Cloud.

1. Crear un repositorio de GitHub.
2. Subir todos los archivos de esta carpeta.
3. Abrir https://share.streamlit.io
4. Conectar el repositorio.
5. Elegir `app.py`.
6. Deploy.
7. Abrir la URL desde Chrome en Android.
8. Chrome > menú ⋮ > **Añadir a pantalla de inicio**.

Quedará un icono directo en el teléfono.

## Actualización

### Al abrir la app
La app comprueba la última ventana. Si está vencida o el cache tiene más de
12 horas, ejecuta de nuevo V8.1.

### Sin abrir el teléfono
El archivo `.github/workflows/refresh.yml` está preparado para ejecutar
`scheduled_refresh.py` una vez al día aproximadamente a las 06:15 hora de Perú.

En GitHub debes permitir a Actions escribir en el repositorio:

Settings > Actions > General > Workflow permissions > Read and write permissions.

El cron puede variar algunos minutos porque GitHub no garantiza el segundo exacto.

## Importante

El motor utiliza fuentes públicas externas. Una caída, cambio de endpoint o
rate-limit puede impedir temporalmente la actualización.

La app no convierte el modelo en una garantía de beneficio.
La regla sigue siendo: cuota real >= CuotaMinExigida y nunca < 4.20.
