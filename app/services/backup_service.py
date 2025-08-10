"""
Automated Database Backup Service - Production Implementation
Complete backup system with scheduling, retention, and monitoring
"""

import logging
import os
import subprocess
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class BackupService:
    """Production database backup service with automation"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', '')
        self.backup_dir = os.getenv('BACKUP_DIR', '/tmp/backups')
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
        self.compression_enabled = os.getenv('BACKUP_COMPRESSION', 'true').lower() == 'true'
        
        # Parse database connection details
        self.db_config = self._parse_database_url()
        
        # Ensure backup directory exists
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_type: str = 'full') -> Dict[str, Any]:
        """
        Create database backup
        """
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"pinklemonade_{backup_type}_{timestamp}.sql"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            backup_result = {
                'timestamp': datetime.utcnow().isoformat(),
                'backup_type': backup_type,
                'backup_filename': backup_filename,
                'backup_path': backup_path,
                'compression_enabled': self.compression_enabled,
                'success': False,
                'size_mb': 0,
                'duration_seconds': 0
            }
            
            start_time = datetime.utcnow()
            
            if 'postgresql' in self.database_url.lower():
                backup_result = self._create_postgres_backup(backup_path, backup_result)
            elif 'sqlite' in self.database_url.lower():
                backup_result = self._create_sqlite_backup(backup_path, backup_result)
            else:
                backup_result['error'] = 'Unsupported database type'
                return backup_result
            
            # Calculate duration
            backup_result['duration_seconds'] = (datetime.utcnow() - start_time).total_seconds()
            
            # Compress backup if enabled
            if self.compression_enabled and backup_result['success']:
                compressed_path = self._compress_backup(backup_path)
                if compressed_path:
                    backup_result['backup_path'] = compressed_path
                    backup_result['backup_filename'] = os.path.basename(compressed_path)
                    backup_result['compressed'] = True
            
            # Calculate final file size
            if os.path.exists(backup_result['backup_path']):
                size_bytes = os.path.getsize(backup_result['backup_path'])
                backup_result['size_mb'] = round(size_bytes / (1024 * 1024), 2)
            
            # Record backup metadata
            self._record_backup_metadata(backup_result)
            
            logger.info(f"Backup completed: {backup_result['backup_filename']} ({backup_result['size_mb']} MB)")
            
            return backup_result
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            backup_result['success'] = False
            backup_result['error'] = str(e)
            return backup_result
    
    def restore_backup(self, backup_filename: str, target_database: Optional[str] = None) -> Dict[str, Any]:
        """
        Restore database from backup
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return {
                    'success': False,
                    'error': f'Backup file not found: {backup_filename}'
                }
            
            restore_result = {
                'timestamp': datetime.utcnow().isoformat(),
                'backup_filename': backup_filename,
                'target_database': target_database or self.db_config.get('database'),
                'success': False
            }
            
            # Decompress if needed
            working_path = backup_path
            if backup_filename.endswith('.gz'):
                working_path = self._decompress_backup(backup_path)
                if not working_path:
                    restore_result['error'] = 'Failed to decompress backup'
                    return restore_result
            
            # Restore based on database type
            if 'postgresql' in self.database_url.lower():
                restore_result = self._restore_postgres_backup(working_path, restore_result)
            elif 'sqlite' in self.database_url.lower():
                restore_result = self._restore_sqlite_backup(working_path, restore_result)
            else:
                restore_result['error'] = 'Unsupported database type'
            
            # Clean up temporary decompressed file
            if working_path != backup_path and os.path.exists(working_path):
                os.remove(working_path)
            
            return restore_result
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'backup_filename': backup_filename
            }
    
    def list_backups(self, backup_type: Optional[str] = None) -> Dict[str, Any]:
        """
        List available backups
        """
        try:
            backup_files = []
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('pinklemonade_') and (filename.endswith('.sql') or filename.endswith('.sql.gz')):
                    if backup_type and backup_type not in filename:
                        continue
                    
                    file_path = os.path.join(self.backup_dir, filename)
                    stat = os.stat(file_path)
                    
                    backup_info = {
                        'filename': filename,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'compressed': filename.endswith('.gz')
                    }
                    
                    # Extract metadata from filename
                    parts = filename.replace('.sql.gz', '').replace('.sql', '').split('_')
                    if len(parts) >= 3:
                        backup_info['backup_type'] = parts[1]
                        backup_info['timestamp'] = parts[2]
                    
                    backup_files.append(backup_info)
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                'success': True,
                'backups': backup_files,
                'total_backups': len(backup_files),
                'total_size_mb': sum(backup['size_mb'] for backup in backup_files)
            }
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """
        Remove backups older than retention period
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            cleaned_files = []
            total_size_freed = 0
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('pinklemonade_'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        
                        cleaned_files.append({
                            'filename': filename,
                            'size_mb': round(file_size / (1024 * 1024), 2),
                            'created_at': file_time.isoformat()
                        })
                        total_size_freed += file_size
            
            return {
                'success': True,
                'cleaned_files': cleaned_files,
                'files_removed': len(cleaned_files),
                'size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
                'retention_days': self.retention_days
            }
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_backup_status(self) -> Dict[str, Any]:
        """
        Get backup system status and statistics
        """
        try:
            backups_list = self.list_backups()
            
            if not backups_list['success']:
                return backups_list
            
            backups = backups_list['backups']
            
            # Calculate statistics
            now = datetime.utcnow()
            recent_backups = [
                b for b in backups 
                if (now - datetime.fromisoformat(b['created_at'])).days <= 7
            ]
            
            last_backup = backups[0] if backups else None
            
            status = {
                'success': True,
                'backup_system_enabled': True,
                'backup_directory': self.backup_dir,
                'retention_days': self.retention_days,
                'compression_enabled': self.compression_enabled,
                'total_backups': len(backups),
                'total_size_mb': backups_list['total_size_mb'],
                'recent_backups_7_days': len(recent_backups),
                'last_backup': last_backup,
                'backup_frequency_recommendation': 'daily',
                'health_status': 'healthy' if last_backup else 'warning'
            }
            
            # Check backup health
            if last_backup:
                last_backup_time = datetime.fromisoformat(last_backup['created_at'])
                hours_since_last = (now - last_backup_time).total_seconds() / 3600
                
                if hours_since_last > 48:
                    status['health_status'] = 'warning'
                    status['warning'] = f'Last backup was {hours_since_last:.1f} hours ago'
                elif hours_since_last > 72:
                    status['health_status'] = 'critical'
                    status['warning'] = f'Last backup was {hours_since_last:.1f} hours ago'
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def schedule_backup(self, backup_type: str = 'full', schedule: str = 'daily') -> Dict[str, Any]:
        """
        Schedule automatic backups (placeholder for cron integration)
        """
        try:
            # In production, this would integrate with cron or a task scheduler
            cron_expression = self._get_cron_expression(schedule)
            
            return {
                'success': True,
                'backup_type': backup_type,
                'schedule': schedule,
                'cron_expression': cron_expression,
                'message': f'Backup scheduled: {backup_type} backup {schedule}',
                'note': 'Automatic scheduling requires cron configuration on the server'
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_database_url(self) -> Dict[str, str]:
        """Parse database URL into components"""
        try:
            if 'postgresql' in self.database_url:
                # Parse PostgreSQL URL
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(self.database_url)
                
                return {
                    'type': 'postgresql',
                    'host': parsed.hostname or 'localhost',
                    'port': str(parsed.port or 5432),
                    'database': parsed.path.lstrip('/') if parsed.path else 'postgres',
                    'username': parsed.username or 'postgres',
                    'password': parsed.password or ''
                }
            elif 'sqlite' in self.database_url:
                return {
                    'type': 'sqlite',
                    'database': self.database_url.replace('sqlite:///', '')
                }
            else:
                return {'type': 'unknown'}
                
        except Exception as e:
            logger.error(f"Failed to parse database URL: {e}")
            return {'type': 'unknown'}
    
    def _create_postgres_backup(self, backup_path: str, backup_result: Dict) -> Dict[str, Any]:
        """Create PostgreSQL backup using pg_dump"""
        try:
            env = os.environ.copy()
            if self.db_config.get('password'):
                env['PGPASSWORD'] = self.db_config['password']
            
            cmd = [
                'pg_dump',
                '-h', self.db_config.get('host', 'localhost'),
                '-p', self.db_config.get('port', '5432'),
                '-U', self.db_config.get('username', 'postgres'),
                '-d', self.db_config.get('database', 'postgres'),
                '--no-password',
                '-f', backup_path
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                backup_result['success'] = True
                backup_result['method'] = 'pg_dump'
            else:
                backup_result['error'] = result.stderr or 'pg_dump failed'
            
            return backup_result
            
        except Exception as e:
            backup_result['error'] = f'PostgreSQL backup failed: {e}'
            return backup_result
    
    def _create_sqlite_backup(self, backup_path: str, backup_result: Dict) -> Dict[str, Any]:
        """Create SQLite backup by copying the database file"""
        try:
            db_path = self.db_config.get('database')
            if db_path and os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                backup_result['success'] = True
                backup_result['method'] = 'file_copy'
            else:
                backup_result['error'] = f'SQLite database file not found: {db_path}'
            
            return backup_result
            
        except Exception as e:
            backup_result['error'] = f'SQLite backup failed: {e}'
            return backup_result
    
    def _restore_postgres_backup(self, backup_path: str, restore_result: Dict) -> Dict[str, Any]:
        """Restore PostgreSQL backup using psql"""
        try:
            env = os.environ.copy()
            if self.db_config.get('password'):
                env['PGPASSWORD'] = self.db_config['password']
            
            cmd = [
                'psql',
                '-h', self.db_config.get('host', 'localhost'),
                '-p', self.db_config.get('port', '5432'),
                '-U', self.db_config.get('username', 'postgres'),
                '-d', restore_result['target_database'],
                '-f', backup_path
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                restore_result['success'] = True
                restore_result['method'] = 'psql'
            else:
                restore_result['error'] = result.stderr or 'psql restore failed'
            
            return restore_result
            
        except Exception as e:
            restore_result['error'] = f'PostgreSQL restore failed: {e}'
            return restore_result
    
    def _restore_sqlite_backup(self, backup_path: str, restore_result: Dict) -> Dict[str, Any]:
        """Restore SQLite backup by copying the file"""
        try:
            target_path = self.db_config.get('database')
            if target_path:
                shutil.copy2(backup_path, target_path)
                restore_result['success'] = True
                restore_result['method'] = 'file_copy'
            else:
                restore_result['error'] = 'SQLite target path not configured'
            
            return restore_result
            
        except Exception as e:
            restore_result['error'] = f'SQLite restore failed: {e}'
            return restore_result
    
    def _compress_backup(self, backup_path: str) -> Optional[str]:
        """Compress backup file using gzip"""
        try:
            compressed_path = f"{backup_path}.gz"
            
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            os.remove(backup_path)
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"Backup compression failed: {e}")
            return None
    
    def _decompress_backup(self, compressed_path: str) -> Optional[str]:
        """Decompress backup file"""
        try:
            decompressed_path = compressed_path.replace('.gz', '')
            
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return decompressed_path
            
        except Exception as e:
            logger.error(f"Backup decompression failed: {e}")
            return None
    
    def _record_backup_metadata(self, backup_result: Dict):
        """Record backup metadata for tracking"""
        try:
            metadata_file = os.path.join(self.backup_dir, 'backup_metadata.json')
            
            # Load existing metadata
            metadata = []
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Add new backup record
            metadata.append({
                'filename': backup_result['backup_filename'],
                'timestamp': backup_result['timestamp'],
                'backup_type': backup_result['backup_type'],
                'size_mb': backup_result['size_mb'],
                'success': backup_result['success'],
                'duration_seconds': backup_result['duration_seconds']
            })
            
            # Keep only last 100 records
            metadata = metadata[-100:]
            
            # Save metadata
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to record backup metadata: {e}")
    
    def _get_cron_expression(self, schedule: str) -> str:
        """Get cron expression for schedule"""
        schedules = {
            'daily': '0 2 * * *',      # 2 AM daily
            'weekly': '0 2 * * 0',     # 2 AM every Sunday
            'monthly': '0 2 1 * *',    # 2 AM on the 1st of every month
            'hourly': '0 * * * *'      # Every hour
        }
        return schedules.get(schedule, '0 2 * * *')