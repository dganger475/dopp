"""Report models for DoppleGänger
===========================

This module defines the report models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Report(db.Model):
    """Report model for storing user reports."""
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reported_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reports_given')
    reported = db.relationship('User', foreign_keys=[reported_id], backref='reports_received')

    def __init__(self, reporter_id, reported_id, report_type, content=None, status='pending'):
        self.reporter_id = reporter_id
        self.reported_id = reported_id
        self.report_type = report_type
        self.content = content
        self.status = status

    def to_dict(self):
        """Convert report to dictionary."""
        return {
            'id': self.id,
            'reporter_id': self.reporter_id,
            'reported_id': self.reported_id,
            'report_type': self.report_type,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, reporter_id, reported_id, report_type, content=None, status='pending'):
        """Create a new report."""
        try:
            report = cls(
                reporter_id=reporter_id,
                reported_id=reported_id,
                report_type=report_type,
                content=content,
                status=status
            )
            db.session.add(report)
            db.session.commit()
            return report
        except Exception as e:
            logger.error(f"Error creating report: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, report_id):
        """Get a report by ID."""
        try:
            return cls.query.get(report_id)
        except Exception as e:
            logger.error(f"Error getting report by ID: {str(e)}")
            raise

    @classmethod
    def get_by_reporter_id(cls, reporter_id):
        """Get reports given by a user."""
        try:
            return cls.query.filter_by(reporter_id=reporter_id).all()
        except Exception as e:
            logger.error(f"Error getting reports by reporter ID: {str(e)}")
            raise

    @classmethod
    def get_by_reported_id(cls, reported_id):
        """Get reports received by a user."""
        try:
            return cls.query.filter_by(reported_id=reported_id).all()
        except Exception as e:
            logger.error(f"Error getting reports by reported ID: {str(e)}")
            raise

    @classmethod
    def get_by_status(cls, status):
        """Get reports by status."""
        try:
            return cls.query.filter_by(status=status).all()
        except Exception as e:
            logger.error(f"Error getting reports by status: {str(e)}")
            raise

    def update(self, status=None, content=None):
        """Update a report."""
        try:
            if status is not None:
                self.status = status
            if content is not None:
                self.content = content
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error updating report: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a report."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting report: {str(e)}")
            db.session.rollback()
            raise 