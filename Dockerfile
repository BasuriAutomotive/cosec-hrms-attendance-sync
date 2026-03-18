FROM python:3.11-slim

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Write cron jobs directly into cron
# main.py        — every 10 minutes
# backfill_sync  — every 2 hours + specifically at 10:00 AM
RUN echo "*/10 * * * * cd /app && python main.py >> /app/logs/cron.log 2>&1" > /etc/cron.d/cosec_hrms_sync && \
    echo "0 */2 * * * cd /app && python backfill_sync.py >> /app/logs/cron.log 2>&1" >> /etc/cron.d/cosec_hrms_sync && \
    echo "0 10 * * * cd /app && python backfill_sync.py >> /app/logs/cron.log 2>&1" >> /etc/cron.d/cosec_hrms_sync && \
    echo "" >> /etc/cron.d/cosec_hrms_sync && \
    chmod 0644 /etc/cron.d/cosec_hrms_sync && \
    crontab /etc/cron.d/cosec_hrms_sync

# Start cron in foreground to keep container running
CMD ["cron", "-f"]