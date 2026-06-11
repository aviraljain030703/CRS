#!/bin/bash
# ========================================================================
# Production Startup Script for Campus Grievance Hub
# ========================================================================
# 
# Usage: ./run_production.sh [--docker] [--local]
# 
# Examples:
#   ./run_production.sh --docker       # Start with Docker Compose
#   ./run_production.sh --local        # Start with Gunicorn directly
#   ./run_production.sh                # Default: Docker Compose
#
# ========================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FLASK_ENV="production"
PORT="${PORT:-5000}"
WORKERS="${WORKERS:-4}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ========================================================================
# Helper Functions
# ========================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

validate_env() {
    log_info "Validating environment configuration..."
    
    # Check required environment variables
    local required_vars=("SECRET_KEY" "JWT_SECRET_KEY")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_error "Please create a .env file with the required variables"
        return 1
    fi
    
    # Validate secret key length
    if [ ${#SECRET_KEY} -lt 16 ]; then
        log_error "SECRET_KEY must be at least 16 characters long"
        return 1
    fi
    
    if [ ${#JWT_SECRET_KEY} -lt 16 ]; then
        log_error "JWT_SECRET_KEY must be at least 16 characters long"
        return 1
    fi
    
    log_info "Environment validation passed!"
}

run_docker() {
    log_info "Starting with Docker Compose..."
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed"
        return 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found, using .env.production"
        cp .env.production .env
    fi
    
    # Load environment variables
    set -a
    source .env
    set +a
    
    # Validate environment
    if ! validate_env; then
        return 1
    fi
    
    # Start services
    log_info "Building Docker images..."
    docker-compose build --no-cache
    
    log_info "Starting services (this may take a minute)..."
    docker-compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 5
    
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker-compose ps | grep -q "healthy\|running"; then
            log_info "Services started successfully!"
            log_info "Application available at http://localhost:$PORT"
            return 0
        fi
        sleep 1
        retries=$((retries - 1))
    done
    
    log_error "Services failed to start within timeout"
    docker-compose logs
    return 1
}

run_local() {
    log_info "Starting with Gunicorn (local)..."
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        return 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate || . venv/Scripts/activate
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found, using .env.production"
        cp .env.production .env
    fi
    
    # Load environment variables
    set -a
    source .env 2>/dev/null || true
    set +a
    
    # Validate environment
    if ! validate_env; then
        return 1
    fi
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Initialize database
    log_info "Initializing database..."
    python3 -c "
from app import create_app, db
import sys
try:
    app = create_app('production')
    with app.app_context():
        db.create_all()
    print('Database initialized successfully!')
except Exception as e:
    print(f'Error initializing database: {e}', file=sys.stderr)
    sys.exit(1)
"
    
    if [ $? -ne 0 ]; then
        log_error "Failed to initialize database"
        return 1
    fi
    
    # Start Gunicorn
    log_info "Starting Gunicorn server with $WORKERS workers..."
    log_info "Application available at http://localhost:$PORT"
    log_info "Press Ctrl+C to stop"
    
    gunicorn \
        --bind "0.0.0.0:$PORT" \
        --workers "$WORKERS" \
        --worker-class sync \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        "wsgi:application"
}

show_help() {
    cat << EOF
Campus Grievance Hub - Production Startup Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --docker    Start with Docker Compose (default)
    --local     Start with Gunicorn directly
    --help      Show this help message
    --validate  Only validate configuration, don't start

EXAMPLES:
    $0 --docker
    $0 --local
    PORT=8000 WORKERS=8 $0 --local

ENVIRONMENT VARIABLES:
    FLASK_ENV       Flask environment (default: production)
    PORT            Port to bind to (default: 5000)
    WORKERS         Number of Gunicorn workers (default: 4)

CONFIGURATION:
    This script expects a .env file in the current directory.
    Use .env.production as a template:
        cp .env.production .env
        nano .env

REQUIRED:
    - SECRET_KEY (at least 16 characters)
    - JWT_SECRET_KEY (at least 16 characters)
    - CMS_DATABASE_URL (MySQL connection string)

For more information, see DEPLOYMENT.md

EOF
}

# ========================================================================
# Main Script
# ========================================================================

# Change to script directory
cd "$SCRIPT_DIR/flask-app" || exit 1

# Parse arguments
MODE="docker"
VALIDATE_ONLY=0

while [ $# -gt 0 ]; do
    case "$1" in
        --docker)
            MODE="docker"
            shift
            ;;
        --local)
            MODE="local"
            shift
            ;;
        --validate)
            VALIDATE_ONLY=1
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

log_info "Campus Grievance Hub - Production Startup"
log_info "Mode: $MODE"
log_info "Working directory: $(pwd)"
log_info "========================================"

if [ $VALIDATE_ONLY -eq 1 ]; then
    log_info "Running in validation-only mode"
    if ! validate_env; then
        exit 1
    fi
    exit 0
fi

case "$MODE" in
    docker)
        if ! run_docker; then
            exit 1
        fi
        ;;
    local)
        if ! run_local; then
            exit 1
        fi
        ;;
    *)
        log_error "Unknown mode: $MODE"
        show_help
        exit 1
        ;;
esac

log_info "Startup completed successfully!"
