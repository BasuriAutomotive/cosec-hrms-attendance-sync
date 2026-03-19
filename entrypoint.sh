#!/bin/bash
 
# Dump all environment variables to a file that cron can source
# This solves cron not inheriting Portainer environment variables
printenv | grep -E "^(HRMS_|COSEC_)" | sed 's/^/export /' > /app/.env_runtime
 
echo "Environment variables written to /app/.env_runtime"
cat /app/.env_runtime
 
# Start cron in foreground
echo "Starting cron..."
cron -f
 