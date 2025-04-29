from datetime import datetime

# Import db from app's new location
try:
    from simple_command_translator import db
except ImportError:
    # Keep compatibility with main.py
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and personalization"""
    __tablename__ = 'users'  # Changed from 'user' to avoid conflicts
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    command_history = db.relationship('CommandHistory', backref='user', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')
    custom_commands = db.relationship('CustomCommand', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


class CommandHistory(db.Model):
    """Stores history of command translations for users"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Updated FK
    query = db.Column(db.Text, nullable=False)
    command = db.Column(db.Text, nullable=False)
    command_type = db.Column(db.String(20), nullable=False)  # 'linux' or 'powershell'
    executed = db.Column(db.Boolean, default=False)
    execution_output = db.Column(db.Text, nullable=True)
    execution_success = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    remote_execution = db.Column(db.Boolean, default=False)  # Flag for remote execution
    
    # Security and tracking fields
    command_hash = db.Column(db.String(64), nullable=True)
    watermark = db.Column(db.String(64), nullable=True)
    risk_level = db.Column(db.Integer, default=0)  # 0-3 risk scale
    
    # Remote session info
    remote_session_id = db.Column(db.Integer, db.ForeignKey('remote_session.id'), nullable=True)
    
    def __repr__(self):
        return f'<CommandHistory {self.id}: {self.command[:20]}...>'


class Favorite(db.Model):
    """Stores favorite/saved commands for quick access"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Updated FK
    command = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    command_type = db.Column(db.String(20), nullable=False)  # 'linux' or 'powershell'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Favorite {self.id}: {self.command[:20]}...>'


class CustomCommand(db.Model):
    """Stores custom command templates and libraries"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Updated FK
    name = db.Column(db.String(100), nullable=False)
    command_template = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    command_type = db.Column(db.String(20), nullable=False)  # 'linux' or 'powershell'
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CustomCommand {self.name}>'


class SecurityAudit(db.Model):
    """Tracks security events and potential issues"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Updated FK
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    command_id = db.Column(db.Integer, db.ForeignKey('command_history.id'), nullable=True)
    risk_level = db.Column(db.Integer, nullable=False)  # 0-3 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SecurityAudit {self.id}: {self.event_type}>'


class CommandLibrary(db.Model):
    """Pre-defined command libraries for specific environments or use cases"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    command_type = db.Column(db.String(20), nullable=False)  # 'linux' or 'powershell'
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Updated FK
    
    # Relationships
    commands = db.relationship('LibraryCommand', backref='library', lazy='dynamic')
    
    def __repr__(self):
        return f'<CommandLibrary {self.name}>'


class LibraryCommand(db.Model):
    """Individual commands within a command library"""
    id = db.Column(db.Integer, primary_key=True)
    library_id = db.Column(db.Integer, db.ForeignKey('command_library.id'), nullable=False)
    command = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    example_usage = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LibraryCommand {self.id}: {self.command[:20]}...>'


class License(db.Model):
    """License management for commercial use"""
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(64), unique=True, nullable=False)
    license_type = db.Column(db.String(50), nullable=False)  # 'single', 'team', 'enterprise'
    organization = db.Column(db.String(200), nullable=True)
    contact_name = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    max_users = db.Column(db.Integer, nullable=True)
    features = db.Column(db.Text, nullable=True)  # JSON string of enabled features
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    users = db.relationship('User', secondary='user_license', lazy='dynamic')
    
    def __repr__(self):
        return f'<License {self.license_key}: {self.license_type}>'


# Association table for user-license many-to-many relationship
user_license = db.Table('user_license',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),  # Updated FK
    db.Column('license_id', db.Integer, db.ForeignKey('license.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow)
)


class RemoteSession(db.Model):
    """
    Records remote execution sessions with detailed tracking
    Copyright (c) 2024 Ervin Remus Radosavlevici
    """
    __tablename__ = 'remote_session'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_type = db.Column(db.String(20), nullable=False)  # 'linux' or 'powershell'
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # Client IP
    
    # Security fields
    session_hash = db.Column(db.String(64), nullable=False)  # DNA-based security hash
    session_watermark = db.Column(db.String(100), nullable=True)
    audit_log = db.Column(db.Text, nullable=True)  # JSON log of session activities
    
    # Relationships
    commands = db.relationship('CommandHistory', backref='remote_session', lazy='dynamic')
    user = db.relationship('User', backref='remote_sessions')
    
    def __repr__(self):
        return f'<RemoteSession {self.id}: {self.host}:{self.port} ({self.session_type})>'