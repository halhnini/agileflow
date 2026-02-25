FROM python:3.9-slim

WORKDIR /app

# Install the GitHub App server dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the GitHub App server
COPY . ./github_app/

# Copy the core AgileFlow engine (shared modules)
COPY ../ghost_scrum_master/core ./ghost_scrum_master/core/
COPY ../ghost_scrum_master/requirements.txt ./ghost_scrum_master/
RUN pip install --no-cache-dir -r ghost_scrum_master/requirements.txt

WORKDIR /app/github_app

EXPOSE 3000

CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "2", "--timeout", "120", "app:app"]
