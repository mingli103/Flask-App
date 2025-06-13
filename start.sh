#!/bin/sh
set -e

echo "Initializing database..."
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"

echo "Starting Flask application..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 run:app 
