# GymTracking — Hoja de ruta de funcionalidades

> Estado actual: app operativa con registro de sesiones, planes, ejercicios, informes y panel de administración.

---

## Prioridad Alta — Quick wins con alto impacto

### 1. Cálculo de calorías quemadas por sesión

**Qué es:** Estimar las calorías consumidas durante una sesión de entrenamiento a partir de los ejercicios realizados, las series/repeticiones y el peso del usuario.

**Cómo funciona:**
- **Fuerza:** Kcal ≈ series × repeticiones × peso_levantado_kg × 0.00086 (factor MET simplificado)
- **Cardio:** Kcal = MET × peso_corporal_kg × (duración_min / 60)
  - Carrera: MET ≈ 8–11, Bicicleta: MET ≈ 7, Elíptica: MET ≈ 5
- El usuario introduce su peso corporal en el perfil (campo nuevo)
- Se muestra el estimado al terminar la sesión y en el dashboard

**Modelos afectados:**
- `users.User` → añadir `weight_kg` (DecimalField, null=True)
- `exercises.Exercise` → añadir `met_value` (FloatField, default según tipo)
- `WorkoutSession` → añadir property `estimated_calories`

**Dificultad:** Media — 1-2 días de trabajo

---

### 2. Timer de descanso integrado en la sesión

**Qué es:** Un cronómetro que se activa automáticamente entre series dentro del log de sesión.

**Cómo funciona:**
- Al marcar una serie como completada, empieza el countdown con el tiempo de descanso del plan (rest_seconds)
- Notificación visual y sonido al terminar el descanso
- Implementado en JS puro en `sessions/log.html`

**Dificultad:** Baja — solo frontend, sin cambios en el modelo

---

### 3. Registro de récords personales (PRs)

**Qué es:** Detección automática y visualización de máximos históricos por ejercicio (peso máximo, volumen máximo, mejor tiempo en cardio).

**Cómo funciona:**
- Al guardar una serie, compara con el histórico del usuario para ese ejercicio
- Si es un nuevo récord, muestra un indicador visual (🏆) en la sesión y lo registra
- Vista de PRs en el perfil o en el detalle del ejercicio

**Modelo nuevo:** `PersonalRecord(user, exercise, value, record_type, achieved_at)`

**Dificultad:** Media

---

### 4. Peso corporal y métricas físicas

**Qué es:** Registro histórico del peso del usuario con gráfica de evolución.

**Campos:** fecha, peso_kg, grasa_corporal_% (opcional), notas
**Vista:** gráfica de línea en el perfil o en una sección "Mi cuerpo"

**Modelo nuevo:** `BodyMetric(user, date, weight_kg, body_fat_pct, notes)`

**Dificultad:** Baja-Media

---

## Prioridad Media — Funcionalidades de alto valor

### 5. Notificaciones push / recordatorios de entreno

**Qué es:** El usuario puede configurar recordatorios para sus días de entrenamiento según su plan activo.

**Implementación:**
- Service Worker + Web Push API (VAPID keys)
- Modelo `PushSubscription(user, endpoint, keys)`
- Tarea programada (Celery o cron) que envía la notificación la mañana del día de entreno
- En producción (Koyeb): usar Celery + Redis, o un servicio externo como Novu

**Dificultad:** Alta

---

### 6. Exportar datos (CSV / PDF)

**Qué es:** El usuario puede descargar su historial de sesiones y estadísticas.

**Opciones:**
- CSV: sesiones, series, ejercicios — usando `csv` de stdlib Python
- PDF: resumen mensual con gráficas — usando `reportlab` o `weasyprint`
- Botón de exportar en los informes y en el perfil

**Dificultad:** Media

---

### 7. Modo offline / PWA básica

**Qué es:** La app funciona sin conexión para consultar el plan y registrar series, sincronizando cuando vuelve el internet.

**Implementación:**
- `manifest.json` para que sea instalable en móvil (Add to Home Screen)
- Service Worker con cache de assets estáticos
- IndexedDB para guardar logs pendientes de sync

**Dificultad:** Alta (sobre todo la sincronización)

---

### 8. Galería de vídeos de técnica por ejercicio

**Qué es:** Cada ejercicio puede tener un vídeo corto de demostración de la técnica correcta.

**Implementación:**
- Campo `video_url` en `Exercise` (YouTube embed o archivo propio)
- Reproducción en el detalle del ejercicio y durante el log de sesión
- El superusuario sube/vincula los vídeos desde el formulario de ejercicio

**Dificultad:** Baja (si es embed de YouTube)

---

### 9. Supersets y circuitos

**Qué es:** Agrupar ejercicios en bloques que se realizan seguidos sin descanso intermedio (supersets, triseries, circuitos).

**Modelo:** `ExerciseGroup(plan_exercise, group_id, group_type)` o añadir `superset_group` a `PlanExercise`

**Dificultad:** Media-Alta (afecta al log de sesión)

---

## Prioridad Baja — Funcionalidades avanzadas

### 10. Integración con Apple Health / Google Fit

**Qué es:** Importar datos de actividad del reloj/móvil (frecuencia cardíaca, pasos, calorías) y exportar los entrenamientos registrados.

**APIs:**
- iOS: HealthKit (requiere app nativa o wrapper como Capacitor)
- Android: Google Fit REST API

**Dificultad:** Muy alta (requiere app nativa o wrapper)

---

### 11. Recomendaciones de progresión asistidas por IA

**Qué es:** Basándose en el historial del usuario, sugerir cuándo subir de peso, qué ejercicios alternativos probar o cuándo descansar.

**Implementación:**
- Reglas simples primero: si hiciste X reps con Y kg durante 3 semanas, sube el 5%
- Integración con Claude API para recomendaciones más elaboradas (describe el contexto del usuario, el API genera el consejo)

**Dificultad:** Media (reglas) → Alta (IA generativa)

---

### 12. Módulo de nutrición básica

**Qué es:** Registro diario de comidas con conteo de macronutrientes (proteína, carbohidratos, grasas, calorías).

**Componentes:**
- Base de datos de alimentos (USDA FoodData Central API o tabla propia)
- Modelo `MealLog(user, date, food_name, kcal, protein_g, carbs_g, fat_g)`
- Dashboard combinado: calorías quemadas en entreno vs. calorías ingeridas

**Dificultad:** Alta

---

### 13. Sistema de logros y gamificación

**Qué es:** Badges y achievements que el usuario desbloquea según hitos de entrenamiento.

**Ejemplos de logros:**
- 🔥 "Racha de 7 días" — 7 sesiones en 7 días consecutivos
- 💪 "Club 100kg" — primera vez que levantas 100kg en sentadilla
- 🏃 "10K" — primeros 10km de cardio registrados
- ⚡ "Constante" — 30 sesiones completadas

**Modelo:** `Achievement(name, description, icon, condition_code)` + `UserAchievement(user, achievement, unlocked_at)`

**Dificultad:** Media

---

### 14. Comparativa y ranking entre atletas (para supervisores)

**Qué es:** Un supervisor puede ver un ranking de sus atletas por volumen semanal, asistencia o progreso en ejercicios específicos.

**Dificultad:** Media

---

## Mejoras técnicas pendientes

### Performance

| Problema | Solución | Impacto |
|----------|----------|---------|
| Tailwind CDN (39KB unused JS) | Migrar a Tailwind CSS build con PostCSS/Vite | Alto |
| Sin paginación en sesiones largas | Paginación AJAX en el log de sesión | Medio |
| Imágenes de ejercicios sin optimización | WebP + lazy loading con `loading="lazy"` | Medio |
| Sin caché de vistas | Django cache framework + `@cache_page` en vistas públicas | Medio |

### Tailwind Build Pipeline (recomendado para producción)

El uso actual del CDN de Tailwind consume ~300KB de JS en cada página. Con un build step:
- CSS final: ~5-15KB (solo las clases usadas)
- Eliminación total del JS de Tailwind en runtime
- Mejora estimada en FCP: ~700ms

```bash
# Setup básico
npm init -y
npm install -D tailwindcss autoprefixer
npx tailwindcss init
# Añadir al Procfile: npm run build:css
```

### UX / Mobile

- Gestos swipe para navegar entre días en el plan
- Haptic feedback al marcar series (Vibration API)
- Modo apaisado para el log de sesión (más cómodo en el gym)
- Botón "deshacer última serie" en el log

### Seguridad

- Rate limiting en login (django-ratelimit)
- 2FA opcional para superusuarios (django-otp)
- Auditoría de acciones admin (django-simple-history)

---

## Próximos pasos recomendados (orden sugerido)

1. **Peso corporal en perfil** → necesario para el cálculo de calorías
2. **Cálculo de calorías** → alta demanda, bajo coste de implementación
3. **Timer de descanso** → mejora inmediata de UX en el gym
4. **PRs automáticos** → motivación y retención de usuarios
5. **Migrar Tailwind a build** → impacto técnico significativo
6. **Exportar CSV** → funcionalidad muy solicitada en apps fitness
7. **PWA / manifest.json** → instalable en móvil, sin coste adicional de infraestructura
