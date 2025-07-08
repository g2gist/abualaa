#!/usr/bin/env python
import os
import sys
from waitress import serve
from abu_alaa_project.wsgi import application

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting server on port {port}")
    serve(application, host='0.0.0.0', port=port)
