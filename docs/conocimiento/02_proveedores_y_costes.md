# Proveedores de modelos y coste por episodio
Fecha: 2026-09-11 · Precios en USD por segundo generado. C = confirmado en la web del proveedor; U = fuente secundaria.

## Hallazgos clave
- Higgsfield revende modelos de terceros. Por API directa o a través de agregadores, el mismo Seedance sale más barato.
- Seedance 2.5 genera de forma nativa solo a 480p y 720p (fal no ofrece 1080p, C). El "1080p" es escalado: generar a 720p y escalar por nuestra cuenta.
- La mayor palanca de coste son los reintentos (hipótesis actual: 400 s generados por cada 90 s finales).

## Precios de referencia
| Ruta | 480p | 720p | Estado |
|---|---|---|---|
| Seedance 2.5 · Higgsfield | 0,15 | 0,325 | base |
| Seedance 2.5 · BytePlus ModelArk / Replicate | 0,103 | 0,231 | U |
| Seedance 2.5 · fal | 0,22 | 0,47 | C (evitar) |
| Seedance 2.0 · OpenRouter | 0,067 | ~0,15 | C/derivado |
| Seedance 2.0 Fast · OpenRouter | desde 0,04 | ~0,09 | C |
| Kling 3.0 Standard (con audio) · fal | – | 0,126 | C |
| Vidu Q3 Turbo (oficial) | – | 0,035–0,065; ~-50 % en horas valle | C |
| Wan 3.0 (pesos cerrados) | – | 0,10 | C |
| LTX-2.5 autoalojado en RTX 5090 | – | ~0,01–0,02 | U |

Licencias de modelos abiertos: LTX gratis por debajo de 10 M$ de ingresos anuales; Wan 2.2 Apache 2.0; HunyuanVideo 1.5 y los pesos de MiniMax H3 excluyen la UE (no usar).
Imágenes: Seedream 5.0 Lite/4.5 ~0,035–0,04 por imagen; Nano Banana 2 con Batch API -50 %.

## Pipeline por niveles
1. Borradores/animatics: Seedance 2.0 Fast a 480p (0,04), con los mismos prompts que 2.0/2.5.
2. Mayoría de planos: Seedance 2.0 (~0,15 a 720p).
3. Planos clave: Seedance 2.5 directo (0,231 a 720p) + escalado propio.
4. Planos sin diálogo en lotes nocturnos: Vidu Q3 Turbo en horas valle.
5. Volumen alto (>50 episodios/mes): LTX-2.5 autoalojado para planos de recurso, extensiones y reintentos.

## Coste por episodio de 90 s (400 s generados + ~40 imágenes)
- Higgsfield: 130–180 $
- A · Seedance 2.5 directo: ~95 $
- B · niveles vía API: ~45 $
- C · niveles + autoalojado: ~30–35 $ (+ GPU y operación)
- B con 250 s generados (menos reintentos gracias a la skill): ~30 $

## Pendiente de verificar
Precio oficial de BytePlus en la consola (y disponibilidad en España), Veo 3.1 a 1080p, precio USD por crédito de Kling, calidad de LTX-2.5 frente a Seedance en prueba ciega propia.
