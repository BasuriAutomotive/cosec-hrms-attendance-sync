FROM python:3.11-slim

# Install cron and timezone data
RUN apt-get update && apt-get install -y cron tzdata && rm -rf /var/lib/apt/lists/*

# Set timezone to IST
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Write cron jobs using full python3 path
RUN echo "*/2 * * * * . /app/.env_runtime && cd /app && /usr/local/bin/python3 main.py >> /app/logs/cron.log 2>&1" > /etc/cron.d/cosec_hrms_sync && \
    echo "0 */2 * * * . /app/.env_runtime && cd /app && /usr/local/bin/python3 backfill_sync.py >> /app/logs/cron.log 2>&1" >> /etc/cron.d/cosec_hrms_sync && \
    echo "0 10 * * * . /app/.env_runtime && cd /app && /usr/local/bin/python3 backfill_sync.py >> /app/logs/cron.log 2>&1" >> /etc/cron.d/cosec_hrms_sync && \
    echo "" >> /etc/cron.d/cosec_hrms_sync && \
    chmod 0644 /etc/cron.d/cosec_hrms_sync && \
    crontab /etc/cron.d/cosec_hrms_sync

# Entrypoint script — dumps env vars to file then starts cron
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]