#!/usr/bin/env bash
# Descarga imágenes de ejercicios desde Wikimedia Commons y otros recursos libres
# Guarda en media/exercises/ para ser referenciadas por los fixtures

set -e
DEST="media/exercises"
mkdir -p "$DEST"

download() {
  local filename="$1"
  local url="$2"
  if [ ! -f "$DEST/$filename" ]; then
    echo "Descargando $filename..."
    curl -sSL -o "$DEST/$filename" "$url" || echo "  AVISO: no se pudo descargar $filename"
  else
    echo "Ya existe $filename, omitiendo."
  fi
}

# PECHO
download "press_banca.jpg"      "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Bench_press.jpg/640px-Bench_press.jpg"
download "aperturas.jpg"        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Dumbbell_fly.jpg/640px-Dumbbell_fly.jpg"
download "fondos_paralelas.jpg" "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Dips_at_Muscle_Beach.jpg/480px-Dips_at_Muscle_Beach.jpg"

# ESPALDA
download "dominadas.jpg"        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Pull_up_woman.jpg/480px-Pull_up_woman.jpg"
download "peso_muerto.jpg"      "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Conventional_deadlift.jpg/640px-Conventional_deadlift.jpg"

# PIERNAS
download "sentadilla.jpg"       "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Back_squat.jpg/480px-Back_squat.jpg"
download "zancadas.jpg"         "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Dumbbell_lunges.jpg/480px-Dumbbell_lunges.jpg"

# HOMBROS
download "press_militar.jpg"    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Overhead_press.jpg/480px-Overhead_press.jpg"
download "elevaciones.jpg"      "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Lateral_raises.jpg/480px-Lateral_raises.jpg"

# CORE
download "plancha.jpg"          "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Plank_pose.jpg/640px-Plank_pose.jpg"
download "crunch.jpg"           "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Crunch_ab_exercise.jpg/640px-Crunch_ab_exercise.jpg"

# CARDIO
download "carrera.jpg"          "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Treadmill_running.jpg/640px-Treadmill_running.jpg"
download "bicicleta.jpg"        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Exercise_bike.jpg/640px-Exercise_bike.jpg"
download "cuerda.jpg"           "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Jump_rope_exercise.jpg/480px-Jump_rope_exercise.jpg"

echo ""
echo "Descarga completada. Imágenes en: $DEST/"
echo ""
echo "Para actualizar los fixtures con las rutas de imagen, edita fixtures/exercises.json"
echo "y cambia el campo \"image\": \"\" por \"image\": \"exercises/<nombre_archivo>\""
