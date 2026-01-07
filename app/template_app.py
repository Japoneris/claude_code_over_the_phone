"""
Container Management Page

This page displays all running Docker containers and provides basic management functionality.
"""
import streamlit as st
import docker
import pandas as pd
from datetime import datetime

st.title("🐳 Container Management")

st.write("""
This page shows all Docker containers on your system and provides basic management functionality.
""")

def get_docker_client():
    """Get Docker client with error handling."""
    try:
        client = docker.from_env()
        # Test connection
        p = client.ping()
        print("Ping docker", p)
        return client
    
    except docker.errors.DockerException as e:
        st.error(f"Cannot connect to Docker daemon: {e}")
        return None
    
    except Exception as e:
        st.error(f"Unexpected error connecting to Docker: {e}")
        return None

def format_ports(port_bindings):
    """Format port bindings for display."""
    if not port_bindings:
        return "None"
    
    ports = []
    for container_port, host_bindings in port_bindings.items():
        if host_bindings:
            for binding in host_bindings:
                host_port = binding['HostPort']
                ports.append(f"{host_port}→{container_port}")
        else:
            ports.append(f"*→{container_port}")
    
    return ", ".join(ports)

def format_created_time(created_str):
    """Format container creation time."""
    try:
        created_time = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
        return created_time.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return created_str

def stop_container(container_id):
    """Stop a container."""
    try:
        client = get_docker_client()
        if client:
            container = client.containers.get(container_id)
            container.stop()
            st.success(f"Container {container_id[:12]} stopped successfully!")
            st.rerun()
    except Exception as e:
        st.error(f"Error stopping container: {e}")

def start_container(container_id):
    """Start a container."""
    try:
        client = get_docker_client()
        if client:
            container = client.containers.get(container_id)
            container.start()
            st.success(f"Container {container_id[:12]} started successfully!")
            st.rerun()
    except Exception as e:
        st.error(f"Error starting container: {e}")

def remove_container(container_id):
    """Remove a container."""
    try:
        client = get_docker_client()
        if client:
            container = client.containers.get(container_id)
            container.remove(force=True)
            st.success(f"Container {container_id[:12]} removed successfully!")
            #st.rerun()

    except Exception as e:
        st.error(f"Error removing container: {e}")

def connect_to_container(container_id):
    """Connect to container in the main app."""
    try:
        # Import the connection function from the container module
        from container import connect_to_existing_container
        
        container = connect_to_existing_container(container_id)
        if container:
            st.session_state["container"] = container
            st.session_state["container_files"] = []
            st.success(f"Connected to container {container_id[:12]}! You can now use it in the SWE agent page.")
        else:
            st.error("Failed to connect to container")
    except ImportError:
        st.error("Container connection functionality not available. Please implement connect_to_existing_container in container.py")
    except Exception as e:
        st.error(f"Error connecting to container: {e}")

# Get Docker client
client = get_docker_client()

if client is None:
    st.stop()

# Refresh button
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("🔄 Refresh", help="Refresh container list"):
        st.rerun()

with col2:
    show_all = st.checkbox("Show all", help="Show all containers (including stopped ones)")

# Get containers
try:
    containers = client.containers.list(all=show_all)
    
    if not containers:
        if show_all:
            st.info("No containers found on this system.")
        else:
            st.info("No running containers found. Check 'Show all' to see stopped containers.")
        st.stop()
    
    # Prepare data for display
    container_data = []
    for container in containers:
        # Get container attributes
        attrs = container.attrs
        config = attrs.get('Config', {})
        network_settings = attrs.get('NetworkSettings', {})
        
        container_info = {
            'ID': container.id[:12],
            'Name': container.name,
            'Image': config.get('Image', 'Unknown'),
            'Status': container.status,
            'State': attrs.get('State', {}).get('Status', 'Unknown'),
            'Ports': format_ports(network_settings.get('Ports', {})),
            'Created': format_created_time(attrs.get('Created', '')),
            'Full ID': container.id
        }
        container_data.append(container_info)
    
    # Display containers in a table
    df = pd.DataFrame(container_data)
    
    st.subheader(f"Containers ({len(containers)} found)")
    
    # Display the table without the Full ID column (we'll use it for actions)
    display_df = df.drop('Full ID', axis=1)
    st.dataframe(display_df, width="stretch")
    
    # Action buttons for each container
    st.subheader("Container Actions")
    
    for i, container_info in enumerate(container_data):
        container_id = container_info['Full ID']
        container_name = container_info['Name']
        container_status = container_info['Status']
        
        with st.expander(f"Actions for {container_name} ({container_info['ID']})"):
            
            # Connect button (only for running containers)
            if container_status == 'running':
                st.button(f"🔗 Connect to {container_name}", 
                          key=f"connect_{i}", 
                          help=f"Connect to {container_name} for use in SWE agent", 
                          width="stretch",
                          on_click=connect_to_container,
                          args=(container_id,))
            
            # Start/Stop button
            if container_status == 'running':
                st.button(f"⏹️ Stop {container_name}", 
                          key=f"stop_{i}", 
                          help=f"Stop the running container {container_name}", 
                          width="stretch",
                          on_click=stop_container,
                          args=(container_id,))

            elif container_status in ['exited', 'created']:
                st.button(f"▶️ Start {container_name}", 
                          key=f"start_{i}", 
                          help=f"Start the stopped container {container_name}", 
                          width="stretch",
                          on_click=start_container,
                          args=(container_id,))
            
            # Remove button
            if st.button(f"🗑️ Remove {container_name}", key=f"remove_{i}", help=f"Permanently remove container {container_name}", width="stretch"):
                # Add confirmation
                st.warning(f"⚠️ Are you sure you want to remove **{container_name}**? This action cannot be undone!")
                st.button(f"✅ Confirm Remove {container_name}", key=f"confirm_remove_{i}", width="stretch", on_click=remove_container, args=(container_id,))
            
            # Details button
            if st.button(f"📋 Show Details for {container_name}", key=f"details_{i}", help=f"Show detailed information about {container_name}", width="stretch"):
                container_obj = client.containers.get(container_id)
                attrs = container_obj.attrs
                
                st.json({
                    'ID': container_id,
                    'Name': container_name,
                    'Image': attrs.get('Config', {}).get('Image'),
                    'Command': attrs.get('Config', {}).get('Cmd'),
                    'Environment': attrs.get('Config', {}).get('Env'),
                    'WorkingDir': attrs.get('Config', {}).get('WorkingDir'),
                    'Ports': attrs.get('NetworkSettings', {}).get('Ports'),
                    'Mounts': [m['Source'] + ' → ' + m['Destination'] for m in attrs.get('Mounts', [])],
                    'State': attrs.get('State')
                })

except docker.errors.DockerException as e:
    st.error(f"Docker error: {e}")
except Exception as e:
    st.error(f"Unexpected error: {e}")

# Current connection status
st.divider()
if "container" in st.session_state:
    current_container = st.session_state["container"]
    try:
        container_id = current_container.get_container_ID()
        st.success(f"✅ Currently connected to container: {container_id}")
    except:
        st.warning("⚠️ Connected to a container, but unable to get its ID")
else:
    st.info("💡 No container currently connected in the SWE agent")
