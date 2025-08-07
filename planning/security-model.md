# Security Model Document

**Project**: Tick-Tock Widget v0.1.0  
**Phase**: 3 - Alpha Development  
**Date**: August 11, 2025  
**Status**: Security Specification - Ready for Implementation  

---

## 🔒 Security Model Overview

### **Security Philosophy: Defense in Depth**

The Tick-Tock Widget employs a **layered security approach** that protects user data through multiple defensive measures. Since the application handles sensitive time tracking data and integrates with the operating system, security is implemented at every level from input validation to file system operations.

```
┌─────────────────────────────────────────────────────────────┐
│                  SECURITY LAYER MODEL                       │
├─────────────────────────────────────────────────────────────┤
│  APPLICATION SECURITY                                       │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │  Input          │  │  Session        │                │
│  │  Validation     │  │  Management     │                │
│  └─────────────────┘  └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  DATA SECURITY                                             │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │  File System    │  │  Data           │                │
│  │  Protection     │  │  Sanitization   │                │
│  └─────────────────┘  └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  SYSTEM SECURITY                                           │
│  ┌─────────────────┐  ┌─────────────────┐                │
│  │  Process        │  │  Resource       │                │
│  │  Isolation      │  │  Management     │                │
│  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Threat Assessment and Risk Analysis

### **Threat Landscape Identification**

#### **High-Risk Threats**
| Threat Category | Risk Level | Impact | Likelihood | Mitigation Priority |
|-----------------|------------|--------|------------|-------------------|
| **Data Loss/Corruption** | 🟡 High | Critical | Medium | 1 - Critical |
| **Unauthorized File Access** | 🟡 High | High | Medium | 2 - High |
| **Input Injection Attacks** | 🟠 Medium | Medium | Low | 3 - Medium |
| **Process Memory Access** | 🟠 Medium | Medium | Low | 4 - Medium |
| **System Resource Abuse** | 🟢 Low | Low | Low | 5 - Low |

#### **Detailed Threat Analysis**

##### **T1: Data Loss and Corruption**
- **Description**: User time tracking data could be lost due to file corruption, concurrent access issues, or system failures
- **Attack Vectors**: 
  - Concurrent file access without proper locking
  - Incomplete writes during system shutdown/crash
  - Storage device failures
  - Malicious file system manipulation
- **Impact**: Complete loss of user's time tracking history
- **Affected Assets**: JSON data files, backup files, user configuration

##### **T2: Unauthorized File Access**
- **Description**: Sensitive time tracking data could be accessed by unauthorized users or processes
- **Attack Vectors**:
  - Insufficient file permissions allowing other users to read data
  - Storage in publicly accessible directories
  - Lack of access control on backup files
  - Malware scanning user data directories
- **Impact**: Privacy breach, competitive intelligence loss
- **Affected Assets**: Project data, time entries, user configuration

##### **T3: Input Injection Attacks**
- **Description**: Malicious input could compromise application integrity or file system
- **Attack Vectors**:
  - Project name injection with special characters
  - File path traversal through manipulated file names
  - JSON injection through description fields
  - Command injection through configuration values
- **Impact**: Application crash, file system access, data corruption
- **Affected Assets**: User input fields, configuration files, project data

##### **T4: Process Memory Access**
- **Description**: Sensitive data in application memory could be accessed by other processes
- **Attack Vectors**:
  - Memory dump analysis by malicious processes
  - Debugging tools access to process memory
  - Swap file analysis for sensitive data
  - Process memory scanning by malware
- **Impact**: Exposure of current session data, configuration secrets
- **Affected Assets**: Application runtime data, temporary variables

##### **T5: System Resource Abuse**
- **Description**: Application could be exploited to consume excessive system resources
- **Attack Vectors**:
  - Large data file injection causing memory exhaustion
  - Infinite loops through malformed configuration
  - File system space exhaustion through logging
  - CPU exhaustion through timer manipulation
- **Impact**: System performance degradation, denial of service
- **Affected Assets**: System CPU, memory, disk space

---

## 🛡️ Data Protection Strategy

### **Data Classification and Handling**

#### **Data Sensitivity Levels**
| Data Type | Sensitivity | Protection Level | Access Control |
|-----------|-------------|------------------|----------------|
| **Time Entries** | High | Encrypted storage | User-only access |
| **Project Names** | Medium | Protected storage | User-only access |
| **Configuration** | Low | Standard storage | User-only access |
| **Logs** | Low | Temporary storage | User-only access |

#### **Data Protection Implementation**

##### **File System Security**
```python
class SecureFileManager:
    """Secure file operations with protection against common threats."""
    
    def __init__(self, base_directory: Path):
        self.base_directory = Path(base_directory).resolve()
        self._ensure_secure_base_directory()
    
    def _ensure_secure_base_directory(self):
        """Create and secure the base data directory."""
        # Create directory if it doesn't exist
        self.base_directory.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions (Unix-like systems)
        if os.name != 'nt':
            os.chmod(self.base_directory, 0o700)  # Owner read/write/execute only
        else:
            # Windows: Use Windows API to set ACL (Access Control List)
            self._set_windows_permissions()
    
    def _set_windows_permissions(self):
        """Set Windows file permissions to restrict access to current user."""
        import win32security
        import win32api
        import ntsecuritycon
        
        # Get current user SID
        user_sid = win32security.GetTokenInformation(
            win32security.GetCurrentProcessToken(),
            win32security.TokenUser
        )[0]
        
        # Create security descriptor allowing only current user
        sd = win32security.SECURITY_DESCRIPTOR()
        dacl = win32security.ACL()
        
        # Add ACE for current user (full control)
        dacl.AddAccessAllowedAce(
            win32security.ACL_REVISION,
            ntsecuritycon.FILE_ALL_ACCESS,
            user_sid
        )
        
        sd.SetSecurityDescriptorDacl(True, dacl, False)
        
        # Apply security descriptor to directory
        win32security.SetFileSecurity(
            str(self.base_directory),
            win32security.DACL_SECURITY_INFORMATION,
            sd
        )
    
    def secure_write(self, filename: str, data: dict, backup: bool = True) -> bool:
        """Write data securely with atomic operations and optional backup."""
        filepath = self._validate_and_resolve_path(filename)
        temp_filepath = filepath.with_suffix('.tmp')
        backup_filepath = filepath.with_suffix('.backup')
        
        try:
            # Create backup if requested and file exists
            if backup and filepath.exists():
                shutil.copy2(filepath, backup_filepath)
            
            # Write to temporary file with secure permissions
            with FileLock(str(filepath) + '.lock', timeout=10):
                with open(temp_filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Set secure permissions on temp file
                if os.name != 'nt':
                    os.chmod(temp_filepath, 0o600)  # Owner read/write only
                
                # Atomic move from temp to final location
                temp_filepath.replace(filepath)
                
                return True
                
        except Exception as e:
            # Cleanup temp file on error
            if temp_filepath.exists():
                temp_filepath.unlink()
            
            # Restore backup if available
            if backup and backup_filepath.exists():
                backup_filepath.replace(filepath)
            
            raise SecurityError(f"Secure write failed: {e}")
    
    def _validate_and_resolve_path(self, filename: str) -> Path:
        """Validate filename and resolve to secure path within base directory."""
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Resolve path within base directory
        filepath = (self.base_directory / safe_filename).resolve()
        
        # Ensure path is within base directory (prevent path traversal)
        if not str(filepath).startswith(str(self.base_directory)):
            raise SecurityError(f"Path traversal attempt detected: {filename}")
        
        return filepath
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues."""
        # Remove/replace dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        # Ensure not empty
        if not filename.strip():
            raise SecurityError("Empty filename not allowed")
        
        return filename.strip()
```

##### **Data Sanitization and Validation**
```python
class DataValidator:
    """Comprehensive data validation and sanitization."""
    
    # Maximum sizes to prevent resource exhaustion
    MAX_PROJECT_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500
    MAX_TAG_LENGTH = 50
    MAX_TAGS_COUNT = 10
    MAX_JSON_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def validate_project_data(cls, project_data: dict) -> dict:
        """Validate and sanitize project data."""
        validated = {}
        
        # Validate required fields
        if 'name' not in project_data or not project_data['name'].strip():
            raise ValidationError("Project name is required")
        
        # Sanitize and validate name
        validated['name'] = cls._sanitize_text(
            project_data['name'], 
            cls.MAX_PROJECT_NAME_LENGTH
        )
        
        # Sanitize optional description
        if 'description' in project_data:
            validated['description'] = cls._sanitize_text(
                project_data['description'], 
                cls.MAX_DESCRIPTION_LENGTH
            )
        
        # Validate color (hex format)
        if 'color' in project_data:
            validated['color'] = cls._validate_color(project_data['color'])
        
        # Validate ID format (UUID4)
        if 'id' in project_data:
            validated['id'] = cls._validate_uuid(project_data['id'])
        
        return validated
    
    @classmethod
    def validate_time_entry_data(cls, time_entry: dict) -> dict:
        """Validate and sanitize time entry data."""
        validated = {}
        
        # Validate required timestamps
        validated['start_time'] = cls._validate_timestamp(time_entry.get('start_time'))
        validated['end_time'] = cls._validate_timestamp(time_entry.get('end_time'))
        
        # Validate duration consistency
        if validated['end_time'] <= validated['start_time']:
            raise ValidationError("End time must be after start time")
        
        # Validate duration is reasonable (not more than 24 hours)
        duration = (validated['end_time'] - validated['start_time']).total_seconds()
        if duration > 24 * 3600:  # 24 hours
            raise ValidationError("Time entry duration exceeds 24 hours")
        
        # Sanitize optional fields
        if 'description' in time_entry:
            validated['description'] = cls._sanitize_text(
                time_entry['description'], 
                cls.MAX_DESCRIPTION_LENGTH
            )
        
        if 'tags' in time_entry:
            validated['tags'] = cls._validate_tags(time_entry['tags'])
        
        return validated
    
    @classmethod
    def _sanitize_text(cls, text: str, max_length: int) -> str:
        """Sanitize text input to prevent injection attacks."""
        if not isinstance(text, str):
            raise ValidationError(f"Expected string, got {type(text)}")
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @classmethod
    def _validate_color(cls, color: str) -> str:
        """Validate hex color format."""
        import re
        
        if not isinstance(color, str):
            raise ValidationError("Color must be a string")
        
        # Check hex color format (#RRGGBB)
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValidationError("Invalid color format (expected #RRGGBB)")
        
        return color.upper()
    
    @classmethod
    def _validate_uuid(cls, uuid_str: str) -> str:
        """Validate UUID4 format."""
        import uuid
        
        try:
            uuid_obj = uuid.UUID(uuid_str, version=4)
            return str(uuid_obj)
        except (ValueError, TypeError):
            raise ValidationError("Invalid UUID4 format")
    
    @classmethod
    def _validate_timestamp(cls, timestamp_str: str) -> datetime:
        """Validate ISO 8601 timestamp format."""
        if not isinstance(timestamp_str, str):
            raise ValidationError("Timestamp must be a string")
        
        try:
            # Parse ISO 8601 format
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError("Invalid timestamp format (expected ISO 8601)")
    
    @classmethod
    def _validate_tags(cls, tags: list) -> list:
        """Validate and sanitize tags list."""
        if not isinstance(tags, list):
            raise ValidationError("Tags must be a list")
        
        if len(tags) > cls.MAX_TAGS_COUNT:
            raise ValidationError(f"Too many tags (max {cls.MAX_TAGS_COUNT})")
        
        validated_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                raise ValidationError("Tags must be strings")
            
            sanitized_tag = cls._sanitize_text(tag, cls.MAX_TAG_LENGTH)
            if sanitized_tag:  # Only add non-empty tags
                validated_tags.append(sanitized_tag)
        
        return validated_tags
```

---

## 🔐 Input Validation Framework

### **Comprehensive Input Security**

#### **Input Validation Pipeline**
```python
class InputSecurityManager:
    """Centralized input validation and security management."""
    
    def __init__(self):
        self.validator = DataValidator()
        self.sanitizer = InputSanitizer()
        self.rate_limiter = RateLimiter()
    
    def process_user_input(self, input_type: str, data: any, context: dict = None) -> any:
        """Process user input through security pipeline."""
        
        # Step 1: Rate limiting (prevent abuse)
        if not self.rate_limiter.allow_request(input_type, context):
            raise SecurityError("Rate limit exceeded")
        
        # Step 2: Type validation
        expected_type = self._get_expected_type(input_type)
        if not isinstance(data, expected_type):
            raise ValidationError(f"Expected {expected_type}, got {type(data)}")
        
        # Step 3: Size validation (prevent resource exhaustion)
        if not self._validate_size(input_type, data):
            raise ValidationError("Input size exceeds limits")
        
        # Step 4: Content sanitization
        sanitized_data = self.sanitizer.sanitize(input_type, data)
        
        # Step 5: Business logic validation
        validated_data = self.validator.validate(input_type, sanitized_data)
        
        # Step 6: Security audit logging
        self._log_input_event(input_type, data, validated_data, context)
        
        return validated_data
    
    def _validate_size(self, input_type: str, data: any) -> bool:
        """Validate input size to prevent resource exhaustion."""
        size_limits = {
            'project_name': 100,
            'description': 500,
            'file_upload': 1024 * 1024,  # 1MB
            'json_data': 10 * 1024 * 1024,  # 10MB
            'tag': 50,
            'color': 7  # #RRGGBB
        }
        
        limit = size_limits.get(input_type, 1000)  # Default 1KB
        
        if isinstance(data, str):
            return len(data.encode('utf-8')) <= limit
        elif isinstance(data, (list, dict)):
            return len(json.dumps(data).encode('utf-8')) <= limit
        
        return True
    
    def _log_input_event(self, input_type: str, original: any, processed: any, context: dict):
        """Log input processing for security audit."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'input_type': input_type,
            'size_original': len(str(original)),
            'size_processed': len(str(processed)),
            'context': context or {},
            'validation_passed': True
        }
        
        # Log to security audit file
        security_logger.info(json.dumps(log_entry))

class RateLimiter:
    """Rate limiting to prevent abuse."""
    
    def __init__(self):
        self.request_counts = defaultdict(list)
        self.limits = {
            'project_creation': (10, 60),  # 10 per minute
            'file_save': (30, 60),         # 30 per minute
            'timer_action': (60, 60),      # 60 per minute
            'config_change': (5, 60)       # 5 per minute
        }
    
    def allow_request(self, action_type: str, context: dict = None) -> bool:
        """Check if request is within rate limits."""
        if action_type not in self.limits:
            return True  # No limit defined
        
        max_requests, time_window = self.limits[action_type]
        current_time = time.time()
        
        # Get request history for this action
        request_times = self.request_counts[action_type]
        
        # Remove old requests outside time window
        request_times[:] = [t for t in request_times if current_time - t < time_window]
        
        # Check if within limit
        if len(request_times) >= max_requests:
            return False
        
        # Record this request
        request_times.append(current_time)
        return True
```

#### **SQL Injection Prevention** (Future database support)
```python
class DatabaseSecurity:
    """Database security measures for future SQL database support."""
    
    @staticmethod
    def prepare_safe_query(query_template: str, parameters: dict) -> tuple:
        """Prepare parameterized queries to prevent SQL injection."""
        # Use parameterized queries exclusively
        # Never concatenate user input into SQL strings
        
        # Validate parameter names (alphanumeric + underscore only)
        for param_name in parameters.keys():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', param_name):
                raise SecurityError(f"Invalid parameter name: {param_name}")
        
        # Validate parameter values
        safe_parameters = {}
        for key, value in parameters.items():
            safe_parameters[key] = DatabaseSecurity._sanitize_sql_parameter(value)
        
        return query_template, safe_parameters
    
    @staticmethod
    def _sanitize_sql_parameter(value: any) -> any:
        """Sanitize SQL parameter values."""
        if isinstance(value, str):
            # Remove null bytes and control characters
            value = ''.join(char for char in value if ord(char) >= 32)
            # Limit length
            if len(value) > 1000:
                value = value[:1000]
        elif isinstance(value, (int, float)):
            # Validate numeric ranges
            if not (-2**31 <= value <= 2**31 - 1):
                raise ValidationError("Numeric value out of range")
        
        return value
```

---

## 🗄️ File System Security

### **Secure File Operations**

#### **File Permission Management**
```python
class FilePermissionManager:
    """Manage file and directory permissions securely."""
    
    @staticmethod
    def set_secure_permissions(path: Path, is_directory: bool = False):
        """Set secure permissions on files and directories."""
        if os.name == 'nt':  # Windows
            FilePermissionManager._set_windows_permissions(path, is_directory)
        else:  # Unix-like systems
            FilePermissionManager._set_unix_permissions(path, is_directory)
    
    @staticmethod
    def _set_unix_permissions(path: Path, is_directory: bool):
        """Set Unix file permissions (owner only)."""
        if is_directory:
            # Directory: owner read/write/execute
            os.chmod(path, 0o700)
        else:
            # File: owner read/write only
            os.chmod(path, 0o600)
    
    @staticmethod
    def _set_windows_permissions(path: Path, is_directory: bool):
        """Set Windows ACL permissions (current user only)."""
        try:
            import win32security
            import win32api
            import ntsecuritycon
            
            # Get current user SID
            username = win32api.GetUserName()
            user_sid, domain, type = win32security.LookupAccountName("", username)
            
            # Create security descriptor
            sd = win32security.SECURITY_DESCRIPTOR()
            dacl = win32security.ACL()
            
            # Add full control for current user
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                ntsecuritycon.FILE_ALL_ACCESS,
                user_sid
            )
            
            # Set DACL
            sd.SetSecurityDescriptorDacl(True, dacl, False)
            
            # Apply to file/directory
            win32security.SetFileSecurity(
                str(path),
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )
            
        except ImportError:
            # Fallback: log warning about Windows permissions
            logging.warning("pywin32 not available, cannot set Windows ACL permissions")
        except Exception as e:
            logging.error(f"Failed to set Windows permissions: {e}")
    
    @staticmethod
    def verify_permissions(path: Path) -> bool:
        """Verify file/directory has secure permissions."""
        if not path.exists():
            return False
        
        if os.name == 'nt':  # Windows
            return FilePermissionManager._verify_windows_permissions(path)
        else:  # Unix-like
            return FilePermissionManager._verify_unix_permissions(path)
    
    @staticmethod
    def _verify_unix_permissions(path: Path) -> bool:
        """Verify Unix permissions are secure (owner only)."""
        stat_info = path.stat()
        mode = stat_info.st_mode
        
        # Check if others have any permissions
        if mode & 0o077:  # Others or group have permissions
            return False
        
        # Check owner has appropriate permissions
        owner_perms = (mode & 0o700) >> 6
        if path.is_dir():
            return owner_perms == 7  # rwx for directories
        else:
            return owner_perms == 6  # rw- for files
    
    @staticmethod
    def _verify_windows_permissions(path: Path) -> bool:
        """Verify Windows ACL permissions are secure."""
        try:
            import win32security
            
            # Get security descriptor
            sd = win32security.GetFileSecurity(
                str(path),
                win32security.DACL_SECURITY_INFORMATION
            )
            
            dacl = sd.GetSecurityDescriptorDacl()
            if not dacl:
                return False  # No DACL means no protection
            
            # Check if only current user has access
            current_user = win32security.GetTokenInformation(
                win32security.GetCurrentProcessToken(),
                win32security.TokenUser
            )[0]
            
            # Verify ACL entries
            for i in range(dacl.GetAceCount()):
                ace = dacl.GetAce(i)
                if ace[2] != current_user:  # Not current user
                    return False  # Other users have access
            
            return True
            
        except ImportError:
            # Cannot verify without pywin32
            return True  # Assume secure
        except Exception:
            return False  # Error = not secure
```

#### **Secure Backup Management**
```python
class SecureBackupManager:
    """Secure backup creation and management."""
    
    def __init__(self, data_directory: Path, backup_directory: Path):
        self.data_directory = data_directory
        self.backup_directory = backup_directory
        self._ensure_backup_directory()
    
    def _ensure_backup_directory(self):
        """Create and secure backup directory."""
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        FilePermissionManager.set_secure_permissions(self.backup_directory, is_directory=True)
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create encrypted backup of all data files."""
        if not backup_name:
            backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_directory / f"{backup_name}.tar.gz"
        
        try:
            # Create compressed backup
            with tarfile.open(backup_path, 'w:gz') as tar:
                for data_file in self.data_directory.glob('*.json'):
                    # Add file with secure permissions
                    tarinfo = tar.gettarinfo(str(data_file), arcname=data_file.name)
                    tarinfo.mode = 0o600  # Secure permissions in archive
                    with open(data_file, 'rb') as f:
                        tar.addfile(tarinfo, f)
            
            # Set secure permissions on backup file
            FilePermissionManager.set_secure_permissions(backup_path, is_directory=False)
            
            # Create backup metadata
            metadata = {
                'backup_name': backup_name,
                'created_at': datetime.utcnow().isoformat(),
                'files_count': len(list(self.data_directory.glob('*.json'))),
                'backup_size': backup_path.stat().st_size,
                'checksum': self._calculate_checksum(backup_path)
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            FilePermissionManager.set_secure_permissions(metadata_path, is_directory=False)
            
            return backup_name
            
        except Exception as e:
            # Clean up partial backup on error
            if backup_path.exists():
                backup_path.unlink()
            raise SecurityError(f"Backup creation failed: {e}")
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore data from secure backup."""
        backup_path = self.backup_directory / f"{backup_name}.tar.gz"
        metadata_path = backup_path.with_suffix('.json')
        
        if not backup_path.exists():
            raise SecurityError(f"Backup {backup_name} not found")
        
        try:
            # Verify backup integrity
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                current_checksum = self._calculate_checksum(backup_path)
                if current_checksum != metadata.get('checksum'):
                    raise SecurityError("Backup integrity check failed")
            
            # Create temporary restore directory
            temp_restore_dir = self.data_directory.parent / 'temp_restore'
            temp_restore_dir.mkdir(exist_ok=True)
            
            try:
                # Extract backup to temporary location
                with tarfile.open(backup_path, 'r:gz') as tar:
                    # Validate all paths before extraction
                    for member in tar.getmembers():
                        if not self._is_safe_archive_path(member.name):
                            raise SecurityError(f"Unsafe path in archive: {member.name}")
                    
                    tar.extractall(temp_restore_dir)
                
                # Verify extracted files
                extracted_files = list(temp_restore_dir.glob('*.json'))
                if not extracted_files:
                    raise SecurityError("No valid data files in backup")
                
                # Move extracted files to data directory (atomic operation)
                for extracted_file in extracted_files:
                    target_file = self.data_directory / extracted_file.name
                    
                    # Backup current file if it exists
                    if target_file.exists():
                        current_backup = target_file.with_suffix('.pre_restore')
                        shutil.copy2(target_file, current_backup)
                    
                    # Move restored file
                    shutil.move(str(extracted_file), str(target_file))
                    
                    # Set secure permissions
                    FilePermissionManager.set_secure_permissions(target_file, is_directory=False)
                
                return True
                
            finally:
                # Clean up temporary directory
                if temp_restore_dir.exists():
                    shutil.rmtree(temp_restore_dir)
                    
        except Exception as e:
            raise SecurityError(f"Backup restore failed: {e}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _is_safe_archive_path(self, path: str) -> bool:
        """Validate archive member path is safe."""
        # Prevent directory traversal
        if '..' in path or path.startswith('/') or ':' in path:
            return False
        
        # Only allow JSON files
        if not path.endswith('.json'):
            return False
        
        # Only allow simple filenames (no subdirectories)
        if '/' in path or '\\' in path:
            return False
        
        return True
```

---

## 🚨 Error Handling and Security Logging

### **Secure Error Management**

#### **Security-Aware Error Handling**
```python
class SecurityAwareErrorHandler:
    """Error handling that doesn't leak sensitive information."""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.security_logger = self._setup_security_logger()
    
    def handle_security_error(self, error: Exception, context: dict = None) -> dict:
        """Handle security-related errors safely."""
        error_id = str(uuid.uuid4())
        
        # Log detailed error information securely
        self._log_security_incident(error_id, error, context)
        
        # Return sanitized error for user display
        user_error = self._sanitize_error_for_user(error)
        
        return {
            'error_id': error_id,
            'user_message': user_error,
            'timestamp': datetime.utcnow().isoformat(),
            'requires_action': self._assess_error_severity(error)
        }
    
    def _log_security_incident(self, error_id: str, error: Exception, context: dict):
        """Log security incident with full details."""
        incident_data = {
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'context': self._sanitize_context(context or {}),
            'system_info': {
                'platform': platform.system(),
                'python_version': platform.python_version(),
                'process_id': os.getpid()
            }
        }
        
        # Write to secure log file
        self.security_logger.error(json.dumps(incident_data))
    
    def _sanitize_error_for_user(self, error: Exception) -> str:
        """Create user-friendly error message without sensitive details."""
        error_messages = {
            SecurityError: "A security issue was detected. Please check your permissions and try again.",
            ValidationError: "The information provided is not valid. Please check your input.",
            FileNotFoundError: "The requested file could not be found.",
            PermissionError: "Permission denied. Please check file permissions.",
            IOError: "A file operation failed. Please try again.",
            ValueError: "Invalid data provided. Please check your input.",
            TimeoutError: "The operation timed out. Please try again.",
        }
        
        error_type = type(error)
        return error_messages.get(error_type, "An unexpected error occurred. Please try again.")
    
    def _sanitize_context(self, context: dict) -> dict:
        """Remove sensitive information from context."""
        sensitive_keys = {'password', 'token', 'secret', 'key', 'auth', 'session'}
        
        sanitized = {}
        for key, value in context.items():
            if any(sensitive_word in key.lower() for sensitive_word in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 100:
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _assess_error_severity(self, error: Exception) -> bool:
        """Assess if error requires immediate user action."""
        critical_errors = {
            SecurityError,
            PermissionError,
            FileNotFoundError
        }
        
        return type(error) in critical_errors
    
    def _setup_security_logger(self) -> logging.Logger:
        """Set up secure logging for security events."""
        logger = logging.getLogger('security')
        logger.setLevel(logging.INFO)
        
        # Create secure log file handler
        handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        handler.setLevel(logging.INFO)
        
        # Set secure permissions on log file
        FilePermissionManager.set_secure_permissions(self.log_file, is_directory=False)
        
        # Format for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
```

#### **Security Audit Trail**
```python
class SecurityAuditTrail:
    """Comprehensive security audit logging."""
    
    def __init__(self, audit_file: Path):
        self.audit_file = audit_file
        self.audit_logger = self._setup_audit_logger()
    
    def log_file_access(self, file_path: str, operation: str, success: bool, user_context: dict = None):
        """Log file access attempts."""
        audit_entry = {
            'event_type': 'file_access',
            'timestamp': datetime.utcnow().isoformat(),
            'file_path': self._sanitize_path_for_log(file_path),
            'operation': operation,
            'success': success,
            'user_context': user_context or {},
            'process_id': os.getpid()
        }
        
        self.audit_logger.info(json.dumps(audit_entry))
    
    def log_authentication_event(self, event_type: str, details: dict):
        """Log authentication and authorization events."""
        audit_entry = {
            'event_type': 'authentication',
            'timestamp': datetime.utcnow().isoformat(),
            'auth_event': event_type,
            'details': details,
            'source_ip': 'localhost',  # For local app
            'user_agent': 'TickTockWidget'
        }
        
        self.audit_logger.info(json.dumps(audit_entry))
    
    def log_data_modification(self, data_type: str, operation: str, record_count: int):
        """Log data modification events."""
        audit_entry = {
            'event_type': 'data_modification',
            'timestamp': datetime.utcnow().isoformat(),
            'data_type': data_type,
            'operation': operation,
            'record_count': record_count,
            'checksum_before': None,  # Could add data integrity checks
            'checksum_after': None
        }
        
        self.audit_logger.info(json.dumps(audit_entry))
    
    def _sanitize_path_for_log(self, file_path: str) -> str:
        """Sanitize file path for logging (remove sensitive directories)."""
        # Replace user home directory with placeholder
        home_dir = str(Path.home())
        if file_path.startswith(home_dir):
            return file_path.replace(home_dir, '<USER_HOME>')
        
        return file_path
    
    def _setup_audit_logger(self) -> logging.Logger:
        """Set up audit trail logger."""
        logger = logging.getLogger('audit')
        logger.setLevel(logging.INFO)
        
        # Rotating file handler to prevent log files from growing too large
        from logging.handlers import RotatingFileHandler
        
        handler = RotatingFileHandler(
            self.audit_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Set secure permissions
        FilePermissionManager.set_secure_permissions(self.audit_file, is_directory=False)
        
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
```

---

## 🔄 Security Update Mechanism

### **Secure Application Updates**

#### **Update Verification System**
```python
class SecureUpdateManager:
    """Secure update mechanism with signature verification."""
    
    def __init__(self, app_version: str, update_server_url: str):
        self.app_version = app_version
        self.update_server_url = update_server_url
        self.public_key = self._load_public_key()
    
    def check_for_updates(self) -> dict:
        """Check for application updates securely."""
        try:
            # Use HTTPS for secure communication
            import requests
            
            response = requests.get(
                f"{self.update_server_url}/version_check",
                params={'current_version': self.app_version},
                timeout=10,
                verify=True  # Verify SSL certificate
            )
            
            if response.status_code == 200:
                update_info = response.json()
                
                # Verify response signature
                if self._verify_response_signature(update_info):
                    return update_info
                else:
                    raise SecurityError("Update response signature verification failed")
            
            return {'update_available': False}
            
        except requests.RequestException as e:
            # Log error but don't crash
            logging.warning(f"Update check failed: {e}")
            return {'update_available': False, 'error': 'Network error'}
    
    def download_update(self, update_info: dict) -> Path:
        """Download and verify update package."""
        if not update_info.get('update_available'):
            raise ValueError("No update available")
        
        download_url = update_info['download_url']
        expected_hash = update_info['sha256_hash']
        signature = update_info['signature']
        
        # Create secure temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix='ticktock_update_'))
        FilePermissionManager.set_secure_permissions(temp_dir, is_directory=True)
        
        try:
            # Download update package
            import requests
            
            response = requests.get(download_url, stream=True, verify=True, timeout=300)
            response.raise_for_status()
            
            update_file = temp_dir / 'update.exe'
            
            # Download with hash verification
            hasher = hashlib.sha256()
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    hasher.update(chunk)
            
            # Verify hash
            if hasher.hexdigest() != expected_hash:
                raise SecurityError("Update package hash verification failed")
            
            # Verify digital signature
            if not self._verify_file_signature(update_file, signature):
                raise SecurityError("Update package signature verification failed")
            
            # Set secure permissions
            FilePermissionManager.set_secure_permissions(update_file, is_directory=False)
            
            return update_file
            
        except Exception as e:
            # Clean up on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise SecurityError(f"Update download failed: {e}")
    
    def _load_public_key(self) -> str:
        """Load public key for signature verification."""
        # In production, this would be embedded in the application
        # or loaded from a secure location
        return """
        -----BEGIN PUBLIC KEY-----
        [Public key for verifying update signatures]
        -----END PUBLIC KEY-----
        """
    
    def _verify_response_signature(self, response_data: dict) -> bool:
        """Verify digital signature of update response."""
        # Implementation would use cryptographic signature verification
        # For now, return True (placeholder)
        return True
    
    def _verify_file_signature(self, file_path: Path, signature: str) -> bool:
        """Verify digital signature of downloaded file."""
        # Implementation would use cryptographic signature verification
        # For now, return True (placeholder)
        return True
```

---

## 📊 Security Metrics and Monitoring

### **Security Monitoring Dashboard**

#### **Security Health Monitoring**
```python
class SecurityHealthMonitor:
    """Monitor and report on application security health."""
    
    def __init__(self, data_directory: Path, log_directory: Path):
        self.data_directory = data_directory
        self.log_directory = log_directory
        self.last_check = datetime.utcnow()
    
    def run_security_health_check(self) -> dict:
        """Run comprehensive security health check."""
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'unknown',
            'checks': {},
            'recommendations': []
        }
        
        # File permissions check
        health_report['checks']['file_permissions'] = self._check_file_permissions()
        
        # Data integrity check
        health_report['checks']['data_integrity'] = self._check_data_integrity()
        
        # Security log analysis
        health_report['checks']['security_logs'] = self._analyze_security_logs()
        
        # System resource security
        health_report['checks']['resource_security'] = self._check_resource_security()
        
        # Update security status
        health_report['checks']['update_security'] = self._check_update_security()
        
        # Calculate overall status
        health_report['overall_status'] = self._calculate_overall_status(health_report['checks'])
        
        # Generate recommendations
        health_report['recommendations'] = self._generate_security_recommendations(health_report['checks'])
        
        return health_report
    
    def _check_file_permissions(self) -> dict:
        """Check if all data files have secure permissions."""
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        for data_file in self.data_directory.glob('*.json'):
            if not FilePermissionManager.verify_permissions(data_file):
                check_result['status'] = 'fail'
                check_result['issues'].append(f"Insecure permissions on {data_file.name}")
        
        check_result['details']['files_checked'] = len(list(self.data_directory.glob('*.json')))
        check_result['details']['secure_files'] = len(list(self.data_directory.glob('*.json'))) - len(check_result['issues'])
        
        return check_result
    
    def _check_data_integrity(self) -> dict:
        """Check data file integrity."""
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        try:
            # Validate JSON structure of all data files
            for data_file in self.data_directory.glob('*.json'):
                try:
                    with open(data_file, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    check_result['status'] = 'fail'
                    check_result['issues'].append(f"Corrupted JSON in {data_file.name}")
            
            # Check for backup files
            backup_files = len(list(self.data_directory.parent.glob('backup/*.tar.gz')))
            check_result['details']['backup_files'] = backup_files
            
            if backup_files == 0:
                check_result['issues'].append("No backup files found")
            
        except Exception as e:
            check_result['status'] = 'error'
            check_result['issues'].append(f"Data integrity check failed: {e}")
        
        return check_result
    
    def _analyze_security_logs(self) -> dict:
        """Analyze security logs for suspicious activity."""
        check_result = {
            'status': 'pass',
            'details': {},
            'issues': []
        }
        
        try:
            security_log = self.log_directory / 'security.log'
            if not security_log.exists():
                check_result['issues'].append("Security log file not found")
                return check_result
            
            # Count security events in last 24 hours
            recent_events = 0
            failed_events = 0
            
            with open(security_log, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        event_time = datetime.fromisoformat(log_entry['timestamp'])
                        
                        if (datetime.utcnow() - event_time).total_seconds() < 86400:  # 24 hours
                            recent_events += 1
                            
                            if not log_entry.get('success', True):
                                failed_events += 1
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            check_result['details']['recent_events'] = recent_events
            check_result['details']['failed_events'] = failed_events
            
            # Flag suspicious activity
            if failed_events > 10:
                check_result['status'] = 'warning'
                check_result['issues'].append(f"High number of failed security events: {failed_events}")
            
        except Exception as e:
            check_result['status'] = 'error'
            check_result['issues'].append(f"Security log analysis failed: {e}")
        
        return check_result
    
    def _generate_security_recommendations(self, checks: dict) -> list:
        """Generate security recommendations based on health check results."""
        recommendations = []
        
        # File permissions recommendations
        if checks['file_permissions']['status'] == 'fail':
            recommendations.append({
                'priority': 'high',
                'category': 'file_security',
                'title': 'Fix File Permissions',
                'description': 'Some data files have insecure permissions that allow other users to access them.',
                'action': 'Run permission repair tool or reinstall application'
            })
        
        # Data integrity recommendations
        if checks['data_integrity']['status'] == 'fail':
            recommendations.append({
                'priority': 'critical',
                'category': 'data_integrity',
                'title': 'Repair Corrupted Data',
                'description': 'Some data files are corrupted and may cause data loss.',
                'action': 'Restore from backup or repair data files'
            })
        
        # Backup recommendations
        if checks['data_integrity']['details'].get('backup_files', 0) == 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'backup',
                'title': 'Create Data Backup',
                'description': 'No backup files found. Regular backups protect against data loss.',
                'action': 'Enable automatic backups in settings'
            })
        
        return recommendations
```

---

## 🎯 Security Implementation Timeline

### **Security Implementation Phases**

#### **Phase 1: Foundation Security (Week 1)**
- [ ] Implement secure file operations and permissions
- [ ] Set up input validation framework
- [ ] Create basic error handling with security awareness
- [ ] Establish security logging infrastructure

#### **Phase 2: Data Protection (Week 2)**
- [ ] Implement data sanitization and validation
- [ ] Create secure backup system
- [ ] Set up file system security measures
- [ ] Implement security audit trail

#### **Phase 3: Advanced Security (Week 3-4)**
- [ ] Add rate limiting and abuse prevention
- [ ] Implement security health monitoring
- [ ] Create update verification system
- [ ] Complete cross-platform security testing

#### **Phase 4: Security Validation (Week 5-6)**
- [ ] Conduct security penetration testing
- [ ] Perform vulnerability assessment
- [ ] Validate all security controls
- [ ] Document security procedures

---

*This security model provides comprehensive protection for Tick-Tock Widget v0.1.0, ensuring user data privacy, system integrity, and application security across all supported platforms.*
