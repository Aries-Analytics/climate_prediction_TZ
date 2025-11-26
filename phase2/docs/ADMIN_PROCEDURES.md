# Administrator Procedures

## Daily Tasks

### Monitor System Health

```bash
# Check all services running
docker-compose -f docker-compose.prod.yml ps

# Check health endpoint
curl http://your-domain.com/health

# View recent logs
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Review Logs

```bash
# Check for errors
docker-compose -f docker-compose.prod.yml logs | grep ERROR

# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend

# Check database logs
docker-compose -f docker-compose.prod.yml logs db
```

## Weekly Tasks

### Data Reload

```bash
# Run ML pipeline
python run_pipeline.py
python train_pipeline.py

# Reload dashboard data
cd backend
python scripts/load_all_data.py --clear
python scripts/verify_data.py
```

### Backup Verification

```bash
# List recent backups
ls -lh backups/

# Test restore (on test database)
docker-compose exec db psql -U user climate_test < backup_latest.sql
```

### User Management

```bash
# List all users
docker-compose exec db psql -U user climate_prod -c "SELECT username, email, role, is_active FROM users;"

# Deactivate user
docker-compose exec db psql -U user climate_prod -c "UPDATE users SET is_active=false WHERE username='olduser';"
```

## Monthly Tasks

### Update Dependencies

```bash
# Update backend dependencies
cd backend
pip list --outdated
pip install --upgrade <package>

# Update frontend dependencies
cd frontend
npm outdated
npm update
```

### Security Review

- Review user access logs
- Check for failed login attempts
- Review API usage patterns
- Update passwords if needed

### Performance Review

- Check database query performance
- Review API response times
- Monitor disk space usage
- Review memory usage

## Emergency Procedures

### System Down

1. Check service status
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. Restart services
   ```bash
   docker-compose -f docker-compose.prod.yml restart
   ```

3. Check logs for errors
   ```bash
   docker-compose -f docker-compose.prod.yml logs --tail=200
   ```

### Database Issues

1. Check database connectivity
   ```bash
   docker-compose exec db psql -U user climate_prod -c "SELECT 1;"
   ```

2. Restart database
   ```bash
   docker-compose -f docker-compose.prod.yml restart db
   ```

3. Restore from backup if corrupted
   ```bash
   docker-compose exec db psql -U user climate_prod < backup_latest.sql
   ```

### Data Corruption

1. Stop services
2. Restore database from latest backup
3. Reload data from ML pipeline
4. Verify data integrity
5. Restart services

## User Support

### Reset User Password

```bash
# Via database
docker-compose exec db psql -U user climate_prod -c "UPDATE users SET hashed_password='<new_hash>' WHERE username='<user>';"
```

### Create New User

```bash
# Via seed script (modify and run)
cd backend
python scripts/seed_users.py
```

### Grant Admin Access

```bash
# Via database
docker-compose exec db psql -U user climate_prod -c "UPDATE users SET role='admin' WHERE username='<user>';"
```

## Maintenance Windows

### Planned Downtime

1. Notify users 24 hours in advance
2. Schedule during low-usage period (e.g., 2 AM)
3. Create database backup
4. Perform maintenance
5. Verify system operational
6. Notify users of completion

### Update Procedure

1. Backup current system
2. Pull latest code
3. Build new Docker images
4. Stop old services
5. Start new services
6. Run migrations if needed
7. Verify functionality
8. Monitor for issues

## Monitoring and Alerts

### Set Up Alerts

Configure monitoring for:
- Service downtime
- High error rates
- Database connection failures
- Disk space > 80%
- Memory usage > 90%

### Health Check Monitoring

```bash
# Add to cron for continuous monitoring
*/5 * * * * curl -f http://your-domain.com/health || echo "Health check failed" | mail -s "Alert" admin@example.com
```

## Contact Information

- **System Administrator**: admin@example.com
- **Database Administrator**: dba@example.com
- **Development Team**: dev@example.com
- **Emergency Contact**: +1-555-0123
