# BIBLIA · La Racha
> Estado: borrador · Versión: 0.1
> La aprobación humana se registra en `proyecto.json` (firma, fecha y versión), no aquí.

> **Atribución.** Esto NO es una campaña del Gobierno de España ni de ningún organismo
> público, y no puede presentarse como tal: ni escudo, ni ministerio, ni tipografía
> institucional, ni cartela final de organismo. Es una pieza de autor sobre ludopatía
> juvenil. Firmarla como institucional sería suplantación, y además es exactamente lo
> que las plataformas persiguen como contenido no auténtico
> (`docs/conocimiento/03_plataformas_y_monetizacion.md`). Si algún día la respalda un
> organismo de verdad, lo firma él.

## 1. Concepto
- Logline: Un chico de diecinueve años entra en el salón de juegos de su barrio con la
  misma naturalidad con la que entraría en clase, y nadie a su alrededor lo nota.
- Género y tono: realismo documental, seco. Sin música, sin voz en off, sin moraleja.
- Público y plataforma: 16–25, TikTok vertical.
- Promesa del formato: la pieza no cuenta una tragedia; cuenta una rutina. Ahí está el golpe.
- Producibilidad IA: 9/10 · un personaje, dos localizaciones interiores/exteriores
  cerradas, cero acción física complicada, cero diálogo hablado.

## 2. Fórmula de episodio (61–90 s, 9:16)
- 0–3 s gancho: un primer plano de su cara, cruzada por una luz roja y verde que
  parpadea. No sabemos qué está mirando.
- Giro central: el móvil vibra en la repisa del terminal. Lo silencia sin apartar la
  vista de la pantalla.
- Cierre: la máquina deja de parpadear. Su cara se queda a oscuras. Corta.

## 3. Mundo y reglas
- Época y lugar: una ciudad de provincia española, hoy, a la hora de cenar.
- Reglas del mundo:
  - Nadie le dice nada. No hay antagonista.
  - No se ve ganar ni perder: no sabemos cuánto lleva. El espectador rellena.
  - No aparece dinero contado en primer plano ni texto legible en pantalla.
- Regla visual narrativa: **el rojo sólo aparece donde está el juego.** La calle es
  ámbar y azul; el salón es lo único rojo de la pieza.

## 4. Personajes
### @char_la-racha_Nil_v1
- Descriptor congelado: Young man, nineteen, thin build, short dark curly hair, faint acne scars on the left cheek, a black fabric wristband on the right wrist, black hooded sweatshirt over a grey t-shirt, cheap white earphones with a frayed cable.
- Anclas de identidad: cicatrices de acné en la mejilla izquierda · pulsera negra de
  tela en la muñeca derecha · auriculares blancos con el cable pelado
- VOZ LOCK: no habla en toda la pieza. Sólo respiración.
- Máscara pública: un chico normal volviendo a casa
- Qué la rompe: nada. Esa es la idea
- Hábitos físicos: se quita un solo auricular cuando va a entrar, nunca los dos
- Forma de caminar: rápido, con la mochila colgando de un hombro
- Objetivo: llegar a la máquina antes de que le dé tiempo a pensarlo

## 5. Localizaciones
### @loc_la-racha_Calle_v1
- Descripción: A narrow street in a Spanish provincial city at dusk: four-storey cream facades with green louvred shutters and wrought-iron balconies, a tiled bar front with a dark green awning, warm sodium streetlights, wet pavement, parked scooters against the kerb.
- Mapa espacial vertical: Nil baja por la acera de la izquierda, la fachada del bar a su
  derecha, la calle se hunde al fondo. La cámara mira calle abajo.
- Estados: atardecer (sodio encendido, cielo aún azul) · noche

### @loc_la-racha_Salon_v1
- Descripción: A small ground-floor gaming arcade: a row of slot terminals along the right wall, one roulette terminal at the back, red and green screen light on a dark patterned carpet, low ceiling of square panels, a counter with a dead plant camera-left.
- Mapa espacial vertical: Nil de pie frente al terminal del fondo, el mostrador a su
  izquierda de cámara, la fila de máquinas a su derecha. La cámara mira hacia el fondo.
- Estados: noche (única luz, las pantallas)

## 6. Props
Ninguno registrado: el móvil y la mochila salen en plano pero no se manipulan en primer
plano, porque el modelo deforma las manos.

## 7. Estilo (ver style.md)
## 8. Arco de temporada (ver temporada.json)

## 9. Riesgos de producción
- Nada de manos contando billetes ni pulsando botones en primer plano: dedos deformes.
- Ningún texto legible: ni el cartel del salón, ni la pantalla, ni el móvil. El del
  móvil se resuelve con el nombre pronunciado fuera de campo o en la cartela de post.
- La cartela final va en montaje con FFmpeg, **nunca** pedida al modelo.
- Sin monumentos reconocibles: el modelo los deforma. La ciudad se reconoce por
  persianas verdes, balcones de hierro, toldo del bar y farola de sodio.
- Sin otras personas identificables en cuadro: figurantes sólo desenfocados al fondo.
- Sin logotipos de casas de apuestas reales: marcas inventadas y fuera de foco.
