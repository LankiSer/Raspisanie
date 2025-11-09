#!/bin/bash

# Schedule SaaS Deployment Script
# This script helps deploy the application to production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    if ! command -v make &> /dev/null; then
        log_warning "Make is not installed. You'll need to run docker-compose commands manually."
    fi
    
    log_success "All dependencies are installed"
}

# Setup production environment
setup_production() {
    log_info "Setting up production environment..."
    
    # Create production environment file
    if [ ! -f ".env.prod" ]; then
        if [ -f ".env.prod.example" ]; then
            cp .env.prod.example .env.prod
            log_warning "Created .env.prod from template. Please edit it with your production settings!"
            echo "Required settings:"
            echo "- POSTGRES_PASSWORD"
            echo "- JWT_SECRET"
            echo "- CORS_ORIGINS"
            echo "- REDIS_PASSWORD"
            read -p "Press Enter to continue after editing .env.prod..."
        else
            log_error ".env.prod.example not found. Cannot create production environment."
            exit 1
        fi
    else
        log_info ".env.prod already exists"
    fi
    
    # Create SSL directory
    if [ ! -d "ssl" ]; then
        mkdir -p ssl
        log_info "Created SSL directory. Place your SSL certificates here."
        log_warning "For SSL support, add your certificates:"
        echo "- ssl/cert.pem"
        echo "- ssl/private.key"
    fi
    
    # Create backups directory
    if [ ! -d "backups" ]; then
        mkdir -p backups
        log_info "Created backups directory"
    fi
    
    log_success "Production environment setup completed"
}

# Deploy application
deploy() {
    log_info "Deploying application..."
    
    # Pull latest changes (if git repo)
    if [ -d ".git" ]; then
        log_info "Pulling latest changes from git..."
        git pull origin main || log_warning "Failed to pull latest changes. Continuing with current code."
    fi
    
    # Build images
    log_info "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check service status
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up.*healthy"; then
        log_success "Services are running and healthy"
    else
        log_error "Some services are not healthy. Check logs with: make logs-prod"
        docker-compose -f docker-compose.prod.yml ps
        exit 1
    fi
    
    log_success "Deployment completed successfully!"
}

# Show deployment info
show_info() {
    echo ""
    log_success "🚀 Schedule SaaS deployed successfully!"
    echo ""
    echo "Access your application:"
    echo "  🌐 Web interface: http://localhost"
    echo "  📚 API documentation: http://localhost/api/v1/docs"
    echo ""
    echo "Useful commands:"
    echo "  📊 View logs: make logs-prod"
    echo "  📈 Monitor: docker stats"
    echo "  🔄 Restart: docker-compose -f docker-compose.prod.yml restart"
    echo "  💾 Backup: make backup"
    echo "  🧹 Clean: make clean"
    echo ""
    log_info "Check DOCKER.md for detailed documentation"
}

# Backup database
backup_database() {
    log_info "Creating database backup..."
    
    if ! docker-compose -f docker-compose.prod.yml ps database | grep -q "Up"; then
        log_error "Database container is not running"
        exit 1
    fi
    
    BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose -f docker-compose.prod.yml exec -T database pg_dump -U schedule_user schedule_saas > "$BACKUP_FILE"
    
    log_success "Database backup created: $BACKUP_FILE"
}

# Restore database
restore_database() {
    if [ -z "$1" ]; then
        log_error "Please specify backup file: $0 restore <backup-file>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        log_error "Backup file not found: $1"
        exit 1
    fi
    
    log_warning "This will replace all existing data. Are you sure? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi
    
    log_info "Restoring database from: $1"
    docker-compose -f docker-compose.prod.yml exec -T database psql -U schedule_user -d schedule_saas < "$1"
    
    log_success "Database restored successfully"
}

# Update application
update_application() {
    log_info "Updating application..."
    
    # Backup before update
    backup_database
    
    # Pull latest changes
    if [ -d ".git" ]; then
        git pull origin main
    fi
    
    # Rebuild and deploy
    docker-compose -f docker-compose.prod.yml build --no-cache
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "Application updated successfully"
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Check if containers are running
    if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_error "Some containers are not running"
        docker-compose -f docker-compose.prod.yml ps
        exit 1
    fi
    
    # Check application endpoints
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "Application is healthy"
    else
        log_error "Application health check failed"
        exit 1
    fi
}

# Main script logic
case "$1" in
    "install"|"setup")
        check_root
        check_dependencies
        setup_production
        ;;
    "deploy")
        check_root
        check_dependencies
        setup_production
        deploy
        show_info
        ;;
    "backup")
        backup_database
        ;;
    "restore")
        restore_database "$2"
        ;;
    "update")
        update_application
        ;;
    "health")
        health_check
        ;;
    "logs")
        docker-compose -f docker-compose.prod.yml logs -f
        ;;
    "status")
        docker-compose -f docker-compose.prod.yml ps
        docker system df
        ;;
    "stop")
        log_info "Stopping services..."
        docker-compose -f docker-compose.prod.yml down
        log_success "Services stopped"
        ;;
    "start")
        log_info "Starting services..."
        docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
        log_success "Services started"
        ;;
    *)
        echo "Schedule SaaS Deployment Script"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  setup     - Setup production environment"
        echo "  deploy    - Full deployment (setup + build + start)"
        echo "  backup    - Backup database"
        echo "  restore   - Restore database from backup"
        echo "  update    - Update application (pull + rebuild + restart)"
        echo "  health    - Health check"
        echo "  logs      - Show application logs"
        echo "  status    - Show containers status"
        echo "  start     - Start services"
        echo "  stop      - Stop services"
        echo ""
        echo "Examples:"
        echo "  $0 deploy                              # Deploy application"
        echo "  $0 backup                              # Create backup"
        echo "  $0 restore backups/backup_20241101.sql # Restore from backup"
        echo "  $0 update                              # Update application"
        ;;
esac
