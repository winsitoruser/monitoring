"""
Connection Tester Utility.
Provides functionality for testing connections to exchanges, bots, and servers.
"""
import logging
import time
import requests
from typing import Dict, Any, Optional, Tuple
import socket
import paramiko
import ccxt
from datetime import datetime

logger = logging.getLogger("utils.connection_tester")

class ConnectionTester:
    """
    Utility class for testing various connection types.
    Supports exchanges, bots, and servers using different protocols.
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the connection tester.
        
        Args:
            timeout: Default timeout for connection attempts in seconds
        """
        self.timeout = timeout
    
    def test_exchange_connection(self, 
                               exchange_name: str, 
                               api_key: str, 
                               secret_key: str, 
                               additional_params: Optional[Dict[str, str]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Test connection to a cryptocurrency exchange using CCXT.
        
        Args:
            exchange_name: Name of the exchange (must be supported by CCXT)
            api_key: API key for the exchange
            secret_key: Secret key for the exchange
            additional_params: Additional parameters required by specific exchanges
            
        Returns:
            Tuple containing (success: bool, message: str, details: dict)
        """
        try:
            # Check if exchange is supported by CCXT
            if exchange_name not in ccxt.exchanges:
                return False, f"Exchange '{exchange_name}' is not supported", {
                    "supported_exchanges": ccxt.exchanges[:10]  # Show first 10 for brevity
                }
            
            # Initialize exchange
            exchange_class = getattr(ccxt, exchange_name)
            
            # Prepare parameters
            params = {
                'apiKey': api_key,
                'secret': secret_key,
                'timeout': self.timeout * 1000,  # CCXT uses milliseconds
                'enableRateLimit': True
            }
            
            # Add additional parameters if provided
            if additional_params:
                for key, value in additional_params.items():
                    params[key] = value
            
            exchange = exchange_class(params)
            
            # Test connection by fetching account balance
            start_time = time.time()
            balance = exchange.fetch_balance()
            response_time = time.time() - start_time
            
            # Verify if we got a valid response
            if balance and 'total' in balance:
                # Don't return actual balance values for security
                return True, f"Successfully connected to {exchange_name}", {
                    "response_time_ms": round(response_time * 1000, 2),
                    "rate_limit_remaining": exchange.last_response_headers.get('ratelimit-remaining', 'N/A'),
                    "has_public_api_access": True,
                    "has_private_api_access": True
                }
            else:
                return False, f"Connection to {exchange_name} succeeded but could not fetch balance", {
                    "response_time_ms": round(response_time * 1000, 2)
                }
                
        except ccxt.AuthenticationError as e:
            return False, f"Authentication failed: {str(e)}", {
                "error_type": "authentication_error",
                "exchange": exchange_name
            }
        except ccxt.ExchangeError as e:
            return False, f"Exchange error: {str(e)}", {
                "error_type": "exchange_error",
                "exchange": exchange_name
            }
        except ccxt.NetworkError as e:
            return False, f"Network error: {str(e)}", {
                "error_type": "network_error",
                "exchange": exchange_name
            }
        except Exception as e:
            logger.error(f"Error testing exchange connection to {exchange_name}: {e}")
            return False, f"Error testing connection: {str(e)}", {
                "error_type": "unknown_error",
                "exchange": exchange_name
            }
    
    def test_bot_connection(self, 
                          api_endpoint: str, 
                          api_token: Optional[str] = None, 
                          health_endpoint: str = "/health") -> Tuple[bool, str, Dict[str, Any]]:
        """
        Test connection to a bot API.
        
        Args:
            api_endpoint: Base URL of the bot API
            api_token: Authentication token for the API
            health_endpoint: Health check endpoint path
            
        Returns:
            Tuple containing (success: bool, message: str, details: dict)
        """
        try:
            # Format the full URL
            if not api_endpoint.endswith('/') and not health_endpoint.startswith('/'):
                health_endpoint = '/' + health_endpoint
            
            url = api_endpoint.rstrip('/') + health_endpoint
            
            # Prepare headers
            headers = {}
            if api_token:
                headers['Authorization'] = f'Bearer {api_token}'
            
            # Make the request
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            # Check response
            if response.status_code < 400:
                details = {
                    "response_time_ms": round(response_time * 1000, 2),
                    "status_code": response.status_code,
                    "content_type": response.headers.get('Content-Type', 'unknown')
                }
                
                try:
                    # Try to parse JSON response
                    json_data = response.json()
                    if isinstance(json_data, dict):
                        # Include relevant health information if available
                        for key in ['status', 'version', 'uptime']:
                            if key in json_data:
                                details[key] = json_data[key]
                except:
                    pass
                
                return True, "Successfully connected to bot API", details
            else:
                return False, f"Bot API responded with status code {response.status_code}", {
                    "response_time_ms": round(response_time * 1000, 2),
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            return False, "Connection timed out", {
                "error_type": "timeout",
                "timeout_seconds": self.timeout
            }
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error: {str(e)}", {
                "error_type": "connection_error"
            }
        except Exception as e:
            logger.error(f"Error testing bot connection to {api_endpoint}: {e}")
            return False, f"Error testing connection: {str(e)}", {
                "error_type": "unknown_error"
            }
    
    def test_server_connection(self, 
                             hostname: str, 
                             port: Optional[int] = None, 
                             protocol: str = "http", 
                             health_endpoint: Optional[str] = None,
                             auth_token: Optional[str] = None,
                             ssh_key: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Test connection to a server using various protocols.
        
        Args:
            hostname: Server hostname or IP
            port: Server port (optional, protocol-dependent)
            protocol: Protocol to use (http, https, tcp, ping, ssh)
            health_endpoint: Health check endpoint for HTTP/HTTPS
            auth_token: Authentication token for HTTP/HTTPS
            ssh_key: SSH key for SSH protocol
            
        Returns:
            Tuple containing (success: bool, message: str, details: dict)
        """
        protocol = protocol.lower()
        
        # HTTP/HTTPS protocol
        if protocol in ["http", "https"]:
            return self._test_http_connection(
                hostname, port, protocol, health_endpoint, auth_token
            )
        
        # TCP protocol
        elif protocol == "tcp":
            return self._test_tcp_connection(hostname, port or 80)
        
        # PING protocol
        elif protocol == "ping":
            return self._test_ping(hostname)
        
        # SSH protocol
        elif protocol == "ssh":
            return self._test_ssh_connection(hostname, port or 22, ssh_key)
        
        # Unsupported protocol
        else:
            return False, f"Unsupported protocol: {protocol}", {
                "supported_protocols": ["http", "https", "tcp", "ping", "ssh"]
            }
    
    def _test_http_connection(self, 
                            hostname: str, 
                            port: Optional[int], 
                            protocol: str, 
                            health_endpoint: Optional[str],
                            auth_token: Optional[str]) -> Tuple[bool, str, Dict[str, Any]]:
        """Test HTTP/HTTPS connection to a server."""
        try:
            # Format the URL
            port_str = f":{port}" if port else ""
            url = f"{protocol}://{hostname}{port_str}"
            
            if health_endpoint:
                if not health_endpoint.startswith('/'):
                    health_endpoint = '/' + health_endpoint
                url += health_endpoint
            
            # Prepare headers
            headers = {}
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            # Make the request
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            # Check response
            if response.status_code < 400:
                return True, f"Successfully connected to {url}", {
                    "response_time_ms": round(response_time * 1000, 2),
                    "status_code": response.status_code,
                    "content_type": response.headers.get('Content-Type', 'unknown'),
                    "server": response.headers.get('Server', 'unknown')
                }
            else:
                return False, f"Server responded with status code {response.status_code}", {
                    "response_time_ms": round(response_time * 1000, 2),
                    "status_code": response.status_code
                }
                
        except requests.exceptions.SSLError as e:
            return False, f"SSL error: {str(e)}", {
                "error_type": "ssl_error"
            }
        except requests.exceptions.Timeout:
            return False, "Connection timed out", {
                "error_type": "timeout",
                "timeout_seconds": self.timeout
            }
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error: {str(e)}", {
                "error_type": "connection_error"
            }
        except Exception as e:
            logger.error(f"Error testing HTTP connection to {hostname}: {e}")
            return False, f"Error testing connection: {str(e)}", {
                "error_type": "unknown_error"
            }
    
    def _test_tcp_connection(self, hostname: str, port: int) -> Tuple[bool, str, Dict[str, Any]]:
        """Test TCP connection to a server."""
        try:
            start_time = time.time()
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Connect to server
            sock.connect((hostname, port))
            response_time = time.time() - start_time
            
            # Close socket
            sock.close()
            
            return True, f"Successfully connected to {hostname}:{port} via TCP", {
                "response_time_ms": round(response_time * 1000, 2),
                "port": port
            }
            
        except socket.timeout:
            return False, "Connection timed out", {
                "error_type": "timeout",
                "timeout_seconds": self.timeout
            }
        except socket.error as e:
            return False, f"Socket error: {str(e)}", {
                "error_type": "socket_error"
            }
        except Exception as e:
            logger.error(f"Error testing TCP connection to {hostname}:{port}: {e}")
            return False, f"Error testing connection: {str(e)}", {
                "error_type": "unknown_error"
            }
    
    def _test_ping(self, hostname: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Test ping to a server."""
        import platform
        import subprocess
        
        try:
            # Determine ping command based on platform
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', hostname]
            
            # Execute ping command
            start_time = time.time()
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=self.timeout)
            response_time = time.time() - start_time
            
            # Check if ping was successful
            if process.returncode == 0:
                output = stdout.decode('utf-8', errors='ignore')
                
                # Try to extract ping time
                ping_time = None
                if "time=" in output:
                    try:
                        time_part = output.split("time=")[1].split(" ")[0]
                        ping_time = float(time_part.replace("ms", ""))
                    except:
                        pass
                
                return True, f"Successfully pinged {hostname}", {
                    "response_time_ms": round(response_time * 1000, 2),
                    "ping_time_ms": ping_time
                }
            else:
                output = stderr.decode('utf-8', errors='ignore')
                return False, f"Ping failed with return code {process.returncode}", {
                    "response_time_ms": round(response_time * 1000, 2),
                    "error_output": output[:200]  # Limit error output length
                }
                
        except subprocess.TimeoutExpired:
            return False, "Ping timed out", {
                "error_type": "timeout",
                "timeout_seconds": self.timeout
            }
        except Exception as e:
            logger.error(f"Error pinging {hostname}: {e}")
            return False, f"Error pinging host: {str(e)}", {
                "error_type": "unknown_error"
            }
    
    def _test_ssh_connection(self, hostname: str, port: int, ssh_key: Optional[str]) -> Tuple[bool, str, Dict[str, Any]]:
        """Test SSH connection to a server."""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Prepare authentication
            auth_args = {}
            if ssh_key:
                from io import StringIO
                key_file = StringIO(ssh_key)
                private_key = paramiko.RSAKey.from_private_key(key_file)
                auth_args['pkey'] = private_key
            
            # Connect to server
            start_time = time.time()
            client.connect(hostname, port=port, timeout=self.timeout, **auth_args)
            response_time = time.time() - start_time
            
            # Execute simple command to verify connection
            stdin, stdout, stderr = client.exec_command('echo "Connection test successful"')
            exit_status = stdout.channel.recv_exit_status()
            
            # Close connection
            client.close()
            
            if exit_status == 0:
                return True, f"Successfully connected to {hostname}:{port} via SSH", {
                    "response_time_ms": round(response_time * 1000, 2),
                    "authentication_method": "key" if ssh_key else "password"
                }
            else:
                stderr_output = stderr.read().decode('utf-8')
                return False, f"SSH connection succeeded but command failed: {stderr_output}", {
                    "response_time_ms": round(response_time * 1000, 2),
                    "exit_status": exit_status
                }
                
        except paramiko.AuthenticationException as e:
            return False, f"SSH authentication failed: {str(e)}", {
                "error_type": "authentication_error"
            }
        except paramiko.SSHException as e:
            return False, f"SSH error: {str(e)}", {
                "error_type": "ssh_error"
            }
        except socket.timeout:
            return False, "SSH connection timed out", {
                "error_type": "timeout",
                "timeout_seconds": self.timeout
            }
        except Exception as e:
            logger.error(f"Error testing SSH connection to {hostname}:{port}: {e}")
            return False, f"Error testing SSH connection: {str(e)}", {
                "error_type": "unknown_error"
            }
