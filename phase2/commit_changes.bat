@echo off
REM Batch script to commit all changes to GitHub
REM Created by Kiro - Review each commit before executing

echo ========================================
echo Git Commit Script
echo ========================================
echo.
echo This script will create 24 organized commits
echo Press Ctrl+C to cancel at any time
echo.
pause

REM 1. Automated forecast pipeline spec
echo.
echo [1/24] Adding automated forecast pipeline spec...
git add .kiro/specs/automated-forecast-pipeline/
git commit -m "Add automated forecast pipeline spec" -m "- Add requirements document with 10 requirements and 50 acceptance criteria" -m "- Add design document with complete architecture and 42 correctness properties" -m "- Add implementation tasks (22 main tasks with sub-tasks)" -m "- Add README with overview and success criteria" -m "- This spec completes the operational automation layer for production readiness"

REM 2. Other specs
echo [2/24] Adding dashboard and early warning system specs...
git add .kiro/specs/dashboard-api-fixes/ .kiro/specs/dashboard-data-integration/ .kiro/specs/dashboard-visualization-fixes/ .kiro/specs/early-warning-system/
git commit -m "Add dashboard and early warning system specs" -m "- Add dashboard API fixes spec" -m "- Add dashboard data integration spec" -m "- Add dashboard visualization fixes spec" -m "- Add early warning system spec with forecast generation"

REM 3. Backend forecast features
echo [3/24] Adding forecast generation and early warning system...
git add backend/app/api/forecasts.py backend/app/models/forecast.py backend/app/schemas/forecast.py backend/app/services/forecast_service.py backend/app/services/forecast_scheduler.py backend/alembic/versions/004_add_forecast_tables.py backend/tests/test_forecast_integration.py backend/tests/test_forecast_properties.py
git commit -m "Add forecast generation and early warning system" -m "- Add forecast API endpoints" -m "- Add forecast models and schemas" -m "- Add forecast service with ML model integration" -m "- Add forecast scheduler for automated generation" -m "- Add database migration for forecast tables" -m "- Add comprehensive forecast tests (integration and property-based)"

REM 4. Backend scripts and utilities
echo [4/24] Adding backend scripts and utilities...
git add backend/scripts/ backend/app/utils/ backend/app/core/cache.py backend/app/middleware/security.py
git commit -m "Add backend scripts and utilities" -m "- Add data loading and verification scripts" -m "- Add forecast generation scripts" -m "- Add utility functions for common operations" -m "- Add caching layer for performance" -m "- Add security middleware"

REM 5. Backend analysis scripts
echo [5/24] Adding backend analysis and data migration scripts...
git add backend/check_models.py backend/check_trigger_gaps.py backend/cleanup_old_coordinates.py backend/debug_correlation.py backend/fix_trigger_data.py backend/migrate_to_tanzania.py backend/verify_climate_patterns.py backend/test_recommendations_api.py
git commit -m "Add backend analysis and data migration scripts" -m "- Add model validation scripts" -m "- Add trigger gap analysis" -m "- Add coordinate cleanup utilities" -m "- Add correlation debugging tools" -m "- Add trigger data fixes" -m "- Add Tanzania migration script" -m "- Add climate pattern verification" -m "- Add recommendations API tests"

REM 6. Backend configuration
echo [6/24] Updating backend configuration and dependencies...
git add backend/app/main.py backend/app/core/config.py backend/requirements.txt backend/.env.example backend/Dockerfile
git commit -m "Update backend configuration and dependencies" -m "- Update main app with new API routes" -m "- Update configuration with new settings" -m "- Update requirements with new dependencies" -m "- Update environment example" -m "- Update Dockerfile for deployment"

REM 7. Backend API and services
echo [7/24] Updating backend API endpoints and services...
git add backend/app/api/climate.py backend/app/api/dashboard.py backend/app/api/triggers.py backend/app/services/auth_service.py backend/app/services/climate_service.py backend/app/services/dashboard_service.py backend/app/services/model_service.py backend/app/services/trigger_service.py
git commit -m "Update backend API endpoints and services" -m "- Enhance climate API with new features" -m "- Improve dashboard API with better data aggregation" -m "- Update trigger API with calibration support" -m "- Refactor services for better performance" -m "- Add error handling and validation"

REM 8. Backend models and schemas
echo [8/24] Updating backend models and schemas...
git add backend/app/models/__init__.py backend/app/models/climate_data.py backend/app/models/model_metric.py backend/app/models/trigger_event.py backend/app/schemas/__init__.py backend/app/schemas/climate_data.py backend/app/schemas/model.py backend/app/schemas/trigger_event.py
git commit -m "Update backend models and schemas" -m "- Enhance climate data model with indexes" -m "- Update model metrics schema" -m "- Improve trigger event model" -m "- Add validation to schemas" -m "- Update model exports"

REM 9. Frontend new pages
echo [9/24] Adding new frontend dashboard pages...
git add frontend/src/pages/AdminDashboard.tsx frontend/src/pages/ForecastDashboard.tsx
git commit -m "Add new frontend dashboard pages" -m "- Add admin dashboard for system management" -m "- Add forecast dashboard for early warning system" -m "- Integrate with forecast API endpoints"

REM 10. Frontend existing pages
echo [10/24] Updating frontend dashboard pages...
git add frontend/src/pages/ClimateInsightsDashboard.tsx frontend/src/pages/ExecutiveDashboard.tsx frontend/src/pages/ModelPerformanceDashboard.tsx frontend/src/pages/RiskManagementDashboard.tsx frontend/src/pages/TriggersDashboard.tsx
git commit -m "Update frontend dashboard pages" -m "- Enhance climate insights with better visualizations" -m "- Improve executive dashboard with KPIs" -m "- Update model performance metrics display" -m "- Enhance risk management dashboard" -m "- Improve triggers dashboard with calibration data"

REM 11. Frontend components
echo [11/24] Updating frontend components and layout...
git add frontend/src/App.tsx frontend/src/components/charts/Chart.tsx frontend/src/components/common/DataTable.tsx frontend/src/components/layout/AppLayout.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "Update frontend components and layout" -m "- Add new routes to App" -m "- Enhance chart components with better styling" -m "- Improve data table with sorting and filtering" -m "- Update app layout with new navigation" -m "- Add forecast dashboard to sidebar"

REM 12. Frontend configuration
echo [12/24] Updating frontend configuration and types...
git add frontend/Dockerfile frontend/Dockerfile.dev frontend/src/types/react-plotly.d.ts frontend/src/vite-env.d.ts
git commit -m "Update frontend configuration and types" -m "- Update production Dockerfile" -m "- Add development Dockerfile" -m "- Add TypeScript type definitions" -m "- Update Vite environment types"

REM 13. Backend documentation
echo [13/24] Adding backend documentation...
git add backend/API_DOCUMENTATION.md backend/CHANGELOG_DATA_LOADER.md backend/DATA_LOADING_GUIDE.md backend/DEPLOYMENT_GUIDE.md backend/DUPLICATE_CLEANUP_GUIDE.md backend/MIGRATION_COMPLETE.md backend/PERFORMANCE_OPTIMIZATION_GUIDE.md backend/SMART_UPSERT_SUMMARY.md
git commit -m "Add backend documentation" -m "- Add comprehensive API documentation" -m "- Add data loader changelog" -m "- Add data loading guide" -m "- Add deployment guide" -m "- Add duplicate cleanup guide" -m "- Add migration completion notes" -m "- Add performance optimization guide" -m "- Add smart upsert summary"

REM 14. Project documentation
echo [14/24] Adding project documentation...
git add docs/IMPLEMENTATION_COMPLETE.md docs/DASHBOARD_INTEGRATION_COMPLETE.md docs/CALIBRATION_COMPLETE.md docs/PROJECT_SUMMARY.md docs/GETTING_STARTED.md docs/SETUP_GUIDES.md docs/ADMIN_PROCEDURES.md docs/DEPLOYMENT_CHECKLIST.md docs/docker_deployment_checklist.md
git commit -m "Add project documentation" -m "- Add implementation completion summary" -m "- Add dashboard integration guide" -m "- Add calibration completion notes" -m "- Add project summary" -m "- Add getting started guide" -m "- Add setup guides" -m "- Add admin procedures" -m "- Add deployment checklists"

REM 15. Analysis docs
echo [15/24] Adding analysis and reference documentation...
git add docs/2021_TRIGGER_GAP_ANALYSIS.md docs/DASHBOARD_DATA_REFERENCE.md docs/DASHBOARD_INTEGRATION_GUIDE.md docs/DASHBOARD_VISUALIZATION_IMPROVEMENTS.md docs/PIPELINE_EXECUTION_SUMMARY.md docs/TASKS_11-20_IMPLEMENTATION.md
git commit -m "Add analysis and reference documentation" -m "- Add 2021 trigger gap analysis" -m "- Add dashboard data reference" -m "- Add dashboard integration guide" -m "- Add visualization improvements doc" -m "- Add pipeline execution summary" -m "- Add tasks implementation notes"

REM 16. Update docs
echo [16/24] Updating project documentation...
git add docs/README.md docs/IMPLEMENTATION_STATUS.md docs/pipeline_overview.md README.md
git commit -m "Update project documentation" -m "- Update main README with current status" -m "- Update implementation status" -m "- Update pipeline overview" -m "- Update docs README"

REM 17. Dashboard docs
echo [17/24] Updating dashboard documentation...
git add dashboard/README.md dashboard/IMPLEMENTATION_STATUS.md dashboard/USER_GUIDE.md
git commit -m "Update dashboard documentation" -m "- Update dashboard README" -m "- Update implementation status" -m "- Add user guide for dashboard features"

REM 18. Root scripts
echo [18/24] Adding root-level scripts and summaries...
git add FORECAST_GENERATION_SUMMARY.md RECOMMENDATIONS_FIX_SUMMARY.md analyze_2021_gap.py check_2021_gap.py setup_dashboard.bat setup_dashboard.sh
git commit -m "Add root-level scripts and summaries" -m "- Add forecast generation summary" -m "- Add recommendations fix summary" -m "- Add 2021 gap analysis scripts" -m "- Add dashboard setup scripts for Windows and Linux"

REM 19. Verification scripts
echo [19/24] Adding data loading and verification scripts...
git add scripts/load_dashboard_data.py scripts/verification/
git commit -m "Add data loading and verification scripts" -m "- Add dashboard data loader" -m "- Add dashboard functionality verification" -m "- Add dashboard integration verification" -m "- Add Docker deployment verification"

REM 20. Docker config
echo [20/24] Updating Docker Compose configuration...
git add docker-compose.dev.yml docker-compose.prod.yml
git commit -m "Update Docker Compose configuration" -m "- Update development environment configuration" -m "- Update production environment configuration" -m "- Add new services and dependencies"

REM 21. Migrations and evaluation
echo [21/24] Updating database migrations and evaluation script...
git add backend/alembic/versions/002_increase_severity_precision.py backend/alembic/versions/003_increase_mape_precision.py run_evaluation.py
git commit -m "Update database migrations and evaluation script" -m "- Add migration for severity precision" -m "- Add migration for MAPE precision" -m "- Update evaluation script"

REM 22. Update specs
echo [22/24] Updating existing spec files...
git add .kiro/specs/insurance-trigger-calibration/requirements.md .kiro/specs/interactive-dashboard-system/tasks.md
git commit -m "Update existing spec files" -m "- Update insurance trigger calibration requirements" -m "- Update interactive dashboard system tasks"

REM 23. Remove deleted files
echo [23/24] Removing obsolete documentation files...
git add -u
git commit -m "Remove obsolete documentation files" -m "- Remove outdated setup and implementation docs" -m "- Remove superseded guides and summaries" -m "- Clean up documentation structure"

REM 24. Hypothesis examples
echo [24/24] Adding Hypothesis property-based testing examples...
git add backend/.hypothesis/
git commit -m "Add Hypothesis property-based testing examples" -m "- Add generated test examples from Hypothesis framework"

echo.
echo ========================================
echo All commits created successfully!
echo ========================================
echo.
echo Next step: Push to GitHub
echo Run: git push origin main
echo.
pause
