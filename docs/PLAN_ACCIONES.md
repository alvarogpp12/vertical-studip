# Plan de acciones · lo que tienes que hacer tú

Tiempo total estimado: unas 3 horas repartidas en 2–3 días. Marca cada casilla al terminar.

---

## BLOQUE A · Instalar el proyecto en tu Mac (30 min)

- [ ] **A1. Descomprime** `showrunner-ia.zip` en una carpeta de trabajo, por ejemplo `~/Proyectos/showrunner-ia`.
- [ ] **A2. Abre la app Terminal** y entra en la carpeta:
  ```bash
  cd ~/Proyectos/showrunner-ia
  ```
- [ ] **A3. Ejecuta el instalador** (instala Homebrew, git, ffmpeg, Node, uv, Python 3.12, las librerías y Claude Code). Te pedirá la contraseña del Mac:
  ```bash
  bash scripts/setup_mac.sh
  ```
  Al final verás una tabla de diagnóstico. Las claves saldrán en ⚠️ hasta el bloque B; es normal.

## BLOQUE B · Subirlo a GitHub (10 min)

- [ ] **B1.** Si no tienes cuenta, créala en https://github.com.
- [ ] **B2. Instala y conecta la herramienta de GitHub:**
  ```bash
  brew install gh
  gh auth login
  ```
  Elige: GitHub.com → HTTPS → Login with a web browser.
- [ ] **B3. Crea el repositorio privado y sube el proyecto** (un solo comando):
  ```bash
  gh repo create showrunner-ia --private --source=. --push
  ```

## BLOQUE C · Cuentas y claves (1 h 30 min)

Cada clave se pega en el archivo `.env` de la carpeta del proyecto (ábrelo con `open -e .env`). Nunca la compartas por chat ni la subas a GitHub.

- [ ] **C1. Anthropic (cerebro del agente)**
  1. Entra en https://console.anthropic.com y crea la cuenta.
  2. Billing → añade método de pago y un **límite mensual** (sugerido: 50 $).
  3. API Keys → Create key → pégala en `ANTHROPIC_API_KEY`.
- [ ] **C2. BytePlus ModelArk (Seedance barato, API oficial de ByteDance)**
  1. Crea la cuenta en https://console.byteplus.com y completa la verificación (empresa o persona).
  2. Abre **ModelArk**. Comprueba que tu cuenta de España puede usarlo.
  3. En la lista de modelos, **activa** Seedance 2.0 Fast, Seedance 2.0 y Seedance 2.5.
  4. API Key Management → crea una clave → pégala en `ARK_API_KEY`.
  5. Copia el **ID exacto** de cada modelo en `ARK_MODEL_SEEDANCE_20_FAST`, `ARK_MODEL_SEEDANCE_20` y `ARK_MODEL_SEEDANCE_25`.
  6. Apunta el **precio real por millón de tokens o por segundo** que muestra la consola y envíamelo. Con eso corrijo `config/modelos.yaml`.
  7. Si hay opción de alertas o límite de gasto, ponlo.
- [ ] **C3. fal.ai (Kling 3.0 y respaldo)**
  1. Cuenta en https://fal.ai → Billing → recarga **20 $**.
  2. Keys → crea una clave → pégala en `FAL_KEY`.
- [ ] **C4. Cloudflare R2 (dónde viven las imágenes de referencia)**
  1. Cuenta en https://dash.cloudflare.com → R2 → activa el plan (hay capa gratuita).
  2. Crea un bucket `showrunner-refs` y activa el acceso público (r2.dev).
  3. Manage R2 API Tokens → crea un token con permiso de lectura y escritura.
  4. Rellena `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` y `R2_PUBLIC_URL`.
- [ ] **C5. Límites de gasto del proyecto:** deja `BUDGET_MAX_PER_JOB=3` y `BUDGET_MAX_PER_DAY=25` hasta que validemos costes.

## BLOQUE D · Comprobar que todo funciona (15 min)

- [ ] **D1. Diagnóstico** (todo debe salir ✅ salvo los modelos que no hayas configurado):
  ```bash
  uv run showrunner doctor
  ```
- [ ] **D2. Prueba sin coste:**
  ```bash
  echo "Prueba" > /tmp/p.md
  uv run showrunner generar /tmp/p.md --salida runs/mock.mp4 --modelo mock --duracion 3
  uv run showrunner qc runs/mock.mp4
  ```
- [ ] **D3. Primera generación real (≈ 0,20 $):**
  ```bash
  cat > /tmp/p.md <<'TXT'
  Vertical 9:16. A single ceramic cup on a wooden table by a rainy window at dusk. Locked-off camera, slow push-in. Steam rises gently from the cup. Soft window light. Rain sound only, no music.
  TXT
  uv run showrunner generar /tmp/p.md --salida runs/prueba_real.mp4 --nivel borrador --duracion 5
  ```
- [ ] **D4. Envíame** el texto que salga en la terminal, tanto si funciona como si da error. Con eso ajusto el conector de BytePlus a la API real.

## BLOQUE E · Decisiones que solo puedes tomar tú (30 min)

- [ ] **E1. Tres ideas de serie**, de 1 a 3 frases cada una. Con ellas construyo y pruebo el agente que escribe la biblia.
- [ ] **E2. Plataforma principal** de la primera serie: TikTok, YouTube Shorts o Instagram Reels.
- [ ] **E3. Presupuesto máximo del primer mes** para pruebas. Sugerido: 100–150 $ entre todos los proveedores.
- [ ] **E4. Reserva los nombres de usuario** de la primera serie en las plataformas. No publiques nada todavía.
- [ ] **E5. Legal:** lee los términos de uso comercial de BytePlus y fal. Si vas a facturar como empresa, consulta con tu asesor la etiqueta de IA (AI Act, art. 50) y la titularidad del contenido.

---

## Lo que hago yo en cuanto termines D4 y E1

1. Ajustar los conectores con tus respuestas reales y precios de consola.
2. Prueba ciega de modelos: los mismos 10 planos verticales en Seedance 2.0 Fast, 2.0, 2.5 y Kling, con coste real por plano aceptado.
3. Skill **showrunner** completa, probada con tus 3 ideas → 3 biblias para que elijas.
4. Subida automática de referencias a R2 y generación de assets de personajes.
5. Orquestación autónoma (Claude Agent SDK) de un episodio completo, con montaje automático.
