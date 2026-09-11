# Fallos del showrunner: los que se pagan 200 veces

> **Procedencia.** Códigos y reglas **[V]**; diagnósticos **[H]**.

Un fallo aquí no cuesta un plano: cuesta la serie entera, porque todo lo de abajo lo
hereda. Un descriptor flojo se paga una vez por plano, doscientas veces por temporada.

| Síntoma, meses después | Causa en la biblia | Arreglo |
|---|---|---|
| La cara del personaje cambia entre planos | Descriptor sin anclas, o con adjetivos en vez de rasgos | Reescribe el descriptor: edad, pelo, 2–3 marcas, ropa. Versión nueva del asset (R-01) |
| El QC no sabe decir si es la misma persona | No hay anclas comprobables en un fotograma | Anclas pequeñas, permanentes y visibles en primer plano |
| Cada episodio suena a otra serie | Se tocó el STYLE PREFIX a mitad de temporada | Es inmutable (R-03). Si de verdad hay que cambiarlo, es una temporada nueva |
| Los contraplanos salen invertidos | La localización no tiene mapa ni eje | Añade el mapa con posiciones ancladas a objetos y «la cámara mira al…» |
| El guionista pide assets que no existen | La biblia tiene menos personajes de los que la historia necesita | O sube el casting (y el coste), o recorta la historia. No lo decide el guionista |
| Cada episodio cuesta el doble de lo previsto | Concepto con producibilidad baja aprobado igual | Por debajo de 6/10 se rediseña el concepto, no se aprieta la producción |
| La serie se agota en el episodio 4 | Premisa en vez de motor | El motor tiene fuente de conflicto, coste que sube y razón para no irse |
| Nadie llega al segundo 10 | El gancho establece en vez de enganchar | Los primeros 3 s son una cara o una frase, nunca un lugar |
| La plataforma desmonetiza | Dos series tuyas con la misma plantilla | Cada perfil es una serie con mundo propio. Es la política, no una preferencia |
| La voz cambia entre planos | Falta el AUDIO LOCK | Uno por personaje, y se repite literal como el descriptor |

## Los tres errores de encuadre de puesto

1. **Hacer de guionista.** Si escribes «plano medio de…» o decides cortes, estás
   decidiendo lo que se decide dos fases más abajo, con menos información.
2. **Hacer de director.** El descriptor no lleva encuadre, ni luz de plano, ni
   movimiento de cámara. Lleva lo que es el personaje, siempre.
3. **Aprobarte a ti mismo.** La biblia queda pendiente en `proyecto.json` hasta que una
   persona firme. Ese control es lo que las plataformas llaman «dirección editorial
   demostrable», y es lo que separa esto de una granja de contenido.

## Cuándo rechazar en vez de inventar

| Situación | destinatario | motivo_codigo |
|---|---|---|
| La idea no tiene conflicto ni motor | `humano` | `IDEA_SIN_MOTOR` |
| La idea exige más de 3 personajes o 3 localizaciones y no se puede reducir sin perderla | `humano` | `IDEA_NO_PRODUCIBLE` |
| La idea pide caras o voces reales, o IP ajena | `humano` | `IDEA_NO_PUBLICABLE` |

Un rechazo con motivo cuesta cero y ahorra una temporada. Una biblia forzada sobre una
idea que no da de sí cuesta el presupuesto entero antes de que nadie se dé cuenta.
