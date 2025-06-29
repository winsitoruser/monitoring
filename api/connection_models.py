"""
Models for connection settings management.
Provides Pydantic models for exchange, bot and server connections 
with validation and secure field handling.
"""
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator, AnyHttpUrl, root_validator
import re
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Generate or load encryption key
def get_encryption_key():
    """Get or generate encryption key for sensitive data"""
    key_file = os.path.join("data", "secure", "connection_key.key")
    os.makedirs(os.path.dirname(key_file), exist_ok=True)
    
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        # Generate a new key
        salt = os.urandom(16)
        password = os.urandom(32)  # This is just a random value for key derivation
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Save the key
        with open(key_file, "wb") as f:
            f.write(key)
        
        # Save salt and password hash for potential recovery
        with open(os.path.join("data", "secure", "connection_salt.bin"), "wb") as f:
            f.write(salt)
            
        return key

# Initialize encryption
ENCRYPTION_KEY = get_encryption_key()
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_value(value: str) -> str:
    """Encrypt a sensitive value"""
    if not value:
        return ""
    return cipher.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a sensitive value"""
    if not encrypted_value:
        return ""
    try:
        return cipher.decrypt(encrypted_value.encode()).decode()
    except:
        return "[DECRYPTION_ERROR]"

# Base models
class ConnectionBase(BaseModel):
    """Base model for all connections with common fields"""
    id: Optional[str] = Field(None, description="Unique identifier")
    name: str = Field(..., description="Connection name")
    description: Optional[str] = Field("", description="Description of this connection")
    isActive: bool = Field(True, description="Whether this connection is active")
    lastTested: Optional[str] = Field(None, description="Timestamp of last connection test")
    connectionStatus: Optional[bool] = Field(None, description="Result of last connection test")
    lastError: Optional[str] = Field(None, description="Last error message")

# Exchange Connection models
class ExchangeConnectionBase(ConnectionBase):
    """Base model for exchange connection settings"""
    exchangeName: str = Field(..., description="Name of the exchange")
    apiKey: str = Field(..., description="API Key for the exchange")
    secretKey: str = Field(..., description="Secret Key for the exchange")
    additionalParams: Optional[Dict[str, str]] = Field({}, description="Additional parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Binance Main Account",
                "description": "Main trading account on Binance",
                "exchangeName": "binance",
                "apiKey": "your-api-key",
                "secretKey": "your-secret-key",
                "additionalParams": {
                    "passphrase": "optional-passphrase"
                },
                "isActive": True
            }
        }

class ExchangeConnectionCreate(ExchangeConnectionBase):
    """Model for creating a new exchange connection"""
    pass

class ExchangeConnectionUpdate(BaseModel):
    """Model for updating an exchange connection"""
    name: Optional[str] = None
    description: Optional[str] = None
    exchangeName: Optional[str] = None
    apiKey: Optional[str] = None
    secretKey: Optional[str] = None
    additionalParams: Optional[Dict[str, str]] = None
    isActive: Optional[bool] = None

class ExchangeConnectionInDB(ExchangeConnectionBase):
    """Model for exchange connection stored in database with encrypted fields"""
    id: str
    apiKey: str
    secretKey: str
    additionalParams: Dict[str, str]
    
    # These fields will be encrypted when stored
    _encrypted_fields = ["apiKey", "secretKey"]
    
    class Config:
        orm_mode = True

class ExchangeConnectionResponse(ExchangeConnectionBase):
    """Model for exchange connection API response with masked sensitive fields"""
    id: str
    apiKey: str = Field(..., description="Masked API Key")
    secretKey: str = Field(..., description="Masked Secret Key")
    
    @validator('apiKey', 'secretKey')
    def mask_sensitive(cls, v):
        """Mask sensitive values in response"""
        if v and len(v) > 8:
            return v[:4] + '*' * (len(v) - 8) + v[-4:]
        elif v:
            return '*' * len(v)
        return ""

# Bot Connection models
class BotConnectionBase(ConnectionBase):
    """Base model for bot connection settings"""
    botType: str = Field(..., description="Type of bot")
    apiEndpoint: str = Field(..., description="API endpoint URL")
    apiToken: str = Field(..., description="API token for authentication")
    healthCheckEndpoint: Optional[str] = Field("/health", description="Health check endpoint")
    telegramBotToken: Optional[str] = Field(None, description="Telegram bot token if applicable")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Trading Bot Alpha",
                "description": "Main trading bot for strategy Alpha",
                "botType": "trading",
                "apiEndpoint": "https://bot-server.example.com/api",
                "apiToken": "your-api-token",
                "healthCheckEndpoint": "/health",
                "telegramBotToken": "telegram-bot-token",
                "isActive": True
            }
        }

class BotConnectionCreate(BotConnectionBase):
    """Model for creating a new bot connection"""
    pass

class BotConnectionUpdate(BaseModel):
    """Model for updating a bot connection"""
    name: Optional[str] = None
    description: Optional[str] = None
    botType: Optional[str] = None
    apiEndpoint: Optional[str] = None
    apiToken: Optional[str] = None
    healthCheckEndpoint: Optional[str] = None
    telegramBotToken: Optional[str] = None
    isActive: Optional[bool] = None

class BotConnectionInDB(BotConnectionBase):
    """Model for bot connection stored in database with encrypted fields"""
    id: str
    apiToken: str
    telegramBotToken: Optional[str]
    
    # These fields will be encrypted when stored
    _encrypted_fields = ["apiToken", "telegramBotToken"]
    
    class Config:
        orm_mode = True

class BotConnectionResponse(BotConnectionBase):
    """Model for bot connection API response with masked sensitive fields"""
    id: str
    apiToken: str = Field(..., description="Masked API Token")
    telegramBotToken: Optional[str] = Field(None, description="Masked Telegram Token")
    
    @validator('apiToken', 'telegramBotToken')
    def mask_sensitive(cls, v):
        """Mask sensitive values in response"""
        if not v:
            return v
        if len(v) > 8:
            return v[:4] + '*' * (len(v) - 8) + v[-4:]
        else:
            return '*' * len(v)

# Server Connection models
class ServerConnectionBase(ConnectionBase):
    """Base model for server connection settings"""
    serverType: str = Field(..., description="Type of server")
    hostname: str = Field(..., description="Server hostname or IP")
    port: Optional[int] = Field(None, description="Server port")
    monitoringProtocol: str = Field("http", description="Protocol for monitoring")
    healthEndpoint: Optional[str] = Field("/health", description="Health check endpoint")
    authToken: Optional[str] = Field(None, description="Authentication token if required")
    sshKey: Optional[str] = Field(None, description="SSH key for SSH monitoring")
    checkInterval: int = Field(60, description="Interval in seconds between checks")
    
    @validator('hostname')
    def validate_hostname(cls, v):
        """Validate hostname format"""
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]+)?[a-zA-Z0-9]$|^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', v):
            raise ValueError('Invalid hostname or IP address format')
        return v
    
    @validator('port')
    def validate_port(cls, v):
        """Validate port range"""
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Production API Server",
                "description": "Main production API server",
                "serverType": "api",
                "hostname": "api.example.com",
                "port": 443,
                "monitoringProtocol": "https",
                "healthEndpoint": "/health",
                "authToken": "server-auth-token",
                "checkInterval": 60,
                "isActive": True
            }
        }

class ServerConnectionCreate(ServerConnectionBase):
    """Model for creating a new server connection"""
    pass

class ServerConnectionUpdate(BaseModel):
    """Model for updating a server connection"""
    name: Optional[str] = None
    description: Optional[str] = None
    serverType: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    monitoringProtocol: Optional[str] = None
    healthEndpoint: Optional[str] = None
    authToken: Optional[str] = None
    sshKey: Optional[str] = None
    checkInterval: Optional[int] = None
    isActive: Optional[bool] = None

class ServerConnectionInDB(ServerConnectionBase):
    """Model for server connection stored in database with encrypted fields"""
    id: str
    authToken: Optional[str]
    sshKey: Optional[str]
    
    # These fields will be encrypted when stored
    _encrypted_fields = ["authToken", "sshKey"]
    
    class Config:
        orm_mode = True

class ServerConnectionResponse(ServerConnectionBase):
    """Model for server connection API response with masked sensitive fields"""
    id: str
    authToken: Optional[str] = Field(None, description="Masked Auth Token")
    sshKey: Optional[str] = Field(None, description="Masked SSH Key")
    
    @validator('authToken')
    def mask_auth_token(cls, v):
        """Mask auth token in response"""
        if not v:
            return v
        if len(v) > 8:
            return v[:4] + '*' * (len(v) - 8) + v[-4:]
        else:
            return '*' * len(v)
    
    @validator('sshKey')
    def mask_ssh_key(cls, v):
        """Mask SSH key in response"""
        if not v:
            return v
        # Only show key format and first/last few characters
        lines = v.strip().split("\n")
        if len(lines) > 2:
            return f"{lines[0]}\n{'*' * 20}\n{lines[-1]}"
        return '*' * 20

# Connection test models
class ConnectionTestRequest(BaseModel):
    """Request model for testing a connection"""
    connectionType: str = Field(..., description="Type of connection (exchange, bot, server)")
    connectionId: Optional[str] = Field(None, description="ID of existing connection to test")
    connectionData: Optional[Dict[str, Any]] = Field(None, description="Connection data for one-time test")
    
    @root_validator
    def check_required_fields(cls, values):
        """Validate that either connectionId or connectionData is provided"""
        conn_id = values.get('connectionId')
        conn_data = values.get('connectionData')
        
        if not conn_id and not conn_data:
            raise ValueError('Either connectionId or connectionData must be provided')
        
        return values

class ConnectionTestResponse(BaseModel):
    """Response model for connection test results"""
    success: bool = Field(..., description="Whether the test was successful")
    message: str = Field(..., description="Test result message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the test")
    timestamp: str = Field(..., description="Timestamp of the test")
