---
name: director-vertical
description: Escribe prompts de vídeo para Seedance/Kling en formato vertical 9:16 a partir de la biblia, registry.json y shotlist.json de una serie. Úsala siempre que haya que convertir un plano de la lista de planos en un prompt de generación, o revisar por qué una toma falló.
---
# Director vertical · v0.1

## Antes de escribir (fases silenciosas, no se muestran)
1. Leer `biblia.md`, `style.md`, `voces.md`, `registry.json` y el plano en `shotlist.json`.
2. Descomponer: referencias activas, mapa espacial, primer fotograma, mirada, lado de cámara.
3. Limpiar: quitar tags, frases o números de escena heredados de otros planos. Cada prompt es una isla.
4. Comprobaciones de fallo (cada riesgo detectado se convierte en un bloqueo positivo):
   - ¿Puede el primer fotograma salir vacío o con otro personaje?
   - ¿Pueden invertirse izquierda/derecha o romperse el eje?
   - ¿Puede un prop cambiar de mano o de estado?
   - ¿Hay más acción de la que cabe en la duración?
   - ¿El diálogo supera ~4 palabras/s + 1 s de cola?
   - ¿Hay vocabulario que active filtros (desvestir, arrancar…)? Reformular.
   - ¿Pide algo que el modelo hace mal (transformación en cámara, rebobinado, multitud)? Rediseñar el plano.
5. Entregar SOLO el prompt.
6. Pasar el linter antes de gastar: `showrunner valida prompt <archivo> --serie <slug> --plano s01_ep01_shNNN`. Si devuelve errores, corrige; no se genera nada hasta que salga limpio.

## Estructura fija del prompt
STYLE PREFIX (copiado de style.md) · SCENE CONTEXT · ACTIVE REFERENCES (cada @tag con su función) · LOCATION MAP (vertical, anclado a objetos visibles) · FIRST FRAME · SEGMENTS (tiempos) · DIALOGUE · PERFORMANCE (tarea, no emoción; estados, no transiciones; ojos vivos) · CAMERA (1 movimiento máx.) · LIGHTING · PHYSICS · AUDIO ("No music") · CONSTRAINTS (copiado) · POSITIVE LOCKS ("… = toma fallida").

## Reglas de oro
R-01 Nada se rueda sin estar en registry.json.
R-02 Descriptores y voice locks palabra por palabra en cada prompt.
R-04 Localización: "controls geometry, materials and light only, never framing"; nada fuera de lo que muestra.
R-06 Primer plano de cada escena: máster de 1 s sin acción para fijar geografía.
R-07 Nunca "triste/enfadado/asustado": objetivo, obstáculo, táctica.
R-08 Describe lo que quieres; los límites como condición de toma fallida.
R-09 "No music" siempre; el diálogo cabe a ~4 palabras/s + 1 s de cola limpia (lo comprueba `valida plano`).
R-11 Al corregir, cambia UNA línea. Tras 20 fallos el plano se bloquea solo: cambia el plano.
Los ids de plano son siempre `s01_ep01_sh003`.

## Vertical 9:16
- Ojos en el tercio superior; quinto inferior libre para subtítulos; márgenes de interfaz 130 px arriba / 320 px abajo en 1080×1920.
- Diálogo a dos: plano/contraplano o escalonado en profundidad, nunca two-shot lateral.
- Cámara: tilt, push-in, pull-back; sin travellings laterales ni cámara en mano.
- Primer plano y plano medio; ópticas 50/85 mm.

## Niveles de generación
borrador = Seedance 2.0 Fast 480p · trabajo = Seedance 2.0 / Kling 720p · clave = Seedance 2.5 720p. Un prompt aprobado en borrador pasa igual al siguiente nivel.
