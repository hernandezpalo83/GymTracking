#!/bin/bash

# --- Colores ---
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

printf "${BLUE}===> GymTracking — Arranque <===${NC}\n"

# 1. Limpieza de temporales
printf "🧹 Limpiando archivos temporales y cache...\n"
find . -path "*/__pycache__" -delete
find . -name "*.pyc" -delete
find . -name ".DS_Store" -delete

# 2. Entorno Virtual
if [ ! -d "venv" ]; then
    printf "📦 Creando entorno virtual...\n"
    python3 -m venv venv
fi

source venv/bin/activate

# 3. Variables de entorno
if [ -f .env ]; then
    printf "🔐 Cargando variables de entorno desde .env...\n"
    set -a
    source .env
    set +a
fi

# 4. Dependencias
printf "🔄 Actualizando pip e instalando dependencias...\n"
pip install --upgrade pip > /dev/null
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# 5. Migraciones
printf "⚙️  Aplicando migraciones...\n"
python manage.py makemigrations
python manage.py migrate

if [ $? -ne 0 ]; then
    printf "${RED}❌ Error en las migraciones. Abortando.${NC}\n"
    exit 1
fi

# 6. Fixtures (datos de ejemplo)
if [ -d "fixtures" ] && [ "$(ls -A fixtures/*.json 2>/dev/null)" ]; then
    printf "${YELLOW}¿Cargar datos de ejemplo (fixtures)? (y/n): ${NC}"
    read -r load_fixtures
    case "$load_fixtures" in
        [yY]|[yY][eE][sS])
            printf "📂 Cargando fixtures...\n"
            for f in fixtures/*.json; do
                python manage.py loaddata "$f" && printf "  ✅ $f\n" || printf "  ⚠️  Error en $f\n"
            done
            ;;
        *)
            printf "⏭️  Fixtures omitidos.\n"
            ;;
    esac
fi

# 7. Superusuario
printf "${YELLOW}¿Crear superusuario? (y/n): ${NC}"
read -r create_super
case "$create_super" in
    [yY]|[yY][eE][sS])
        python manage.py createsuperuser
        ;;
esac

# 8. Tests
printf "${BLUE}¿Ejecutar tests unitarios? (y/n): ${NC}"
read -r run_tests
case "$run_tests" in
    [yY]|[yY][eE][sS])
        printf "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        printf "🧪 Ejecutando tests unitarios...\n"
        printf "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n\n"
        export DJANGO_ENV=testing
        PYTHONWARNINGS=ignore::UserWarning python manage.py test --verbosity=2
        test_exit_code=$?
        unset DJANGO_ENV

        printf "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
        if [ $test_exit_code -ne 0 ]; then
            printf "${RED}❌ Tests fallidos. Revisa los errores arriba. Abortando.${NC}\n"
            printf "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
            exit 1
        fi

        printf "${GREEN}✅ Todos los tests han pasado correctamente.${NC}\n"
        printf "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

        printf "${BLUE}¿Arrancar el servidor ahora? (y/n): ${NC}"
        read -r run_after_test
        case "$run_after_test" in
            [yY]|[yY][eE][sS])
                printf "${GREEN}🚀 Arrancando servidor en http://127.0.0.1:8000 ...${NC}\n"
                python manage.py runserver
                ;;
            *)
                printf "${BLUE}👋 Tests OK. Saliendo sin arrancar el servidor.${NC}\n"
                exit 0
                ;;
        esac
        ;;
    *)
        printf "${GREEN}🚀 Arrancando servidor en http://127.0.0.1:8000 ...${NC}\n"
        python manage.py runserver
        ;;
esac
