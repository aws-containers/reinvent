#!/usr/bin/env python3
"""
Simple Flask app that displays a QR code for demo purposes.
Shows cluster info and stays available during EKS Auto Mode upgrades.
"""
import os
import socket
import subprocess
from datetime import datetime
from flask import Flask, render_template_string, request
import qrcode
import io
import base64

app = Flask(__name__)

def get_all_pods_and_nodes():
    """Get all pods and their nodes from the cluster with node versions"""
    try:
        token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
        ca_cert_path = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
        
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                token = f.read().strip()
            
            import urllib.request
            import json
            import ssl
            
            context = ssl.create_default_context(cafile=ca_cert_path)
            
            # Get all nodes first to get their versions
            nodes_versions = {}
            try:
                url = 'https://kubernetes.default.svc/api/v1/nodes'
                req = urllib.request.Request(url)
                req.add_header('Authorization', f'Bearer {token}')
                
                with urllib.request.urlopen(req, context=context, timeout=2) as response:
                    nodes_data = json.loads(response.read().decode())
                    for node in nodes_data['items']:
                        node_name = node['metadata']['name']
                        version = node['status']['nodeInfo']['kubeletVersion']
                        # Get just v1.30 or v1.31
                        short_version = version.split('.')[0] + '.' + version.split('.')[1]
                        nodes_versions[node_name] = short_version
            except Exception as e:
                print(f"Error getting node versions: {e}")
            
            # Get all pods
            url = 'https://kubernetes.default.svc/api/v1/namespaces/default/pods?labelSelector=app=eks-demo-app'
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Bearer {token}')
            
            with urllib.request.urlopen(req, context=context, timeout=2) as response:
                data = json.loads(response.read().decode())
                
                # Group pods by node
                nodes_dict = {}
                for pod in data['items']:
                    node_name = pod['spec'].get('nodeName', 'Unknown')
                    pod_name = pod['metadata']['name']
                    pod_status = pod['status']['phase']
                    
                    if node_name not in nodes_dict:
                        nodes_dict[node_name] = {
                            'version': nodes_versions.get(node_name, 'Unknown'),
                            'pods': []
                        }
                    nodes_dict[node_name]['pods'].append({
                        'name': pod_name,
                        'status': pod_status
                    })
                
                return nodes_dict
    except Exception as e:
        print(f"Error getting pods and nodes: {e}")
    
    return {}

def get_versions():
    """Get both control plane and node Kubernetes versions"""
    control_plane_version = 'Unknown'
    node_version = 'Unknown'
    
    try:
        node_name = os.environ.get('NODE_NAME', '')
        
        # Read from the Kubernetes API via service account
        token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
        ca_cert_path = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
        
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                token = f.read().strip()
            
            import urllib.request
            import json
            import ssl
            
            # Create SSL context with CA cert
            context = ssl.create_default_context(cafile=ca_cert_path)
            
            # Get control plane version
            try:
                url = 'https://kubernetes.default.svc/version'
                req = urllib.request.Request(url)
                req.add_header('Authorization', f'Bearer {token}')
                
                with urllib.request.urlopen(req, context=context, timeout=2) as response:
                    data = json.loads(response.read().decode())
                    version = data['gitVersion']
                    # Return just the version number (e.g., v1.30 or v1.31)
                    control_plane_version = version.split('.')[0] + '.' + version.split('.')[1]
            except Exception as e:
                print(f"Error getting control plane version: {e}")
            
            # Get node version
            if node_name and node_name != 'unknown':
                try:
                    url = f'https://kubernetes.default.svc/api/v1/nodes/{node_name}'
                    req = urllib.request.Request(url)
                    req.add_header('Authorization', f'Bearer {token}')
                    
                    with urllib.request.urlopen(req, context=context, timeout=2) as response:
                        data = json.loads(response.read().decode())
                        version = data['status']['nodeInfo']['kubeletVersion']
                        # Return just the version number (e.g., v1.30 or v1.31)
                        node_version = version.split('.')[0] + '.' + version.split('.')[1]
                except Exception as e:
                    print(f"Error getting node version: {e}")
    except Exception as e:
        print(f"Error in get_versions: {e}")
    
    return control_plane_version, node_version

# HTML template with QR code
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>EKS Auto Mode Demo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 10px;
            margin: 0;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        h1 {
            font-size: clamp(1.5em, 5vw, 2.5em);
            margin-bottom: 10px;
        }
        .status {
            font-size: clamp(1em, 3vw, 1.5em);
            color: #4ade80;
            margin: 15px 0;
            font-weight: bold;
        }
        .version-badges {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        .version-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 10px 20px;
            border-radius: 25px;
            font-size: clamp(0.9em, 2.5vw, 1.2em);
            font-weight: bold;
            border: 3px solid #fbbf24;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        .highlight {
            background: rgba(251, 191, 36, 0.3);
            padding: 2px 8px;
            border-radius: 5px;
        }
        .nodes-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .node-box {
            background: rgba(0, 0, 0, 0.3);
            border: 3px solid #fbbf24;
            border-radius: 15px;
            padding: 15px;
            text-align: left;
        }
        .node-header {
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 10px;
            color: #fbbf24;
            border-bottom: 2px solid #fbbf24;
            padding-bottom: 5px;
        }
        .pod-item {
            background: rgba(102, 126, 234, 0.3);
            border-left: 4px solid #4ade80;
            padding: 8px;
            margin: 8px 0;
            border-radius: 5px;
            font-size: 0.85em;
            word-break: break-all;
        }
        .qr-section {
            margin: 20px 0;
        }
        .qr-code {
            background: white;
            padding: 15px;
            border-radius: 15px;
            display: inline-block;
            max-width: 100%;
        }
        .qr-code img {
            max-width: 100%;
            height: auto;
            display: block;
        }
        .info {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            text-align: left;
            font-size: clamp(0.8em, 2vw, 0.9em);
        }
        .info-item {
            margin: 8px 0;
        }
        .info-label {
            font-weight: bold;
            color: #fbbf24;
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            .nodes-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 EKS Auto Mode Demo</h1>
        
        <div class="version-badges">
            <div class="version-badge">
                Control Plane: <span class="highlight">{{ control_plane_version }}</span>
            </div>
            <div class="version-badge">
                Node Version: <span class="highlight">{{ node_version }}</span>
            </div>
        </div>
        
        <div class="status pulse">✅ Application Running</div>
        
        <h2 style="margin: 20px 0; font-size: clamp(1.2em, 4vw, 1.8em);">📦 Cluster Topology</h2>
        <div class="nodes-container">
            {% for node, node_data in nodes_pods.items() %}
            <div class="node-box">
                <div class="node-header">
                    🖥️ {{ node[:20] }}...<br>
                    <span style="color: #4ade80; font-size: 0.9em;">{{ node_data.version }}</span>
                </div>
                {% for pod in node_data.pods %}
                <div class="pod-item">
                    🔷 {{ pod.name[:30] }}...<br>
                    <small>Status: {{ pod.status }}</small>
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </div>
        
        <div class="qr-section">
            <p style="margin: 15px 0;">📱 Scan to monitor from your phone!</p>
            <div class="qr-code">
                <img src="data:image/png;base64,{{ qr_code }}" alt="QR Code">
            </div>
        </div>
        
        <div class="info">
            <div class="info-item">
                <span class="info-label">🔷 Current Pod:</span> {{ pod_name }}
            </div>
            <div class="info-item">
                <span class="info-label">🖥️ Current Node:</span> {{ node_name }}
            </div>
            <div class="info-item">
                <span class="info-label">🔄 Last Updated:</span> {{ timestamp }}
            </div>
            <div class="info-item">
                <span class="info-label">📊 Request Count:</span> {{ request_count }}
            </div>
        </div>
        <p style="margin-top: 20px; font-size: clamp(0.8em, 2vw, 0.9em); opacity: 0.9;">
            ⚡ This page auto-refreshes every 3 seconds<br>
            Watch the node version change during upgrades!
        </p>
    </div>
    <script>
        // Auto-refresh every 3 seconds to show live updates
        setTimeout(function(){ location.reload(); }, 3000);
    </script>
</body>
</html>
"""

request_count = 0

@app.route('/')
def index():
    global request_count
    request_count += 1
    
    # Get pod and node information from environment variables
    pod_name = os.environ.get('POD_NAME', 'unknown')
    node_name = os.environ.get('NODE_NAME', 'unknown')
    control_plane_version, node_version = get_versions()
    nodes_pods = get_all_pods_and_nodes()
    
    # Get the service URL - use the request host if available
    service_url = os.environ.get('SERVICE_URL', '')
    if not service_url or service_url == 'Scan QR code to access this app!':
        # Use the actual host from the request
        from flask import request
        service_url = f"http://{request.host}"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(service_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qr_code_base64 = base64.b64encode(buf.getvalue()).decode()
    
    return render_template_string(
        HTML_TEMPLATE,
        qr_code=qr_code_base64,
        pod_name=pod_name,
        node_name=node_name,
        control_plane_version=control_plane_version,
        node_version=node_version,
        nodes_pods=nodes_pods,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        request_count=request_count
    )

@app.route('/health')
def health():
    return {'status': 'healthy', 'pod': os.environ.get('POD_NAME', 'unknown')}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
