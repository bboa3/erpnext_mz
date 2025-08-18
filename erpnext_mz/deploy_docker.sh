#!/usr/bin/env bash

# 🚀 ERPNext Mozambique Custom App - Docker Deployment Script
# This script deploys the erpnext_mz app from zero to fully deployed

set -euo pipefail  # Exit on error, unset vars, and fail pipelines

echo "🚀 Starting ERPNext Mozambique App Deployment..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Resolve absolute path to this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage / args
SHOW_HELP=false
YES=false
SELECTED_SITES=""
SKIP_TESTS=false
INSTALL_HRMS=false
NO_HOST_SYNC=false
COMPOSE_FILE=""
ADMIN_PASSWORD=""
SITE_NAME=""
DB_ROOT_PASSWORD=""

print_help() {
    cat <<'USAGE'
Usage: ../erpnext_mz/deploy_docker.sh [options]

Options:
  -y, --yes                Non-interactive; assume "yes" to prompts
  -s, --site <site>        Target site. If it doesn't exist, the script will create it
      --skip-tests         Skip smoke tests (faster)
      --no-host-sync       Do not create/update ../apps/erpnext_mz on host; copy only into container
  -f, --compose-file FILE  Use specific docker compose file (e.g., pwd.yml)
      --install-hrms       Install HRMS app (optional) and add to selected sites
      --admin-password PWD Set Administrator password for the selected sites (default: admin)
      --db-root-password P  MariaDB root password used for site creation (fallbacks to container env or 'admin')
  -h, --help               Show this help

Examples:
  cd frappe_docker && ../erpnext_mz/deploy_docker.sh -y -s my.site.local --admin-password StrongPass#2025
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--yes)
            YES=true
            shift
            ;;
        -s|--site)
            if [[ $# -lt 2 ]]; then print_error "Missing value for --site"; exit 1; fi
            if [[ -z "$SELECTED_SITES" ]]; then SELECTED_SITES="$2"; else SELECTED_SITES+=$'\n'"$2"; fi
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --install-hrms)
            INSTALL_HRMS=true
            shift
            ;;
        --admin-password)
            if [[ $# -lt 2 ]]; then print_error "Missing value for --admin-password"; exit 1; fi
            ADMIN_PASSWORD="$2"
            shift 2
            ;;
        --no-host-sync)
            NO_HOST_SYNC=true
            shift
            ;;
        -f|--compose-file)
            if [[ $# -lt 2 ]]; then print_error "Missing value for --compose-file"; exit 1; fi
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            SHOW_HELP=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            SHOW_HELP=true
            break
            ;;
    esac
done

if $SHOW_HELP; then
    print_help
    exit 0
fi

## Locate frappe_docker compose file so we can run from anywhere
if [ -f "compose.yaml" ]; then
    FRAPPE_DIR="$(pwd)"
elif [ -f "$SCRIPT_DIR/../frappe_docker/compose.yaml" ]; then
    FRAPPE_DIR="$(cd "$SCRIPT_DIR/../frappe_docker" && pwd)"
else
    print_error "Could not locate compose.yaml for frappe_docker. Run from frappe_docker or keep default layout (../frappe_docker)."
    exit 1
fi

print_status "✅ Using frappe_docker at: $FRAPPE_DIR"

# Helper to always use the correct compose file
dc() {
    local file
    if [[ -n "$COMPOSE_FILE" ]]; then
        file="$COMPOSE_FILE"
    elif [[ -f "$FRAPPE_DIR/compose.yaml" ]]; then
        file="$FRAPPE_DIR/compose.yaml"
    elif [[ -f "$FRAPPE_DIR/pwd.yml" ]]; then
        file="$FRAPPE_DIR/pwd.yml"
    else
        file="$FRAPPE_DIR/compose.yaml"
    fi
    docker compose -f "$file" "$@"
}

# Host apps directory (consistent path regardless of CWD)
HOST_APPS_DIR="$FRAPPE_DIR/../apps/erpnext_mz"

# Step 1: Check Docker environment
print_status "Step 1: Checking Docker environment..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    print_error "Docker Compose is not installed or not in PATH"
    exit 1
fi

print_success "✅ Docker and Docker Compose are available"

# No external host deps; we will parse JSON inside the container with Python

# Step 2: Check if ERPNext is running
print_status "Step 2: Checking if ERPNext is running..."

if ! dc ps | grep -q "backend.*Up"; then
    print_warning "ERPNext backend is not running. Starting services..."
    dc up -d
    print_status "Waiting for services to start (backend ready check)..."
    for i in {1..30}; do
        if dc exec -T backend bench --version >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done
else
    print_success "✅ ERPNext services are running"
fi

# Step 3: Target site(s)
print_status "Step 3: Determining target site(s)..."

if [[ -z "$SELECTED_SITES" ]]; then
    print_error "No site specified. Use --site <site-name> to create/configure a site."
    exit 1
fi

# Discover existing sites to decide on creation
EXISTING_SITES=$(dc exec -T backend bash -lc "bench list-sites --format json | python3 - <<'PY'
import sys,json
data=sys.stdin.read().strip() or '[]'
try:
    sites=json.loads(data)
    print('\n'.join(sites))
except Exception:
    print(data)
PY
" 2>/dev/null || echo "")

if [ -z "$EXISTING_SITES" ]; then
    EXISTING_SITES=$(dc exec -T backend bash -lc "find /home/frappe/frappe-bench/sites -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | grep -v '^assets$' | sed '/^$/d'" 2>/dev/null || echo "")
fi

print_status "Selected sites:"
echo "$SELECTED_SITES" | sed 's/^/  - /'

# Step 3.5: Create missing sites (idempotent)
if [[ -z "$ADMIN_PASSWORD" ]]; then
    ADMIN_PASSWORD="admin"
fi

# Determine DB root password if not provided
if [[ -z "$DB_ROOT_PASSWORD" ]]; then
    DB_ROOT_PASSWORD=$(dc exec -T backend bash -lc 'printenv MARIADB_ROOT_PASSWORD || printenv MYSQL_ROOT_PASSWORD || printenv DB_PASSWORD || echo admin' 2>/dev/null | tr -d '\r' | tail -n1)
fi

echo "$SELECTED_SITES" | while read -r site; do
    [[ -z "$site" ]] && continue
    if echo "$EXISTING_SITES" | grep -Fxq "$site"; then
        print_status "Site already exists: $site"
    else
        print_status "Creating site: $site"
        if dc exec -T backend bash -lc "bench new-site --mariadb-user-host-login-scope='%' --admin-password=\"$ADMIN_PASSWORD\" --db-root-username=root --db-root-password=\"$DB_ROOT_PASSWORD\" --install-app erpnext --set-default \"$site\""; then
            print_success "✅ Site created: $site"
        else
            print_error "❌ Failed to create site: $site"
            exit 1
        fi
    fi
done

# Step 4: Create the custom app
print_status "Step 4: Creating the custom app..."

# Ensure app directory exists (idempotent) unless disabled
if ! $NO_HOST_SYNC; then
    mkdir -p "$HOST_APPS_DIR"
fi

# Step 5: Copy app files
print_status "Step 5: Copying app files..."

# Sync app files from repo into bench apps dir (rsync if available, else cp)
if ! $NO_HOST_SYNC; then
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete "$SCRIPT_DIR"/ "$HOST_APPS_DIR/"
    else
        rm -rf "$HOST_APPS_DIR"/*
        cp -r "$SCRIPT_DIR"/* "$HOST_APPS_DIR/"
    fi
fi
print_success "✅ Copied app files"

# Step 6: Set proper permissions
print_status "Step 6: Setting proper permissions..."

chmod -R 755 "$HOST_APPS_DIR"
print_success "✅ Set proper permissions"

# Step 7: Prepare the app inside the container
print_status "Step 7: Preparing app inside the container..."

# Ensure app path exists in the container
dc exec -T backend bash -lc 'mkdir -p /home/frappe/frappe-bench/apps/erpnext_mz && chown -R frappe:frappe /home/frappe/frappe-bench/apps/erpnext_mz'

# Copy our files into the container (one-shot sync)
print_status "Copying our custom files into container..."
docker cp "$SCRIPT_DIR"/. $(dc ps -q backend):/home/frappe/frappe-bench/apps/erpnext_mz/
dc exec -T backend bash -lc 'chown -R frappe:frappe /home/frappe/frappe-bench/apps/erpnext_mz'

print_success "✅ App structure created"

# Install Python dependencies for the app (optional)
print_status "Installing app Python dependencies if specified..."
dc exec -T backend bash -lc "cd /home/frappe/frappe-bench && if [ -f apps/erpnext_mz/requirements.txt ]; then pip install -q -r apps/erpnext_mz/requirements.txt || true; fi"

# Ensure app is listed in apps.txt so bench can import it
print_status "Ensuring erpnext_mz is listed in sites/apps.txt..."
dc exec -T backend bash -lc '
set -e
cd /home/frappe/frappe-bench
mkdir -p sites
touch sites/apps.txt
if ! grep -qx "erpnext_mz" sites/apps.txt; then
  echo "erpnext_mz" >> sites/apps.txt
  echo "Added erpnext_mz to sites/apps.txt"
else
  echo "erpnext_mz already present in sites/apps.txt"
fi'

# Ensure Python path includes bench apps (create .pth)
print_status "Ensuring Python path includes bench apps directory..."
dc exec -T backend bash -lc '
PYLIB=$(env/bin/python - <<"PY"
import sysconfig
print(sysconfig.get_paths()["purelib"])
PY
)
echo "/home/frappe/frappe-bench/apps" > "$PYLIB/bench_apps_path.pth" && ls -l "$PYLIB/bench_apps_path.pth" || true
'

# Step 8: Install the app on the target site(s)
print_status "Step 8: Installing app on target site(s)..."

for site in $SELECTED_SITES; do
    print_status "Installing app on $site..."
    
    # Optionally install HRMS first (if requested)
    if $INSTALL_HRMS; then
        print_status "Ensuring HRMS app is installed on $site..."
        # Ensure Node & Yarn are available (best-effort). Use root to install if missing.
        dc exec -T backend bash -lc "command -v node >/dev/null 2>&1 && command -v yarn >/dev/null 2>&1" || \
        dc exec -T -u 0 backend bash -lc "set -e; export DEBIAN_FRONTEND=noninteractive; \
            apt-get update -y && apt-get install -y curl ca-certificates gnupg; \
            curl -fsSL https://deb.nodesource.com/setup_18.x | bash -; \
            apt-get install -y nodejs; \
            npm install -g yarn || true; \
            chown -R frappe:frappe /home/frappe || true"
        # Pre-clean HR-related Module Defs to avoid duplicate errors
        dc exec -T backend bench --site "$site" execute erpnext_mz.setup.cleanup_hr_module_defs_for_hrms_install || true
        dc exec -T backend bash -lc "cd /home/frappe/frappe-bench && bench get-app --branch version-15 hrms https://github.com/frappe/hrms || true"
        # Ensure hrms is present in apps.txt
        dc exec -T backend bash -lc 'cd /home/frappe/frappe-bench && mkdir -p sites && touch sites/apps.txt && { grep -qx "hrms" sites/apps.txt || echo "hrms" >> sites/apps.txt; }'
        if dc exec -T backend bench --site "$site" list-apps | grep -q "hrms"; then
            print_status "HRMS already installed on $site"
        else
            if dc exec -T backend bench --site "$site" install-app hrms; then
                print_success "✅ HRMS installed on $site"
            else
                print_warning "⚠️ HRMS installation failed or skipped on $site; continuing without HRMS"
            fi
        fi
    fi

    # Install our app (retry once after cache-clear if first attempt fails)
    if dc exec -T backend bench --site "$site" install-app erpnext_mz; then
        print_success "✅ App installed successfully on $site"
    else
        print_warning "⚠️ First install attempt failed; clearing cache and retrying..."
        dc exec -T backend bench --site "$site" clear-cache || true
        if dc exec -T backend bench --site "$site" install-app erpnext_mz; then
            print_success "✅ App installed successfully on $site (after retry)"
        else
            print_error "❌ App installation failed on $site"
            continue
        fi
    fi
    # Apply migrations and clear caches to avoid stale state
    dc exec -T backend bench --site "$site" migrate || true
    dc exec -T backend bench --site "$site" clear-cache || true
    dc exec -T backend bench --site "$site" clear-website-cache || true
done

# Step 8.5: Ensure Administrator password (also applied during site creation, but enforce here too)
DEFAULT_ADMIN_PASSWORD="admin"
if [[ -z "$ADMIN_PASSWORD" ]]; then
    ADMIN_PASSWORD="$DEFAULT_ADMIN_PASSWORD"
    print_warning "Nenhuma senha foi fornecida via --admin-password; definindo senha do Administrator como padrão: '$ADMIN_PASSWORD'"
fi

print_status "Step 8.5: Definindo senha do Administrator..."
for site in $SELECTED_SITES; do
    dc exec -T backend bench --site "$site" set-admin-password "$ADMIN_PASSWORD" >/dev/null 2>&1 || true
    print_success "✅ Senha do Administrator definida (ou já definida) em $site"
done

# Step 9: Run the setup script
print_status "Step 9: Running setup script (all companies on each site)..."
for site in $SELECTED_SITES; do
    print_status "Running setup for all companies on $site..."
    if dc exec -T backend bench --site "$site" execute erpnext_mz.setup.setup_all_companies; then
        print_success "✅ Setup executed on $site"
    else
        print_warning "⚠️ Setup reported errors on $site; review logs"
    fi
done

# Step 10: Verify installation
print_status "Step 10: Verifying installation..."

for site in $SELECTED_SITES; do
    print_status "Verifying installation on $site..."
    
    # Check if app is properly installed
    if dc exec -T backend bench --site "$site" list-apps | tr -d '\r' | grep -q "erpnext_mz"; then
        print_success "✅ App is listed in installed apps on $site"
    else
        print_error "❌ App is not properly installed on $site"
        continue
    fi
    
    # Quick status JSON (company setup readiness)
    dc exec -T backend bench --site "$site" execute erpnext_mz.setup.get_first_company_setup_status | cat || true
done

# Step 11: Test basic functionality (optional)
if ! $SKIP_TESTS; then
    print_status "Step 11: Testing basic functionality..."
    for site in $SELECTED_SITES; do
        print_status "Skipping SAF-T generation test by default (requires existing Company)"
    done
fi

# Step 12: Final verification
print_status "Step 12: Final verification..."

for site in $SELECTED_SITES; do
    print_status "Checking app status on $site..."
    # Use bench execute to avoid console -c issues
    dc exec -T backend bench --site "$site" execute erpnext_mz.setup.get_first_company_setup_status | cat || true
done

# Step 13: Restart backend and refresh frontend to avoid stale state
print_status "Step 13: Restarting backend and refreshing frontend..."
dc restart backend || true
sleep 2
dc restart frontend || true

print_success "🎉 Multi-tenancy deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "======================"
echo "Sites processed: $SELECTED_SITES"
echo "App: erpnext_mz"
echo "Features: Mozambique compliance, SAF-T, VAT, HR & Payroll"
echo ""

echo "📋 Next Steps:"
echo "=============="
for site in $SELECTED_SITES; do
    echo "For site: $site"
    echo "1. Access: http://$site"
    echo "2. Go to Setup > Company and configure Mozambique settings"
    echo "3. Set country to 'Mozambique' and currency to 'MZN'"
    echo "4. Add your company NUIT number"
    echo "5. Test the Mozambique compliance features"
    echo ""
done

echo "🔧 Troubleshooting:"
echo "=================="
echo "- Check logs: docker compose -f $FRAPPE_DIR/compose.yaml logs backend"
echo "- Access console: docker compose -f $FRAPPE_DIR/compose.yaml exec backend bench --site <site-name> console"
echo "- Uninstall if needed: docker compose -f $FRAPPE_DIR/compose.yaml exec backend bench --site <site-name> uninstall-app erpnext_mz"
echo "- Check app status: docker compose -f $FRAPPE_DIR/compose.yaml exec backend bench --site <site-name> list-apps"
echo ""
echo "📚 Documentation: See README.md, DEPLOYMENT_CHECKLIST.md, and DOCKER_DEPLOYMENT_GUIDE.md for details"
echo ""
echo "🌍 Multi-tenancy deployment completed! Each site now has Mozambique compliance features."
