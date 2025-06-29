"""
Connection Settings API.
Provides REST API endpoints for managing connection settings for exchanges, bots, and servers.
"""
import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Body, Query, status, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime

from api.connection_models import (
    ExchangeConnectionBase, ExchangeConnectionCreate, ExchangeConnectionUpdate, ExchangeConnectionResponse,
    BotConnectionBase, BotConnectionCreate, BotConnectionUpdate, BotConnectionResponse,
    ServerConnectionBase, ServerConnectionCreate, ServerConnectionUpdate, ServerConnectionResponse,
    ConnectionTestRequest, ConnectionTestResponse
)
from utils.connection_manager import ConnectionManager
from utils.connection_tester import ConnectionTester

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("connection_api")

# Create the router
router = APIRouter(
    prefix="/connections",
    tags=["connections"],
    responses={404: {"description": "Not found"}},
)

# Initialize managers
connection_manager = ConnectionManager()
connection_tester = ConnectionTester()

# Auth key for API security
API_KEY = os.environ.get("CONFIG_API_KEY", "change_me_in_production")

# Dependency for API key verification
async def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key

# Exchange Connection Routes
@router.get("/exchanges", response_model=List[ExchangeConnectionResponse])
async def get_all_exchange_connections(api_key: str = Depends(verify_api_key)):
    """Get all exchange connections"""
    try:
        connections = connection_manager.get_all_exchange_connections()
        return connections
    except Exception as e:
        logger.error(f"Error retrieving exchange connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve exchange connections: {str(e)}")

@router.post("/exchanges", response_model=ExchangeConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_exchange_connection(
    connection: ExchangeConnectionCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new exchange connection"""
    try:
        new_connection = connection_manager.create_exchange_connection(connection)
        return ExchangeConnectionResponse(**new_connection.dict())
    except Exception as e:
        logger.error(f"Error creating exchange connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create exchange connection: {str(e)}")

@router.get("/exchanges/{connection_id}", response_model=ExchangeConnectionResponse)
async def get_exchange_connection(
    connection_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get exchange connection by ID"""
    connection = connection_manager.get_exchange_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Exchange connection not found")
    
    return ExchangeConnectionResponse(**connection.dict())

@router.put("/exchanges/{connection_id}", response_model=ExchangeConnectionResponse)
async def update_exchange_connection(
    connection_id: str,
    updates: ExchangeConnectionUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update an exchange connection"""
    try:
        # Convert updates to dict, excluding None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        # Update the connection
        updated_connection = connection_manager.update_exchange_connection(connection_id, update_data)
        if not updated_connection:
            raise HTTPException(status_code=404, detail="Exchange connection not found")
        
        return ExchangeConnectionResponse(**updated_connection.dict())
    except Exception as e:
        logger.error(f"Error updating exchange connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update exchange connection: {str(e)}")

@router.delete("/exchanges/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange_connection(
    connection_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete an exchange connection"""
    success = connection_manager.delete_exchange_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exchange connection not found")
    
    return None

# Bot Connection Routes
@router.get("/bots", response_model=List[BotConnectionResponse])
async def get_all_bot_connections(api_key: str = Depends(verify_api_key)):
    """Get all bot connections"""
    try:
        connections = connection_manager.get_all_bot_connections()
        return connections
    except Exception as e:
        logger.error(f"Error retrieving bot connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bot connections: {str(e)}")

@router.post("/bots", response_model=BotConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_bot_connection(
    connection: BotConnectionCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new bot connection"""
    try:
        new_connection = connection_manager.create_bot_connection(connection)
        return BotConnectionResponse(**new_connection.dict())
    except Exception as e:
        logger.error(f"Error creating bot connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create bot connection: {str(e)}")

@router.get("/bots/{connection_id}", response_model=BotConnectionResponse)
async def get_bot_connection(
    connection_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get bot connection by ID"""
    connection = connection_manager.get_bot_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Bot connection not found")
    
    return BotConnectionResponse(**connection.dict())

@router.put("/bots/{connection_id}", response_model=BotConnectionResponse)
async def update_bot_connection(
    connection_id: str,
    updates: BotConnectionUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update a bot connection"""
    try:
        # Convert updates to dict, excluding None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        # Update the connection
        updated_connection = connection_manager.update_bot_connection(connection_id, update_data)
        if not updated_connection:
            raise HTTPException(status_code=404, detail="Bot connection not found")
        
        return BotConnectionResponse(**updated_connection.dict())
    except Exception as e:
        logger.error(f"Error updating bot connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update bot connection: {str(e)}")

@router.delete("/bots/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot_connection(
    connection_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a bot connection"""
    success = connection_manager.delete_bot_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bot connection not found")
    
    return None

# Server Connection Routes
@router.get("/servers", response_model=List[ServerConnectionResponse])
async def get_all_server_connections(api_key: str = Depends(verify_api_key)):
    """Get all server connections"""
    try:
        connections = connection_manager.get_all_server_connections()
        return connections
    except Exception as e:
        logger.error(f"Error retrieving server connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve server connections: {str(e)}")

@router.post("/servers", response_model=ServerConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_server_connection(
    connection: ServerConnectionCreate,
    api_key: str = Depends(verify_api_key)
):
    """Create a new server connection"""
    try:
        new_connection = connection_manager.create_server_connection(connection)
        return ServerConnectionResponse(**new_connection.dict())
    except Exception as e:
        logger.error(f"Error creating server connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create server connection: {str(e)}")

@router.get("/servers/{connection_id}", response_model=ServerConnectionResponse)
async def get_server_connection(
    connection_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get server connection by ID"""
    connection = connection_manager.get_server_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Server connection not found")
    
    return ServerConnectionResponse(**connection.dict())

@router.put("/servers/{connection_id}", response_model=ServerConnectionResponse)
async def update_server_connection(
    connection_id: str,
    updates: ServerConnectionUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update a server connection"""
    try:
        # Convert updates to dict, excluding None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        # Update the connection
        updated_connection = connection_manager.update_server_connection(connection_id, update_data)
        if not updated_connection:
            raise HTTPException(status_code=404, detail="Server connection not found")
        
        return ServerConnectionResponse(**updated_connection.dict())
    except Exception as e:
        logger.error(f"Error updating server connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update server connection: {str(e)}")

@router.delete("/servers/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server_connection(
    connection_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a server connection"""
    success = connection_manager.delete_server_connection(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Server connection not found")
    
    return None

# Connection Testing Routes
@router.post("/test/exchange", response_model=ConnectionTestResponse)
async def test_exchange_connection(
    request: ConnectionTestRequest,
    api_key: str = Depends(verify_api_key)
):
    """Test an exchange connection"""
    try:
        # Check if connectionType is correct
        if request.connectionType != "exchange":
            raise HTTPException(
                status_code=400, 
                detail="Invalid connection type. Expected 'exchange'"
            )
        
        # Test existing connection or one-time connection data
        if request.connectionId:
            # Get existing connection
            connection = connection_manager.get_exchange_connection(request.connectionId)
            if not connection:
                raise HTTPException(status_code=404, detail="Exchange connection not found")
            
            # Test connection
            success, message, details = connection_tester.test_exchange_connection(
                connection.exchangeName,
                connection.apiKey,
                connection.secretKey,
                connection.additionalParams
            )
            
            # Update connection status
            connection_manager.update_exchange_connection(
                request.connectionId,
                {
                    "lastTested": datetime.now().isoformat(),
                    "connectionStatus": success,
                    "lastError": None if success else message
                }
            )
        elif request.connectionData:
            # Test one-time connection data
            data = request.connectionData
            
            if not all(k in data for k in ["exchangeName", "apiKey", "secretKey"]):
                raise HTTPException(
                    status_code=400, 
                    detail="Missing required connection data fields"
                )
            
            # Test connection
            success, message, details = connection_tester.test_exchange_connection(
                data["exchangeName"],
                data["apiKey"],
                data["secretKey"],
                data.get("additionalParams")
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Either connectionId or connectionData must be provided"
            )
        
        # Return test results
        return ConnectionTestResponse(
            success=success,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing exchange connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test exchange connection: {str(e)}")

@router.post("/test/bot", response_model=ConnectionTestResponse)
async def test_bot_connection(
    request: ConnectionTestRequest,
    api_key: str = Depends(verify_api_key)
):
    """Test a bot connection"""
    try:
        # Check if connectionType is correct
        if request.connectionType != "bot":
            raise HTTPException(
                status_code=400, 
                detail="Invalid connection type. Expected 'bot'"
            )
        
        # Test existing connection or one-time connection data
        if request.connectionId:
            # Get existing connection
            connection = connection_manager.get_bot_connection(request.connectionId)
            if not connection:
                raise HTTPException(status_code=404, detail="Bot connection not found")
            
            # Test connection
            success, message, details = connection_tester.test_bot_connection(
                connection.apiEndpoint,
                connection.apiToken,
                connection.healthCheckEndpoint
            )
            
            # Update connection status
            connection_manager.update_bot_connection(
                request.connectionId,
                {
                    "lastTested": datetime.now().isoformat(),
                    "connectionStatus": success,
                    "lastError": None if success else message
                }
            )
        elif request.connectionData:
            # Test one-time connection data
            data = request.connectionData
            
            if "apiEndpoint" not in data:
                raise HTTPException(
                    status_code=400, 
                    detail="Missing required connection data field: apiEndpoint"
                )
            
            # Test connection
            success, message, details = connection_tester.test_bot_connection(
                data["apiEndpoint"],
                data.get("apiToken"),
                data.get("healthCheckEndpoint", "/health")
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Either connectionId or connectionData must be provided"
            )
        
        # Return test results
        return ConnectionTestResponse(
            success=success,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing bot connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test bot connection: {str(e)}")

@router.post("/test/server", response_model=ConnectionTestResponse)
async def test_server_connection(
    request: ConnectionTestRequest,
    api_key: str = Depends(verify_api_key)
):
    """Test a server connection"""
    try:
        # Check if connectionType is correct
        if request.connectionType != "server":
            raise HTTPException(
                status_code=400, 
                detail="Invalid connection type. Expected 'server'"
            )
        
        # Test existing connection or one-time connection data
        if request.connectionId:
            # Get existing connection
            connection = connection_manager.get_server_connection(request.connectionId)
            if not connection:
                raise HTTPException(status_code=404, detail="Server connection not found")
            
            # Test connection
            success, message, details = connection_tester.test_server_connection(
                connection.hostname,
                connection.port,
                connection.monitoringProtocol,
                connection.healthEndpoint,
                connection.authToken,
                connection.sshKey
            )
            
            # Update connection status
            connection_manager.update_server_connection(
                request.connectionId,
                {
                    "lastTested": datetime.now().isoformat(),
                    "connectionStatus": success,
                    "lastError": None if success else message
                }
            )
        elif request.connectionData:
            # Test one-time connection data
            data = request.connectionData
            
            if "hostname" not in data:
                raise HTTPException(
                    status_code=400, 
                    detail="Missing required connection data field: hostname"
                )
            
            # Test connection
            success, message, details = connection_tester.test_server_connection(
                data["hostname"],
                data.get("port"),
                data.get("monitoringProtocol", "http"),
                data.get("healthEndpoint"),
                data.get("authToken"),
                data.get("sshKey")
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Either connectionId or connectionData must be provided"
            )
        
        # Return test results
        return ConnectionTestResponse(
            success=success,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing server connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test server connection: {str(e)}")
