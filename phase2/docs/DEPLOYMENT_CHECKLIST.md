# Deployment Checklist

## Pre-Deployment

- [ ] Run ML pipeline to generate latest data
  ```bash
  python run_pipeline.py
  python train_pipeline.py
  ```

- [ ] Load data into database
  ```bash
  cd backend
  python scripts/load_all_data.py --clear
  python scripts/seed_users.py
  ```

- [ ] Verify data loaded correctly
  ```bash
  python scripts/verify_data.py
  ```

- [ ] Run end-to-end tests
  ```bash
  python scripts/test_e2e.py
  ```

## Environment Configuration

- [ ] Copy `.env.template` to `.env`
- [ ] Set strong `JWT_SECRET` (32+ characters)
- [ ] Set strong database password
- [ ] Configure `DATABASE_URL` for production
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure CORS origins for production domain

## Security

- [ ] Change default user passwords
- [ ] Review and update CORS settings
- [ ] Enable HTTPS (configure reverse proxy)
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Review API authentication settings

## Database

- [ ] Set up automated backups
  ```bash
  # Daily backup cron job
  0 2 * * * docker-compose exec db pg_dump -U user climate_prod > backup_$(date +\%Y\%m\%d).sql
  ```

- [ ] Test backup restoration
- [ ] Configure database connection pooling
- [ ] Set up database monitoring

## Monitoring

- [ ] Set up health check monitoring
  ```bash
  # Monitor /health endpoint
  curl http://your-domain.com/health
  ```

- [ ] Configure log aggregation
- [ ] Set up error alerting
- [ ] Configure uptime monitoring
- [ ] Set up performance monitoring

## Deployment

- [ ] Build production Docker images
  ```bash
  docker-compose -f docker-compose.prod.yml build
  ```

- [ ] Start production services
  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  ```

- [ ] Verify all services running
  ```bash
  docker-compose -f docker-compose.prod.yml ps
  ```

- [ ] Test frontend accessibility
- [ ] Test backend API
- [ ] Test authentication flow
- [ ] Test all dashboards

## Post-Deployment

- [ ] Monitor logs for errors
  ```bash
  docker-compose -f docker-compose.prod.yml logs -f
  ```

- [ ] Verify data refresh works
- [ ] Test user access and permissions
- [ ] Document any issues encountered
- [ ] Create rollback plan

## Rollback Procedure

If deployment fails:

1. Stop production services
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. Restore database from backup
   ```bash
   docker-compose exec db psql -U user climate_prod < backup_YYYYMMDD.sql
   ```

3. Restart previous version
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. Verify system operational
5. Investigate and fix issues
6. Retry deployment

## Maintenance

- [ ] Schedule regular data reloads
- [ ] Monitor disk space
- [ ] Review logs weekly
- [ ] Update dependencies monthly
- [ ] Test backups monthly
- [ ] Review security settings quarterly
