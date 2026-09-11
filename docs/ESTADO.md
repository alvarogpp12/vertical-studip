# Estado del proyecto
> Claude Code: lee este archivo al empezar cada sesión y actualízalo al terminar (qué se hizo, qué falta, bloqueos).

## Última actualización
2026-09-11 · Repo publicado en alvarogpp12/vertical-studip. Entorno de desarrollo verificado, etiquetas/fases/issues creados, CI en verde.

## Hecho
- Investigación: sistema director, 12 reglas del top 30 de Higgsfield, vertical 9:16, proveedores y costes, políticas de plataformas.
- Entorno verificado en Mac: `uv` + Python 3.12.14 + dependencias; `pytest` en verde y `showrunner doctor` sin fallos salvo claves. No se usó `setup_mac.sh` entero: instalaría node por brew pisando nvm y duplicaría Claude Code.
- Corregido un fallo del QC: `fotogramas.extraer()` pedía un fotograma en `t == dur` y ffmpeg fallaba. Afectaba a todo clip de duración par con el `cada_seg` por defecto. PR #1.
- v0.1: CLI `showrunner`, router de modelos por nivel, límites de gasto, ledger, conectores fal y BytePlus (este sin verificar), proveedor mock, QC técnico, plantillas de serie, skills base, CI.

## En curso · Fase 0 · Cimientos
- [ ] Claves en `.env`: Anthropic, BytePlus, fal, R2
- [ ] Issue #3 · Verificar conector BytePlus con llamada real
- [ ] Issue #4 · Precios reales de consola en `config/modelos.yaml`
- [ ] Issue #5 · Subida de referencias a R2

## Pendiente del usuario
- 3 ideas de serie (1–3 frases) · plataforma principal · presupuesto del primer mes

## Bloqueos
- Ninguno conocido.
