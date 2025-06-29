"""
Remote access monitoring and management module.
Provides tools for remote troubleshooting via SSH, VPN, AnyDesk, TeamViewer, 
and container management via Portainer or Rancher.
"""
import logging
import subprocess
import os
import re
import json
import socket
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("monitoring.remote_access")

class RemoteAccessManager:
    """
    Manages remote access tools and configurations for troubleshooting.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the remote access manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.hostname = socket.gethostname()
    
    def check_ssh_status(self) -> Dict[str, Any]:
        """
        Check if SSH service is running and accessible.
        
        Returns:
            Dictionary with SSH service status
        """
        try:
            # Check if sshd is running
            result = subprocess.run(
                ["pgrep", "sshd"],
                capture_output=True,
                text=True,
                check=False
            )
            
            is_running = result.returncode == 0
            
            if is_running:
                # Get listening port
                port_result = subprocess.run(
                    ["netstat", "-tuln", "|", "grep", "ssh"],
                    capture_output=True,
                    text=True,
                    shell=True,
                    check=False
                )
                
                port_match = re.search(r':(\d+)', port_result.stdout)
                ssh_port = port_match.group(1) if port_match else "22"
                
                # Get external IP
                ip_result = subprocess.run(
                    ["curl", "-s", "https://api.ipify.org"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                external_ip = ip_result.stdout.strip() if ip_result.returncode == 0 else "Unknown"
                
                return {
                    "service": "SSH",
                    "status": "running",
                    "port": ssh_port,
                    "host": self.hostname,
                    "external_ip": external_ip
                }
            else:
                return {
                    "service": "SSH",
                    "status": "not_running",
                    "host": self.hostname
                }
        
        except Exception as e:
            logger.error(f"Error checking SSH status: {e}")
            return {
                "service": "SSH",
                "status": "error",
                "error": str(e),
                "host": self.hostname
            }
    
    def check_vpn_status(self, vpn_type: str = "openvpn") -> Dict[str, Any]:
        """
        Check if VPN service is running.
        
        Args:
            vpn_type: Type of VPN service (openvpn, wireguard, etc.)
            
        Returns:
            Dictionary with VPN service status
        """
        try:
            if vpn_type.lower() == "openvpn":
                result = subprocess.run(
                    ["pgrep", "openvpn"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                is_running = result.returncode == 0
                
                # Get connection info if running
                if is_running:
                    # Check for active tun/tap interfaces
                    interfaces_result = subprocess.run(
                        ["ip", "addr", "show", "type", "tun"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    return {
                        "service": "OpenVPN",
                        "status": "running",
                        "interfaces": interfaces_result.stdout.strip() if interfaces_result.returncode == 0 else "Unknown",
                        "host": self.hostname
                    }
                else:
                    return {
                        "service": "OpenVPN",
                        "status": "not_running",
                        "host": self.hostname
                    }
            
            elif vpn_type.lower() == "wireguard":
                result = subprocess.run(
                    ["wg", "show"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                is_running = result.returncode == 0 and result.stdout.strip() != ""
                
                if is_running:
                    return {
                        "service": "WireGuard",
                        "status": "running",
                        "interfaces": result.stdout.strip(),
                        "host": self.hostname
                    }
                else:
                    return {
                        "service": "WireGuard",
                        "status": "not_running",
                        "host": self.hostname
                    }
            
            elif vpn_type.lower() == "tailscale":
                result = subprocess.run(
                    ["tailscale", "status"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                is_running = result.returncode == 0 and "Tailscale is running" in result.stdout
                
                if is_running:
                    return {
                        "service": "Tailscale",
                        "status": "running",
                        "details": result.stdout.strip(),
                        "host": self.hostname
                    }
                else:
                    return {
                        "service": "Tailscale",
                        "status": "not_running",
                        "host": self.hostname
                    }
            
            else:
                return {
                    "service": vpn_type,
                    "status": "unknown",
                    "error": "Unsupported VPN type",
                    "host": self.hostname
                }
        
        except Exception as e:
            logger.error(f"Error checking VPN status: {e}")
            return {
                "service": vpn_type,
                "status": "error",
                "error": str(e),
                "host": self.hostname
            }
    
    def check_remote_desktop_status(self, tool: str) -> Dict[str, Any]:
        """
        Check if remote desktop tool is running.
        
        Args:
            tool: Remote desktop tool name (anydesk, teamviewer, etc.)
            
        Returns:
            Dictionary with service status
        """
        try:
            if tool.lower() == "anydesk":
                result = subprocess.run(
                    ["pgrep", "anydesk"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                is_running = result.returncode == 0
                
                if is_running:
                    # Try to get AnyDesk ID
                    id_result = subprocess.run(
                        ["anydesk", "--get-id"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    anydesk_id = id_result.stdout.strip() if id_result.returncode == 0 else "Unknown"
                    
                    return {
                        "service": "AnyDesk",
                        "status": "running",
                        "id": anydesk_id,
                        "host": self.hostname
                    }
                else:
                    return {
                        "service": "AnyDesk",
                        "status": "not_running",
                        "host": self.hostname
                    }
            
            elif tool.lower() == "teamviewer":
                result = subprocess.run(
                    ["pgrep", "teamviewer"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                is_running = result.returncode == 0
                
                if is_running:
                    # Try to get TeamViewer ID
                    id_result = subprocess.run(
                        ["teamviewer", "--info"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    teamviewer_id_match = re.search(r'TeamViewer ID:\s+(\d+)', id_result.stdout)
                    teamviewer_id = teamviewer_id_match.group(1) if teamviewer_id_match else "Unknown"
                    
                    return {
                        "service": "TeamViewer",
                        "status": "running",
                        "id": teamviewer_id,
                        "host": self.hostname
                    }
                else:
                    return {
                        "service": "TeamViewer",
                        "status": "not_running",
                        "host": self.hostname
                    }
            
            else:
                return {
                    "service": tool,
                    "status": "unknown",
                    "error": "Unsupported remote desktop tool",
                    "host": self.hostname
                }
        
        except Exception as e:
            logger.error(f"Error checking remote desktop status: {e}")
            return {
                "service": tool,
                "status": "error",
                "error": str(e),
                "host": self.hostname
            }
    
    def check_docker_status(self) -> Dict[str, Any]:
        """
        Check if Docker is running and get container status.
        
        Returns:
            Dictionary with Docker service status
        """
        try:
            # Check if Docker daemon is running
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                check=False
            )
            
            is_running = result.returncode == 0
            
            if is_running:
                # Get container count
                containers_result = subprocess.run(
                    ["docker", "ps", "-q"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                container_count = len(containers_result.stdout.strip().split('\n')) if containers_result.stdout.strip() else 0
                
                # Get Docker version
                version_result = subprocess.run(
                    ["docker", "version", "--format", "{{.Server.Version}}"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                docker_version = version_result.stdout.strip() if version_result.returncode == 0 else "Unknown"
                
                return {
                    "service": "Docker",
                    "status": "running",
                    "version": docker_version,
                    "container_count": container_count,
                    "host": self.hostname
                }
            else:
                return {
                    "service": "Docker",
                    "status": "not_running",
                    "host": self.hostname
                }
        
        except Exception as e:
            logger.error(f"Error checking Docker status: {e}")
            return {
                "service": "Docker",
                "status": "error",
                "error": str(e),
                "host": self.hostname
            }
    
    def check_portainer_status(self) -> Dict[str, Any]:
        """
        Check if Portainer is running and accessible.
        
        Returns:
            Dictionary with Portainer service status
        """
        try:
            portainer_url = getattr(self.config, 'portainer_url', 'http://localhost:9000')
            
            response = requests.get(f"{portainer_url}/api/status", timeout=5)
            
            if response.status_code == 200:
                return {
                    "service": "Portainer",
                    "status": "running",
                    "url": portainer_url,
                    "version": response.json().get("Version", "Unknown"),
                    "host": self.hostname
                }
            else:
                return {
                    "service": "Portainer",
                    "status": "error",
                    "url": portainer_url,
                    "error": f"Status code: {response.status_code}",
                    "host": self.hostname
                }
        
        except Exception as e:
            logger.error(f"Error checking Portainer status: {e}")
            return {
                "service": "Portainer",
                "status": "error",
                "error": str(e),
                "host": self.hostname
            }
    
    def check_rancher_status(self) -> Dict[str, Any]:
        """
        Check if Rancher is running and accessible.
        
        Returns:
            Dictionary with Rancher service status
        """
        try:
            rancher_url = getattr(self.config, 'rancher_url', 'http://localhost:8080')
            
            response = requests.get(f"{rancher_url}/ping", timeout=5)
            
            if response.status_code == 200:
                return {
                    "service": "Rancher",
                    "status": "running",
                    "url": rancher_url,
                    "host": self.hostname
                }
            else:
                return {
                    "service": "Rancher",
                    "status": "error",
                    "url": rancher_url,
                    "error": f"Status code: {response.status_code}",
                    "host": self.hostname
                }
        
        except Exception as e:
            logger.error(f"Error checking Rancher status: {e}")
            return {
                "service": "Rancher",
                "status": "error",
                "error": str(e),
                "host": self.hostname
            }


def check_remote_access_tools(config, notifier = None) -> Dict[str, Any]:
    """
    Check the status of all configured remote access tools.
    
    Args:
        config: Application configuration
        notifier: Notification service (optional)
    
    Returns:
        Dictionary with status information for each tool
    """
    logger.info("Checking remote access tools")
    
    manager = RemoteAccessManager(config)
    results = {}
    
    # Check SSH
    if getattr(config, 'enable_ssh_monitoring', True):
        results['ssh'] = manager.check_ssh_status()
    
    # Check VPN
    vpn_types = getattr(config, 'monitored_vpn_types', ['openvpn', 'wireguard', 'tailscale'])
    results['vpn'] = {}
    
    for vpn_type in vpn_types:
        try:
            results['vpn'][vpn_type] = manager.check_vpn_status(vpn_type)
        except Exception as e:
            logger.error(f"Error checking {vpn_type} status: {e}")
            results['vpn'][vpn_type] = {
                "service": vpn_type,
                "status": "error",
                "error": str(e)
            }
    
    # Check remote desktop tools
    desktop_tools = getattr(config, 'monitored_desktop_tools', ['anydesk', 'teamviewer'])
    results['remote_desktop'] = {}
    
    for tool in desktop_tools:
        try:
            results['remote_desktop'][tool] = manager.check_remote_desktop_status(tool)
        except Exception as e:
            logger.error(f"Error checking {tool} status: {e}")
            results['remote_desktop'][tool] = {
                "service": tool,
                "status": "error",
                "error": str(e)
            }
    
    # Check Docker
    if getattr(config, 'enable_docker_monitoring', True):
        results['docker'] = manager.check_docker_status()
    
    # Check Portainer
    if getattr(config, 'enable_portainer_monitoring', False):
        results['portainer'] = manager.check_portainer_status()
    
    # Check Rancher
    if getattr(config, 'enable_rancher_monitoring', False):
        results['rancher'] = manager.check_rancher_status()
    
    # Store results for dashboard
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/remote_access_status.json', 'w') as f:
            json.dump(results, f)
    except Exception as e:
        logger.error(f"Error storing remote access status: {e}")
    
    # Send notification if any tool is down and notifier is provided
    if notifier:
        down_services = []
        
        # Check SSH
        if 'ssh' in results and results['ssh'].get('status') != 'running':
            down_services.append(f"SSH: {results['ssh'].get('error', 'Not running')}")
        
        # Check VPNs
        for vpn_type, status in results.get('vpn', {}).items():
            if status.get('status') != 'running':
                down_services.append(f"{vpn_type}: {status.get('error', 'Not running')}")
        
        # Check remote desktop tools
        for tool, status in results.get('remote_desktop', {}).items():
            if status.get('status') != 'running':
                down_services.append(f"{tool}: {status.get('error', 'Not running')}")
        
        # Check Docker
        if 'docker' in results and results['docker'].get('status') != 'running':
            down_services.append(f"Docker: {results['docker'].get('error', 'Not running')}")
        
        # Check Portainer
        if 'portainer' in results and results['portainer'].get('status') != 'running':
            down_services.append(f"Portainer: {results['portainer'].get('error', 'Not running')}")
        
        # Check Rancher
        if 'rancher' in results and results['rancher'].get('status') != 'running':
            down_services.append(f"Rancher: {results['rancher'].get('error', 'Not running')}")
        
        # Send notification if any service is down
        if down_services:
            notifier.send_alert(
                f"⚠️ REMOTE ACCESS TOOLS STATUS ALERT\n\n"
                f"The following remote access tools are not running:\n\n"
                f"- {'\n- '.join(down_services)}\n\n"
                f"Please check the system to ensure remote troubleshooting access is available."
            )
    
    return results
