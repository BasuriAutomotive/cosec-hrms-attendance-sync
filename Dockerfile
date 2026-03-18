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

# Set up cron job
COPY crontab /etc/cron.d/cosec_hrms_sync
RUN chmod 0644 /etc/cron.d/cosec_hrms_sync
RUN crontab /etc/cron.d/cosec_hrms_sync

# Give execution rights on the cron job
RUN touch /var/log/cron.log

# Start cron in foreground to keep container running
CMD ["cron", "-f"]