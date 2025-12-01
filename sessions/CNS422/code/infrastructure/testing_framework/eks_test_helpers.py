"""
EKS REST API testing infrastructure.

This module provides helper classes and functions for testing REST API endpoints
deployed on EKS clusters with ALB ingress controllers. It includes ALB URL discovery,
timeout configuration, error handling, and health validation utilities.
"""

import json
import subprocess
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class EKSTestConfig:
    """
    Configuration class for EKS REST API testing.

    Provides ALB URL discovery, timeout configuration, and error handling
    for testing REST API endpoints deployed on EKS clusters.
    """

    def __init__(self, cluster_name: Optional[str] = None, timeout: int = 30):
        """
        Initialize EKS test configuration.

        Args:
            cluster_name: Name of the EKS cluster (optional, will try to auto-detect)
            timeout: Default timeout in seconds for HTTP requests to ALB endpoints
        """
        self.cluster_name = cluster_name
        self.timeout = timeout
        self.alb_urls: Dict[str, str] = {}
        self.terraform_outputs: Dict[str, Any] = {}

        # Service name to ingress name mapping
        self.service_ingress_mapping = {
            "customer-server": "customer-server-ingress",
            "appointment-server": "appointment-server-ingress",
            "technician-server": "technician-server-ingress"
        }

        # Service name to port mapping
        self.service_ports = {
            "customer-server": 8001,
            "appointment-server": 8002,
            "technician-server": 8003
        }

        # Initialize HTTP session with retry strategy
        self.session = self._create_http_session()

        # Discover ALB URLs on initialization
        self._discover_all_alb_urls()

    def _create_http_session(self) -> requests.Session:
        """
        Create HTTP session with retry strategy for ALB requests.

        Returns:
            Configured requests.Session with retry strategy
        """
        session = requests.Session()

        # Configure retry strategy for transient network issues
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _discover_all_alb_urls(self):
        """Discover ALB URLs for all services."""
        print("Discovering ALB URLs for EKS services...")

        for service_name in self.service_ingress_mapping.keys():
            try:
                url = self._discover_alb_url(service_name)
                if url:
                    self.alb_urls[service_name] = url
                    print(f"✓ Found ALB URL for {service_name}: {url}")
                else:
                    print(f"⚠ Could not discover ALB URL for {service_name}")
            except Exception as e:
                print(f"✗ Error discovering ALB URL for {service_name}: {e}")

    def _discover_alb_url(self, service_name: str) -> Optional[str]:
        """
        Discover ALB URL for a specific service using kubectl and terraform outputs.

        Args:
            service_name: Name of the service (e.g., 'customer-server')

        Returns:
            ALB URL if found, None otherwise
        """
        # Try kubectl ingress discovery first
        url = self._discover_alb_url_from_kubectl(service_name)
        if url:
            return url

        # Fallback to terraform outputs
        url = self._discover_alb_url_from_terraform(service_name)
        if url:
            return url

        return None

    def _discover_alb_url_from_kubectl(self, service_name: str) -> Optional[str]:
        """
        Discover ALB URL from kubectl ingress output using label selectors.

        Args:
            service_name: Name of the service

        Returns:
            ALB URL if found, None otherwise
        """
        try:
            # Try multiple label-based discovery approaches

            # 1. Try using app label selector (most common)
            url = self._try_get_ingress_by_label("app", service_name)
            if url:
                return url

            # 2. Try using app.kubernetes.io/name label (recommended Kubernetes label)
            url = self._try_get_ingress_by_label("app.kubernetes.io/name", service_name)
            if url:
                return url

            # 3. Try using service label
            url = self._try_get_ingress_by_label("service", service_name)
            if url:
                return url

            # 4. Try using component label
            url = self._try_get_ingress_by_label("app.kubernetes.io/component", service_name)
            if url:
                return url

            # 5. Fallback to name-based discovery for backward compatibility
            url = self._try_name_based_discovery(service_name)
            if url:
                return url

        except Exception as e:
            print(f"Error discovering ALB URL for {service_name}: {e}")

        return None

    def _try_get_ingress_by_label(self, label_key: str, service_name: str) -> Optional[str]:
        """
        Try to find ingress using label selector.

        Args:
            label_key: Label key to search by
            service_name: Service name to match in label value

        Returns:
            ALB URL if found, None otherwise
        """
        try:
            # Try exact match first
            label_selector = f"{label_key}={service_name}"
            url = self._get_ingress_by_selector(label_selector, service_name)
            if url:
                return url

            # Try without hyphen (e.g., customerserver instead of customer-server)
            service_name_no_hyphen = service_name.replace("-", "")
            label_selector = f"{label_key}={service_name_no_hyphen}"
            url = self._get_ingress_by_selector(label_selector, service_name)
            if url:
                return url

            # Try with underscores instead of hyphens
            service_name_underscore = service_name.replace("-", "_")
            label_selector = f"{label_key}={service_name_underscore}"
            url = self._get_ingress_by_selector(label_selector, service_name)
            if url:
                return url

        except Exception:
            pass

        return None

    def _get_ingress_by_selector(self, label_selector: str, service_name: str) -> Optional[str]:
        """
        Get ingress using kubectl with label selector.

        Args:
            label_selector: Label selector string
            service_name: Service name for logging

        Returns:
            ALB URL if found, None otherwise
        """
        try:
            cmd = ["kubectl", "get", "ingress", "--all-namespaces", "-l", label_selector, "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if result.returncode != 0:
                return None

            ingresses_data = json.loads(result.stdout)
            items = ingresses_data.get("items", [])

            if not items:
                return None

            # Use the first matching ingress
            ingress = items[0]
            url = self._extract_alb_url_from_ingress(ingress)

            if url:
                ingress_name = ingress.get("metadata", {}).get("name", "")
                namespace = ingress.get("metadata", {}).get("namespace", "default")
                print(f"Found {service_name} ingress '{ingress_name}' in namespace '{namespace}' using selector '{label_selector}'")
                return url

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            pass

        return None

    def _try_name_based_discovery(self, service_name: str) -> Optional[str]:
        """
        Fallback to name-based discovery for backward compatibility.

        Args:
            service_name: Service name

        Returns:
            ALB URL if found, None otherwise
        """
        try:
            ingress_name = self.service_ingress_mapping.get(service_name)
            if not ingress_name:
                return None

            # Try multiple approaches to find the ingress
            # 1. Try default namespace first
            url = self._try_get_ingress_url(ingress_name, None, service_name)
            if url:
                return url

            # 2. Try common namespaces
            common_namespaces = ["development", "dev", "production", "prod", "default"]
            for namespace in common_namespaces:
                # Try exact name
                url = self._try_get_ingress_url(ingress_name, namespace, service_name)
                if url:
                    return url

                # Try with namespace suffix (e.g., customer-server-ingress-dev)
                suffixed_name = f"{ingress_name}-{namespace}"
                url = self._try_get_ingress_url(suffixed_name, namespace, service_name)
                if url:
                    return url

                # Try with short namespace suffix
                if namespace in ["development", "production"]:
                    short_suffix = "dev" if namespace == "development" else "prod"
                    short_suffixed_name = f"{ingress_name}-{short_suffix}"
                    url = self._try_get_ingress_url(short_suffixed_name, namespace, service_name)
                    if url:
                        return url

            # 3. Try all namespaces as last resort
            url = self._try_get_ingress_all_namespaces(ingress_name, service_name)
            if url:
                return url

        except Exception as e:
            print(f"Error in name-based discovery for {service_name}: {e}")

        return None

    def _try_get_ingress_url(self, ingress_name: str, namespace: Optional[str], service_name: str) -> Optional[str]:
        """
        Try to get ingress URL from a specific namespace.

        Args:
            ingress_name: Name of the ingress resource
            namespace: Namespace to search in (None for default)
            service_name: Service name for logging

        Returns:
            ALB URL if found, None otherwise
        """
        try:
            cmd = ["kubectl", "get", "ingress", ingress_name, "-o", "json"]
            if namespace:
                cmd.extend(["-n", namespace])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return None

            ingress_data = json.loads(result.stdout)
            return self._extract_alb_url_from_ingress(ingress_data)

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            return None

    def _try_get_ingress_all_namespaces(self, ingress_name: str, service_name: str) -> Optional[str]:
        """
        Try to find ingress in all namespaces.

        Args:
            ingress_name: Name of the ingress resource
            service_name: Service name for logging

        Returns:
            ALB URL if found, None otherwise
        """
        try:
            # Get all ingresses across all namespaces
            cmd = ["kubectl", "get", "ingress", "--all-namespaces", "-o", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if result.returncode != 0:
                return None

            all_ingresses = json.loads(result.stdout)

            # Look for ingresses that match our service
            for item in all_ingresses.get("items", []):
                item_name = item.get("metadata", {}).get("name", "")

                # Check if this ingress matches our service
                if (item_name == ingress_name or
                    item_name.startswith(f"{ingress_name}-") or
                    service_name in item_name):

                    url = self._extract_alb_url_from_ingress(item)
                    if url:
                        namespace = item.get("metadata", {}).get("namespace", "default")
                        print(f"Found {service_name} ingress '{item_name}' in namespace '{namespace}'")
                        return url

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            pass

        return None

    def _extract_alb_url_from_ingress(self, ingress_data: dict) -> Optional[str]:
        """
        Extract ALB URL from ingress data.

        Args:
            ingress_data: Kubernetes ingress resource data

        Returns:
            ALB URL if found, None otherwise
        """
        try:
            status = ingress_data.get("status", {})
            load_balancer = status.get("loadBalancer", {})
            ingress_list = load_balancer.get("ingress", [])

            if ingress_list and len(ingress_list) > 0:
                hostname = ingress_list[0].get("hostname")
                if hostname:
                    # ALB URLs are typically HTTP for internal testing, but can be HTTPS
                    # Let's try HTTP first as it's more common for internal ALBs
                    return f"http://{hostname}"

        except Exception:
            pass

        return None

    def _discover_alb_url_from_terraform(self, service_name: str) -> Optional[str]:
        """
        Discover ALB URL from terraform outputs.

        Args:
            service_name: Name of the service

        Returns:
            ALB URL if found, None otherwise
        """
        try:
            # Load terraform outputs if not already loaded
            if not self.terraform_outputs:
                self._load_terraform_outputs()

            # Look for ALB-related outputs
            # This is a placeholder - actual terraform outputs would need to be defined
            alb_output_key = f"{service_name.replace('-', '_')}_alb_url"
            return self.terraform_outputs.get(alb_output_key)

        except Exception as e:
            print(f"Error getting terraform outputs for {service_name}: {e}")
            return None

    def _load_terraform_outputs(self):
        """Load terraform outputs from the infrastructure directory."""
        try:
            cmd = ["terraform", "output", "-json"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd="infrastructure/terraform"
            )

            if result.returncode == 0:
                self.terraform_outputs = json.loads(result.stdout)
            else:
                print(f"Failed to load terraform outputs: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("Terraform output command timed out")
        except json.JSONDecodeError as e:
            print(f"Failed to parse terraform outputs: {e}")
        except Exception as e:
            print(f"Error loading terraform outputs: {e}")

    def get_service_url(self, service_name: str) -> Optional[str]:
        """
        Get the ALB URL for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            ALB URL if available, None otherwise
        """
        return self.alb_urls.get(service_name)

    def get_all_service_urls(self) -> Dict[str, str]:
        """
        Get ALB URLs for all discovered services.

        Returns:
            Dictionary mapping service names to ALB URLs
        """
        return self.alb_urls.copy()

    def validate_alb_endpoint_accessibility(self, service_name: str) -> Tuple[bool, str]:
        """
        Validate that an ALB endpoint is accessible and healthy.

        Args:
            service_name: Name of the service to validate

        Returns:
            Tuple of (is_accessible, status_message)
        """
        url = self.get_service_url(service_name)
        if not url:
            return False, f"No ALB URL found for {service_name}"

        return self._check_endpoint_health(url, service_name)

    def validate_all_alb_endpoints(self) -> Dict[str, Tuple[bool, str]]:
        """
        Validate accessibility and health of all discovered ALB endpoints.

        Returns:
            Dictionary mapping service names to (is_accessible, status_message) tuples
        """
        results = {}

        for service_name in self.alb_urls.keys():
            results[service_name] = self.validate_alb_endpoint_accessibility(service_name)

        return results

    def _check_endpoint_health(self, base_url: str, service_name: str) -> Tuple[bool, str]:
        """
        Check the health of a specific endpoint.

        Args:
            base_url: Base URL of the service
            service_name: Name of the service for context

        Returns:
            Tuple of (is_healthy, status_message)
        """
        health_url = f"{base_url.rstrip('/')}/health"

        try:
            print(f"Checking health endpoint: {health_url}")

            response = self.session.get(
                health_url,
                timeout=self.timeout,
                headers={"User-Agent": "EKS-Test-Client/1.0"}
            )

            if response.status_code == 200:
                try:
                    health_data = response.json()
                    status = health_data.get("status", "unknown")
                    if status == "healthy":
                        return True, f"Service {service_name} is healthy"
                    else:
                        return False, f"Service {service_name} reports status: {status}"
                except json.JSONDecodeError:
                    return False, f"Service {service_name} returned invalid JSON health response"
            else:
                return False, f"Service {service_name} health check failed with status {response.status_code}"

        except requests.exceptions.Timeout:
            return False, f"Health check for {service_name} timed out after {self.timeout} seconds"
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error for {service_name}: {str(e)}"
        except requests.exceptions.RequestException as e:
            return False, f"Request error for {service_name}: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error checking {service_name}: {str(e)}"

    def wait_for_alb_readiness(self, service_name: str, max_wait_time: int = 300, check_interval: int = 10) -> bool:
        """
        Wait for an ALB endpoint to become ready and healthy.

        Args:
            service_name: Name of the service to wait for
            max_wait_time: Maximum time to wait in seconds
            check_interval: Time between health checks in seconds

        Returns:
            True if endpoint becomes ready, False if timeout
        """
        url = self.get_service_url(service_name)
        if not url:
            print(f"No ALB URL found for {service_name}")
            return False

        print(f"Waiting for {service_name} ALB endpoint to become ready...")
        print(f"URL: {url}")
        print(f"Max wait time: {max_wait_time} seconds")

        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            is_healthy, message = self._check_endpoint_health(url, service_name)

            if is_healthy:
                elapsed = int(time.time() - start_time)
                print(f"✓ {service_name} is ready after {elapsed} seconds")
                return True

            print(f"⏳ {message}, retrying in {check_interval} seconds...")
            time.sleep(check_interval)

        elapsed = int(time.time() - start_time)
        print(f"✗ {service_name} did not become ready within {elapsed} seconds")
        return False

    def get_service_port(self, service_name: str) -> int:
        """
        Get the port number for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            Port number for the service
        """
        return self.service_ports.get(service_name, 8000)

    def create_test_client_config(self, service_name: str) -> Dict[str, Any]:
        """
        Create configuration for test clients to use ALB endpoints.

        Args:
            service_name: Name of the service

        Returns:
            Configuration dictionary for test clients
        """
        base_url = self.get_service_url(service_name)

        return {
            "base_url": base_url,
            "timeout": self.timeout,
            "service_name": service_name,
            "port": self.get_service_port(service_name),
            "headers": {
                "User-Agent": "EKS-Test-Client/1.0",
                "Content-Type": "application/json"
            },
            "verify_ssl": True,  # ALB endpoints typically use valid SSL certificates
            "retry_config": {
                "total": 3,
                "backoff_factor": 1,
                "status_forcelist": [429, 500, 502, 503, 504]
            }
        }

    def print_discovery_summary(self):
        """Print a summary of ALB URL discovery results."""
        print("\n" + "="*60)
        print("EKS ALB URL Discovery Summary")
        print("="*60)

        if not self.alb_urls:
            print("⚠ No ALB URLs discovered")
            print("\nTroubleshooting:")
            print("1. Ensure kubectl is configured for the correct cluster")
            print("2. Verify ingress resources are deployed")
            print("3. Check that ALB controller is running")
            print("4. Confirm ingress resources have been assigned hostnames")
            return

        print(f"Discovered {len(self.alb_urls)} ALB endpoints:")

        for service_name, url in self.alb_urls.items():
            port = self.get_service_port(service_name)
            print(f"  • {service_name:20} (port {port}): {url}")

        print(f"\nConfiguration:")
        print(f"  • Timeout: {self.timeout} seconds")
        print(f"  • Cluster: {self.cluster_name or 'auto-detect'}")

        # Test connectivity
        print(f"\nConnectivity Test:")
        results = self.validate_all_alb_endpoints()

        for service_name, (is_accessible, message) in results.items():
            status_icon = "✓" if is_accessible else "✗"
            print(f"  {status_icon} {service_name}: {message}")

    def cleanup(self):
        """Clean up resources used by the test configuration."""
        if hasattr(self, 'session'):
            self.session.close()


def discover_eks_cluster_name() -> Optional[str]:
    """
    Discover the current EKS cluster name from kubectl context.

    Returns:
        Cluster name if found, None otherwise
    """
    try:
        cmd = ["kubectl", "config", "current-context"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            context = result.stdout.strip()
            # EKS contexts typically contain the cluster name
            if "eks" in context.lower():
                # Extract cluster name from context (format varies)
                parts = context.split("/")
                if len(parts) >= 2:
                    return parts[-1]  # Usually the last part is the cluster name

        return None

    except Exception as e:
        print(f"Error discovering cluster name: {e}")
        return None


def wait_for_all_services_ready(config: EKSTestConfig, max_wait_time: int = 300) -> bool:
    """
    Wait for all discovered ALB endpoints to become ready.

    Args:
        config: EKS test configuration
        max_wait_time: Maximum time to wait for all services

    Returns:
        True if all services become ready, False otherwise
    """
    service_names = list(config.get_all_service_urls().keys())

    if not service_names:
        print("No services found to wait for")
        return False

    print(f"Waiting for {len(service_names)} services to become ready...")

    ready_services = set()
    start_time = time.time()

    while len(ready_services) < len(service_names) and time.time() - start_time < max_wait_time:
        for service_name in service_names:
            if service_name in ready_services:
                continue

            is_healthy, message = config.validate_alb_endpoint_accessibility(service_name)
            if is_healthy:
                ready_services.add(service_name)
                print(f"✓ {service_name} is ready")

        if len(ready_services) < len(service_names):
            remaining = len(service_names) - len(ready_services)
            print(f"⏳ Waiting for {remaining} more services...")
            time.sleep(10)

    elapsed = int(time.time() - start_time)

    if len(ready_services) == len(service_names):
        print(f"🎉 All {len(service_names)} services are ready after {elapsed} seconds")
        return True
    else:
        not_ready = set(service_names) - ready_services
        print(f"✗ {len(not_ready)} services not ready after {elapsed} seconds: {', '.join(not_ready)}")
        return False


def create_eks_test_config(cluster_name: Optional[str] = None, timeout: int = 30) -> EKSTestConfig:
    """
    Create and initialize an EKS test configuration.

    Args:
        cluster_name: Name of the EKS cluster (auto-detect if None)
        timeout: Default timeout for HTTP requests

    Returns:
        Initialized EKSTestConfig instance
    """
    if cluster_name is None:
        cluster_name = discover_eks_cluster_name()

    config = EKSTestConfig(cluster_name=cluster_name, timeout=timeout)
    config.print_discovery_summary()

    return config
