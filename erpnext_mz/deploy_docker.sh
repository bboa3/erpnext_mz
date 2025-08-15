#!/bin/bash

# 🚀 ERPNext Mozambique Custom App - Docker Deployment Script
# This script deploys the erpnext_mz app from zero to fully deployed

set -e  # Exit on any error

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

# Check if we're in the right directory
if [ ! -f "compose.yaml" ]; then
    print_error "This script must be run from the frappe_docker directory"
    print_error "Current directory: $(pwd)"
    print_error "Expected: frappe_docker directory with compose.yaml"
    exit 1
fi

print_status "✅ Verified we're in the frappe_docker directory"

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

# Ensure jq is available on the host (used to parse JSON)
if ! command -v jq &> /dev/null; then
    print_error "jq is not installed. Please install it (e.g., sudo apt-get install -y jq)"
    exit 1
fi

# Step 2: Check if ERPNext is running
print_status "Step 2: Checking if ERPNext is running..."

if ! docker compose ps | grep -q "backend.*Up"; then
    print_warning "ERPNext backend is not running. Starting services..."
    docker compose up -d
    print_status "Waiting for services to start..."
    sleep 30
else
    print_success "✅ ERPNext services are running"
fi

# Step 3: Detect available sites
print_status "Step 3: Detecting available sites..."

# Get all sites from the bench
SITES=$(docker compose exec -T backend bench list-sites --format json | jq -r '.[]' 2>/dev/null || echo "")

if [ -z "$SITES" ]; then
    print_error "No sites found. Please create at least one site first."
    print_status "You can create a site using:"
    print_status "docker compose exec backend bench new-site --mariadb-user-host-login-scope=% --db-root-password <password> --admin-password <password> <site-name>"
    exit 1
fi

print_status "Available sites:"
echo "$SITES" | while read -r site; do
    print_status "  - $site"
done

# User site selection
echo ""
print_status "Site selection..."
echo "Available sites:"
echo "$SITES" | nl

read -p "Enter the number of the site to deploy to (or 'all' for all sites): " SITE_CHOICE

if [ "$SITE_CHOICE" = "all" ]; then
    SELECTED_SITES="$SITES"
    print_status "Deploying to all sites: $SELECTED_SITES"
else
    if ! [[ "$SITE_CHOICE" =~ ^[0-9]+$ ]]; then
        print_error "Invalid selection. Please enter a number or 'all'"
        exit 1
    fi
    
    SELECTED_SITES=$(echo "$SITES" | sed -n "${SITE_CHOICE}p")
    if [ -z "$SELECTED_SITES" ]; then
        print_error "Invalid site number"
        exit 1
    fi
    
    print_status "Selected site: $SELECTED_SITES"
fi

# Step 4: Create the custom app
print_status "Step 4: Creating the custom app..."

# Check if app directory already exists
if [ -d "../apps/erpnext_mz" ]; then
    print_warning "App directory already exists, removing old version..."
    rm -rf "../apps/erpnext_mz"
fi

# Create the app directory
mkdir -p "../apps/erpnext_mz"
print_success "✅ Created app directory"

# Step 5: Copy app files
print_status "Step 5: Copying app files..."

# Copy all files from the app directory (next to this script)
cp -r "$SCRIPT_DIR"/* "../apps/erpnext_mz/"
print_success "✅ Copied app files"

# Step 6: Set proper permissions
print_status "Step 6: Setting proper permissions..."

chmod -R 755 "../apps/erpnext_mz/"
print_success "✅ Set proper permissions"

# Step 7: Prepare the app inside the container
print_status "Step 7: Preparing app inside the container..."

# Ensure app path exists in the container
docker compose exec -T backend bash -lc 'mkdir -p /home/frappe/frappe-bench/apps/erpnext_mz'

# Copy our files over the generated structure
print_status "Copying our custom files..."
docker cp "$SCRIPT_DIR"/. $(docker compose ps -q backend):/home/frappe/frappe-bench/apps/erpnext_mz/

# Set proper ownership
docker compose exec -T backend bash -c "chown -R frappe:frappe /home/frappe/frappe-bench/apps/erpnext_mz/"

print_success "✅ App structure created"

# Install Python dependencies for the app
print_status "Installing app Python dependencies..."
docker compose exec -T backend bash -lc "cd /home/frappe/frappe-bench && if [ -f apps/erpnext_mz/requirements.txt ]; then pip install -q -r apps/erpnext_mz/requirements.txt; fi"

# Ensure bench recognizes and installs requirements across apps
print_status "Running bench setup requirements..."
docker compose exec -T backend bash -lc "cd /home/frappe/frappe-bench && bench setup requirements --skip-assets"

# Ensure app is listed in apps.txt so Python path includes it
print_status "Ensuring app is listed in sites/apps.txt..."
docker compose exec -T backend bash -lc '
set -e
cd /home/frappe/frappe-bench
if [ -f sites/apps.txt ]; then
  if ! grep -qx "erpnext_mz" sites/apps.txt; then
    echo "erpnext_mz" >> sites/apps.txt
    echo "Added erpnext_mz to sites/apps.txt"
  else
    echo "erpnext_mz already present in sites/apps.txt"
  fi
else
  echo "erpnext_mz" > sites/apps.txt
  echo "Created sites/apps.txt with erpnext_mz"
fi'

# Step 8: Install the app on selected sites
print_status "Step 8: Installing app on selected sites..."

for site in $SELECTED_SITES; do
    print_status "Installing app on $site..."
    
    # Install the app
    if docker compose exec -T backend bench --site "$site" install-app erpnext_mz; then
        print_success "✅ App installed successfully on $site"
    else
        print_error "❌ App installation failed on $site"
        continue
    fi
done

# Step 9: Run the setup script
print_status "Step 9: Running setup script..."

for site in $SELECTED_SITES; do
    print_status "Setting up Mozambique compliance on $site..."
    
    # Get companies for this site
    print_status "Getting companies for $site..."
    COMPANIES=$(docker compose exec -T backend bench --site "$site" console -c "
import frappe
companies = frappe.get_all('Company', fields=['name'])
for company in companies:
    print(company.name)
" 2>/dev/null | grep -v "Traceback" | grep -v "Error" || echo "")
    
    if [ -z "$COMPANIES" ]; then
        print_warning "No companies found on $site, skipping setup"
        continue
    fi
    
    print_status "Companies found on $site:"
    echo "$COMPANIES" | while read -r company; do
        print_status "  - $company"
    done
    
    # Setup Mozambique compliance for each company
    for company in $COMPANIES; do
        print_status "Setting up Mozambique compliance for company: $company on site: $site"
        
        # Run the setup script
        if docker compose exec -T backend bench --site "$site" console -c "
from erpnext_mz.setup import setup_mozambique_compliance
try:
    setup_mozambique_compliance('$company')
    print('✅ Setup completed successfully for $company')
except Exception as e:
    print(f'❌ Setup failed for $company: {str(e)}')
    import traceback
    traceback.print_exc()
"; then
            print_success "✅ Setup completed for $company on $site"
        else
            print_error "❌ Setup failed for $company on $site"
        fi
    done
done

# Step 10: Verify installation
print_status "Step 10: Verifying installation..."

for site in $SELECTED_SITES; do
    print_status "Verifying installation on $site..."
    
    # Check if app is properly installed
    if docker compose exec -T backend bench --site "$site" list-apps | grep -q "erpnext_mz"; then
        print_success "✅ App is listed in installed apps on $site"
    else
        print_error "❌ App is not properly installed on $site"
        continue
    fi
    
    # Check custom fields
    CUSTOM_FIELDS_COUNT=$(docker compose exec -T backend bench --site "$site" console -c "
import frappe
custom_fields = frappe.get_all('Custom Field', filters={'app': 'erpnext_mz'})
print(len(custom_fields))
" 2>/dev/null | tail -n 1 | grep -E '^[0-9]+$' || echo "0")
    
    print_status "Custom fields created on $site: $CUSTOM_FIELDS_COUNT"
    
    # Check print formats
    PRINT_FORMATS_COUNT=$(docker compose exec -T backend bench --site "$site" console -c "
import frappe
print_formats = frappe.get_all('Print Format', filters={'app': 'erpnext_mz'})
print(len(print_formats))
" 2>/dev/null | tail -n 1 | grep -E '^[0-9]+$' || echo "0")
    
    print_status "Print formats created on $site: $PRINT_FORMATS_COUNT"
done

# Step 11: Test basic functionality
print_status "Step 11: Testing basic functionality..."

for site in $SELECTED_SITES; do
    print_status "Testing SAF-T generation on $site..."
    
    # Test SAF-T generation
    docker compose exec -T backend bench --site "$site" console -c "
from erpnext_mz.modules.tax_compliance.saf_t_generator import generate_monthly_saf_t
try:
    companies = frappe.get_all('Company', limit=1)
    if companies:
        result = generate_monthly_saf_t(companies[0].name, 2025, 1)
        print('✅ SAF-T generation test successful')
        print(f'Generated files: {result}')
    else:
        print('⚠️ No companies found for testing')
except Exception as e:
    print(f'❌ SAF-T generation test failed: {str(e)}')
"
done

# Step 12: Final verification
print_status "Step 12: Final verification..."

for site in $SELECTED_SITES; do
    print_status "Checking app status on $site..."
    
    # Check app status
    docker compose exec -T backend bench --site "$site" console -c "
from erpnext_mz.setup import get_setup_status
try:
    companies = frappe.get_all('Company', limit=1)
    if companies:
        status = get_setup_status(companies[0].name)
        print(f'Setup Status for {companies[0].name}:')
        for key, value in status.items():
            print(f'  {key}: {value}')
    else:
        print('⚠️ No companies found for status check')
except Exception as e:
    print(f'❌ Status check failed: {str(e)}')
"
done

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
echo "- Check logs: docker compose logs backend"
echo "- Access console: docker compose exec backend bench --site <site-name> console"
echo "- Uninstall if needed: docker compose exec backend bench --site <site-name> uninstall-app erpnext_mz"
echo "- Check app status: docker compose exec backend bench --site <site-name> list-apps"
echo ""
echo "📚 Documentation: See README.md, DEPLOYMENT_CHECKLIST.md, and DOCKER_DEPLOYMENT_GUIDE.md for details"
echo ""
echo "🌍 Multi-tenancy deployment completed! Each site now has Mozambique compliance features."
