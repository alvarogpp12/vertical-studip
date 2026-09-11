# Episodios

Una carpeta por episodio: `ep01/`, `ep02/`…

El contenido lo escribe el agente guionista, no se rellena a mano:

```bash
uv run showrunner guion <serie> --episodio s01_ep01
```

y deja `guion.md`, `guion.json` y `shotlist.json` con los ids canónicos
(`s01_ep01_sh001`). Después, `showrunner prompts` escribe `prompts/` y
`showrunner producir` deja `tomas/` y `final.mp4` (esas dos, fuera de git).

El formato de `shotlist.json` lo define `src/showrunner/dominio/shotlist.py`: es el
contrato, y se valida al cargarlo. Antes vivía en una plantilla de ejemplo que
nadie comprobaba y que traía la convención de ids antigua.
