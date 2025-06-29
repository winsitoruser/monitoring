"""
Connection Manager for handling connection settings.
Provides secure storage and retrieval of connection settings
for exchanges, bots, and servers.
"""
import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import threading

from api.connection_models import (
    encrypt_value, decrypt_value,
    ExchangeConnectionInDB, ExchangeConnectionBase, ExchangeConnectionResponse,
    BotConnectionInDB, BotConnectionBase, BotConnectionResponse,
    ServerConnectionInDB, ServerConnectionBase, ServerConnectionResponse,
)

logger = logging.getLogger("utils.connection_manager")

class ConnectionManager:
    """
    Manager for connection settings.
    
    Features:
    - Secure storage of connection settings with encryption for sensitive fields
    - CRUD operations for exchange, bot, and server connections
    - Connection testing functionality
    """
    
    def __init__(self, storage_path="data/connections"):
        """
        Initialize the Connection Manager.
        
        Args:
            storage_path: Path where connection settings will be stored
        """
        self.storage_path = storage_path
        self.lock = threading.RLock()
        
        # Create storage directories
        os.makedirs(os.path.join(self.storage_path, "exchanges"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, "bots"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, "servers"), exist_ok=True)
        
        # Initialize connection collections
        self.exchanges: Dict[str, ExchangeConnectionInDB] = {}
        self.bots: Dict[str, BotConnectionInDB] = {}
        self.servers: Dict[str, ServerConnectionInDB] = {}
        
        # Load existing connections
        self._load_all_connections()
    
    def _load_all_connections(self):
        """Load all existing connections from storage."""
        self._load_connections("exchanges", self.exchanges, ExchangeConnectionInDB)
        self._load_connections("bots", self.bots, BotConnectionInDB)
        self._load_connections("servers", self.servers, ServerConnectionInDB)
        
        logger.info(f"Loaded {len(self.exchanges)} exchange connections, "
                   f"{len(self.bots)} bot connections, and "
                   f"{len(self.servers)} server connections")
    
    def _load_connections(self, connection_type: str, collection: Dict, model_class):
        """Load connections of a specific type from storage."""
        directory = os.path.join(self.storage_path, connection_type)
        
        try:
            for filename in os.listdir(directory):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(directory, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Decrypt sensitive fields
                for field in model_class._encrypted_fields:
                    if field in data and data[field]:
                        data[field] = decrypt_value(data[field])
                
                connection = model_class(**data)
                collection[connection.id] = connection
        except Exception as e:
            logger.error(f"Error loading {connection_type} connections: {e}")
    
    def _save_connection(self, connection_type: str, connection, model_class):
        """Save a connection to storage with encryption."""
        try:
            directory = os.path.join(self.storage_path, connection_type)
            filename = f"{connection.id}.json"
            filepath = os.path.join(directory, filename)
            
            # Convert to dict
            data = connection.dict()
            
            # Encrypt sensitive fields
            for field in model_class._encrypted_fields:
                if field in data and data[field]:
                    data[field] = encrypt_value(data[field])
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {connection_type} connection: {connection.name} ({connection.id})")
            
        except Exception as e:
            logger.error(f"Error saving {connection_type} connection: {e}")
            raise
    
    def _delete_connection(self, connection_type: str, connection_id: str) -> bool:
        """Delete a connection from storage."""
        directory = os.path.join(self.storage_path, connection_type)
        filepath = os.path.join(directory, f"{connection_id}.json")
        
        if not os.path.exists(filepath):
            return False
        
        try:
            os.remove(filepath)
            logger.info(f"Deleted {connection_type} connection: {connection_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {connection_type} connection {connection_id}: {e}")
            return False
    
    # Exchange connection methods
    def create_exchange_connection(self, connection: ExchangeConnectionBase) -> ExchangeConnectionInDB:
        """Create a new exchange connection."""
        with self.lock:
            connection_id = str(uuid.uuid4())
            
            exchange_connection = ExchangeConnectionInDB(
                id=connection_id,
                **connection.dict()
            )
            
            self.exchanges[connection_id] = exchange_connection
            self._save_connection("exchanges", exchange_connection, ExchangeConnectionInDB)
            
            return exchange_connection
    
    def get_exchange_connection(self, connection_id: str) -> Optional[ExchangeConnectionInDB]:
        """Get an exchange connection by ID."""
        return self.exchanges.get(connection_id)
    
    def get_all_exchange_connections(self) -> List[ExchangeConnectionResponse]:
        """Get all exchange connections."""
        return [
            ExchangeConnectionResponse(**conn.dict())
            for conn in self.exchanges.values()
        ]
    
    def update_exchange_connection(self, connection_id: str, updates: Dict[str, Any]) -> Optional[ExchangeConnectionInDB]:
        """Update an exchange connection."""
        with self.lock:
            if connection_id not in self.exchanges:
                return None
            
            connection = self.exchanges[connection_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(connection, key) and value is not None:
                    setattr(connection, key, value)
            
            self._save_connection("exchanges", connection, ExchangeConnectionInDB)
            
            return connection
    
    def delete_exchange_connection(self, connection_id: str) -> bool:
        """Delete an exchange connection."""
        with self.lock:
            if connection_id not in self.exchanges:
                return False
            
            del self.exchanges[connection_id]
            return self._delete_connection("exchanges", connection_id)
    
    # Bot connection methods
    def create_bot_connection(self, connection: BotConnectionBase) -> BotConnectionInDB:
        """Create a new bot connection."""
        with self.lock:
            connection_id = str(uuid.uuid4())
            
            bot_connection = BotConnectionInDB(
                id=connection_id,
                **connection.dict()
            )
            
            self.bots[connection_id] = bot_connection
            self._save_connection("bots", bot_connection, BotConnectionInDB)
            
            return bot_connection
    
    def get_bot_connection(self, connection_id: str) -> Optional[BotConnectionInDB]:
        """Get a bot connection by ID."""
        return self.bots.get(connection_id)
    
    def get_all_bot_connections(self) -> List[BotConnectionResponse]:
        """Get all bot connections."""
        return [
            BotConnectionResponse(**conn.dict())
            for conn in self.bots.values()
        ]
    
    def update_bot_connection(self, connection_id: str, updates: Dict[str, Any]) -> Optional[BotConnectionInDB]:
        """Update a bot connection."""
        with self.lock:
            if connection_id not in self.bots:
                return None
            
            connection = self.bots[connection_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(connection, key) and value is not None:
                    setattr(connection, key, value)
            
            self._save_connection("bots", connection, BotConnectionInDB)
            
            return connection
    
    def delete_bot_connection(self, connection_id: str) -> bool:
        """Delete a bot connection."""
        with self.lock:
            if connection_id not in self.bots:
                return False
            
            del self.bots[connection_id]
            return self._delete_connection("bots", connection_id)
    
    # Server connection methods
    def create_server_connection(self, connection: ServerConnectionBase) -> ServerConnectionInDB:
        """Create a new server connection."""
        with self.lock:
            connection_id = str(uuid.uuid4())
            
            server_connection = ServerConnectionInDB(
                id=connection_id,
                **connection.dict()
            )
            
            self.servers[connection_id] = server_connection
            self._save_connection("servers", server_connection, ServerConnectionInDB)
            
            return server_connection
    
    def get_server_connection(self, connection_id: str) -> Optional[ServerConnectionInDB]:
        """Get a server connection by ID."""
        return self.servers.get(connection_id)
    
    def get_all_server_connections(self) -> List[ServerConnectionResponse]:
        """Get all server connections."""
        return [
            ServerConnectionResponse(**conn.dict())
            for conn in self.servers.values()
        ]
    
    def update_server_connection(self, connection_id: str, updates: Dict[str, Any]) -> Optional[ServerConnectionInDB]:
        """Update a server connection."""
        with self.lock:
            if connection_id not in self.servers:
                return None
            
            connection = self.servers[connection_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(connection, key) and value is not None:
                    setattr(connection, key, value)
            
            self._save_connection("servers", connection, ServerConnectionInDB)
            
            return connection
    
    def delete_server_connection(self, connection_id: str) -> bool:
        """Delete a server connection."""
        with self.lock:
            if connection_id not in self.servers:
                return False
            
            del self.servers[connection_id]
            return self._delete_connection("servers", connection_id)
