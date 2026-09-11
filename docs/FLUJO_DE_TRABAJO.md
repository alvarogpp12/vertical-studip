# Flujo de trabajo

## Reglas básicas
1. **`main` siempre funciona.** Nunca se trabaja directamente en `main`.
2. **1 issue = 1 rama = 1 pull request.** Nombre de rama: `tipo/numero-descripcion`, por ejemplo `feat/12-conector-r2` o `fix/15-byteplus-estado`.
3. **La CI tiene que estar en verde** antes de fusionar (GitHub Actions ejecuta los tests en cada PR).
4. **Nunca se suben** claves, `.env`, vídeos ni imágenes. Las medias van a R2 o a disco local; en git solo texto (código, biblias, prompts, JSON).
5. **Commits pequeños y en español**, con prefijo: `feat:` nueva función · `fix:` corrección · `docs:` documentación · `skill:` cambios en skills · `config:` modelos y precios.
6. **Versiones:** al cerrar cada fase, etiqueta `v0.2`, `v0.3`…

## El ciclo de cada tarea
```bash
git checkout main && git pull
git checkout -b feat/12-conector-r2
# … trabajar (o pedírselo a Claude Code) …
uv run pytest
git add -A && git commit -m "feat: subida de referencias a R2"
git push -u origin feat/12-conector-r2
gh pr create --fill
# revisar el PR en GitHub → CI en verde → "Squash and merge"
```

## Trabajar con Claude Code
- Abre la carpeta y ejecuta `claude`. Lee `CLAUDE.md` automáticamente.
- Pídele las tareas por issue: *"Resuelve el issue #12 en una rama nueva, ejecuta los tests y abre el PR"*.
- Revisa siempre el PR antes de fusionar: tú apruebas, Claude propone.

## Series (contenido)
- Cada serie vive en `proyectos/<slug>/` y sus textos sí van a git: biblia, style, voces, registry, guiones, shotlists.
- Cambios de biblia en rama propia: `serie/<slug>-biblia-v2`.
