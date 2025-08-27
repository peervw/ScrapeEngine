FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    iputils-ping \
    dnsutils \
    net-tools \
    fonts-unifont \
    fonts-freefont-ttf \
    # Add more font packages to satisfy Playwright requirements
    xfonts-utils \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers without dependencies (we installed them manually)
RUN playwright install chromium --with-deps || \
    (apt-get update && \
     apt-get install -y \
     libx11-xcb1 \
     libxcomposite1 \
     libxcursor1 \
     libxdamage1 \
     libxi6 \
     libxtst6 \
     libnss3 \
     libcups2 \
     libxss1 \
     libxrandr2 \
     libasound2 \
     libatk1.0-0 \
     libatk-bridge2.0-0 \
     libpangocairo-1.0-0 \
     libgtk-3-0 \
     libgbm1 \
     libxshmfence1 \
     && playwright install chromium)

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]