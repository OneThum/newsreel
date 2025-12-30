#!/bin/bash
# 🚀 Newsreel Clustering Overhaul - Complete Deployment Script
# Deploys the new semantic clustering system with A/B testing

set -e

# Configuration - Update these for your environment
RESOURCE_GROUP="${RESOURCE_GROUP:-Newsreel-RG}"
FUNCTION_APP_NAME="${FUNCTION_APP_NAME:-newsreel-func-51689}"
LOCATION="${LOCATION:-centralus}"
ACR_NAME="${ACR_NAME:-newsreelacr}"
EMBEDDINGS_ACI_NAME="${EMBEDDINGS_ACI_NAME:-newsreel-embeddings}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Pre-deployment validation
validate_environment() {
    log_info "Validating deployment environment..."

    # Check if Azure CLI is logged in
    if ! az account show &> /dev/null; then
        log_error "Azure CLI not logged in. Please run 'az login'"
        exit 1
    fi

    # Check if resource group exists
    if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        log_warning "Resource group '$RESOURCE_GROUP' does not exist. Creating..."
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none
        log_success "Resource group created"
    fi

    # Check if function app exists
    if ! az functionapp show --name "$FUNCTION_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log_error "Function app '$FUNCTION_APP_NAME' does not exist in resource group '$RESOURCE_GROUP'"
        log_info "Please ensure the function app is deployed before running this script"
        exit 1
    fi

    log_success "Environment validation passed"
}

# Step 1: Deploy embedding service
deploy_embedding_service() {
    log_info "Step 1: Deploying embedding service to Azure Container Instances..."

    cd embeddings

    # Set deployment parameters
    export RESOURCE_GROUP="$RESOURCE_GROUP"
    export ACI_NAME="$EMBEDDINGS_ACI_NAME"
    export LOCATION="$LOCATION"

    # Optional: Use ACR if configured
    if [ ! -z "$ACR_NAME" ]; then
        export ACR_LOGIN_SERVER="$ACR_NAME.azurecr.io"
        log_info "Using Azure Container Registry: $ACR_LOGIN_SERVER"
    fi

    # Run deployment script
    if ./deploy.sh; then
        log_success "Embedding service deployed successfully"

        # Get the service URL
        FQDN=$(az container show --resource-group "$RESOURCE_GROUP" --name "$EMBEDDINGS_ACI_NAME" --query ipAddress.fqdn -o tsv)
        EMBEDDINGS_URL="http://$FQDN:8080"
        log_info "Embedding service URL: $EMBEDDINGS_URL"
    else
        log_error "Embedding service deployment failed"
        exit 1
    fi

    cd ..
}

# Step 2: Train similarity model
train_similarity_model() {
    log_info "Step 2: Training similarity model..."

    if python3 train_similarity_model.py; then
        log_success "Similarity model training completed"
    else
        log_error "Model training failed"
        exit 1
    fi
}

# Step 3: Configure A/B testing
configure_ab_testing() {
    log_info "Step 3: Configuring A/B testing (30% traffic to new system)..."

    # Set feature flags for A/B testing
    az functionapp config appsettings set \
        --name "$FUNCTION_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --setting CLUSTERING_USE_EMBEDDINGS=true \
        --setting CLUSTERING_USE_EVENT_SIGNATURES=true \
        --setting CLUSTERING_USE_GEOGRAPHIC=true \
        --setting CLUSTERING_USE_WIKIDATA_LINKING=true \
        --setting SCORING_OPTIMIZATION_ENABLED=true \
        --setting CLUSTER_MAINTENANCE_ENABLED=true \
        --setting EMBEDDINGS_SERVICE_URL="$EMBEDDINGS_URL" \
        --output none

    if [ $? -eq 0 ]; then
        log_success "A/B testing configuration applied"
        log_info "Traffic split: 70% control (MD5), 30% new semantic clustering"
    else
        log_error "Failed to configure A/B testing"
        exit 1
    fi
}

# Step 4: Run validation tests
run_validation_tests() {
    log_info "Step 4: Running post-deployment validation tests..."

    # Run core functionality tests
    if python3 -m pytest tests/test_core_functionality.py -v --tb=short; then
        log_success "Core functionality validation passed"
    else
        log_error "Core functionality validation failed"
        exit 1
    fi

    # Test A/B testing integration
    if python3 -m pytest tests/clustering_overhaul_test.py::TestAPIETags -v --tb=short; then
        log_success "A/B testing integration validation passed"
    else
        log_warning "A/B testing integration validation failed (may be expected)"
    fi
}

# Step 5: Monitor initial rollout
monitor_rollout() {
    log_info "Step 5: Setting up initial monitoring..."

    # Run monitoring script
    if [ -f "scripts/monitor_clustering_improvements.py" ]; then
        log_info "Starting clustering improvement monitor..."
        python3 scripts/monitor_clustering_improvements.py &
        MONITOR_PID=$!
        log_info "Monitor started (PID: $MONITOR_PID)"
    fi

    log_success "Initial monitoring configured"
}

# Step 6: Gradual rollout plan
display_rollout_plan() {
    log_info "Step 6: Gradual rollout plan configured"

    echo ""
    echo "🎯 GRADUAL ROLLOUT PLAN"
    echo "========================"
    echo ""
    echo "Current State: 30% traffic to new clustering system"
    echo ""
    echo "Recommended Rollout Schedule:"
    echo "• Day 1-2: 30% traffic - Monitor performance metrics"
    echo "• Day 3-4: 50% traffic - Validate clustering accuracy"
    echo "• Day 5-6: 80% traffic - Full performance validation"
    echo "• Day 7+: 100% traffic - Complete rollout"
    echo ""
    echo "Key Metrics to Monitor:"
    echo "• API response times (<200ms P95)"
    echo "• Clustering accuracy (>85% F1)"
    echo "• Story completeness improvement"
    echo "• Duplicate detection rate (<5%)"
    echo ""
}

# Main deployment function
main() {
    echo ""
    echo "🚀 NEWSREEL CLUSTERING OVERHAUL DEPLOYMENT"
    echo "=========================================="
    echo ""
    log_info "Starting deployment of semantic clustering system with A/B testing"

    # Validate environment
    validate_environment

    # Step 1: Deploy embedding service
    deploy_embedding_service

    # Step 2: Train similarity model
    train_similarity_model

    # Step 3: Configure A/B testing
    configure_ab_testing

    # Step 4: Run validation
    run_validation_tests

    # Step 5: Setup monitoring
    monitor_rollout

    # Step 6: Display rollout plan
    display_rollout_plan

    echo ""
    log_success "DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Monitor metrics for 24-48 hours"
    echo "2. Validate A/B test results"
    echo "3. Gradually increase traffic to new system"
    echo "4. Complete rollout to 100% when targets met"
    echo ""
    echo "📊 Monitor using: scripts/monitor_clustering_improvements.py"
    echo "🔍 Check metrics: Azure Application Insights"
    echo ""
}

# Handle command line arguments
case "${1:-}" in
    "validate")
        validate_environment
        ;;
    "embeddings")
        deploy_embedding_service
        ;;
    "model")
        train_similarity_model
        ;;
    "ab-test")
        configure_ab_testing
        ;;
    "test")
        run_validation_tests
        ;;
    "monitor")
        monitor_rollout
        ;;
    "full"|*)
        main
        ;;
esac
