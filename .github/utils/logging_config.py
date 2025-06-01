"""
Logging Configuration
===================

Configures structured logging for the application.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from flask import request, has_request_context
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()
        if has_request_context():
            log_record['request_id'] = request.headers.get('X-Request-ID')
            log_record['ip_address'] = request.remote_addr
            log_record['user_agent'] = request.user_agent.string
            log_record['endpoint'] = request.endpoint
        if not log_record.get('level'):
            log_record['level'] = record.levelname
        if not log_record.get('type'):
            log_record['type'] = record.name

def setup_logging(app):
    """Configure application logging"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure JSON formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # Configure file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, app.config['LOG_FILE']),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(app.config['LOG_LEVEL'])
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set up werkzeug logger
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # Log application startup
    app.logger.info('Application startup', extra={
        'environment': app.config['ENV'],
        'debug': app.debug,
        'testing': app.testing
    })

def log_request():
    """Log HTTP request details"""
    if has_request_context():
        app.logger.info('HTTP Request', extra={
            'method': request.method,
            'url': request.url,
            'headers': dict(request.headers),
            'data': request.get_data(as_text=True)
        })

def log_response(response):
    """Log HTTP response details"""
    if has_request_context():
        app.logger.info('HTTP Response', extra={
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'data': response.get_data(as_text=True)
        })
    return response
