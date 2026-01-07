"""
Docker Container Manager

Simple web interface to view, manage, and download files from Docker containers.
"""
import streamlit as st
import docker
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Container Manager", page_icon="🐳", layout="wide")

st.title("🐳 Docker Container Manager")

st.write("""
Manage Docker containers and download files from them.
""")

def get_docker_client():
    """Get Docker client with error handling."""
    try:
        client = docker.from_env()
        # Test connection
        client.ping()
        return client
    except docker.errors.DockerException as e:
        st.error(f"Cannot connect to Docker daemon: {e}")
        st.info("💡 Make sure Docker is running and the socket is mounted")
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
        return created_str[:19].replace('T', ' ')
    except:
        return created_str

def format_size(bytes_size):
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

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

def restart_container(container_id):
    """Restart a container."""
    try:
        client = get_docker_client()
        if client:
            container = client.containers.get(container_id)
            container.restart()
            st.success(f"Container {container_id[:12]} restarted successfully!")
            st.rerun()
    except Exception as e:
        st.error(f"Error restarting container: {e}")

# Get Docker client
client = get_docker_client()

if client is None:
    st.stop()

# Sidebar
st.sidebar.header("Settings")

# Refresh button
if st.sidebar.button("🔄 Refresh", use_container_width=True):
    st.rerun()

show_all = st.sidebar.checkbox("Show all containers", value=False, help="Show stopped containers too")

# Page selection
page = st.sidebar.selectbox("Page", ["Container List", "Container Details", "File Browser"])

# Get containers
try:
    containers = client.containers.list(all=show_all)

    if not containers:
        if show_all:
            st.info("No containers found on this system.")
        else:
            st.info("No running containers found. Check 'Show all containers' to see stopped ones.")
        st.stop()

    # Container selection for detail pages
    if page in ["Container Details", "File Browser"]:
        st.sidebar.divider()
        st.sidebar.subheader("Select Container")

        container_names = [f"{c.name} ({c.status})" for c in containers]
        selected_idx = st.sidebar.selectbox(
            "Container",
            range(len(containers)),
            format_func=lambda x: container_names[x]
        )
        selected_container = containers[selected_idx]

        # Show status
        status_color = "🟢" if selected_container.status == "running" else "🔴"
        st.sidebar.metric("Status", f"{status_color} {selected_container.status}")
        st.sidebar.metric("ID", selected_container.short_id)

        # Action buttons
        st.sidebar.divider()
        st.sidebar.subheader("Actions")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            if selected_container.status == "running":
                if st.button("⏸️ Stop", use_container_width=True):
                    stop_container(selected_container.id)
            else:
                if st.button("▶️ Start", use_container_width=True):
                    start_container(selected_container.id)

        with col2:
            if st.button("🔄 Restart", use_container_width=True):
                restart_container(selected_container.id)

    # PAGE: Container List
    if page == "Container List":
        st.header("📦 All Containers")

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
                'Ports': format_ports(network_settings.get('Ports', {})),
                'Created': format_created_time(attrs.get('Created', '')),
                'Full ID': container.id
            }
            container_data.append(container_info)

        # Display containers in a table
        df = pd.DataFrame(container_data)

        st.subheader(f"Containers ({len(containers)} found)")

        # Display the table without the Full ID column
        display_df = df.drop('Full ID', axis=1)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Action buttons for each container
        st.divider()
        st.subheader("Quick Actions")

        for i, container_info in enumerate(container_data):
            container_id = container_info['Full ID']
            container_name = container_info['Name']
            container_status = container_info['Status']

            with st.expander(f"{container_name} ({container_info['ID']})"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    if container_status == 'running':
                        st.button(f"⏹️ Stop",
                                  key=f"stop_{i}",
                                  use_container_width=True,
                                  on_click=stop_container,
                                  args=(container_id,))
                    else:
                        st.button(f"▶️ Start",
                                  key=f"start_{i}",
                                  use_container_width=True,
                                  on_click=start_container,
                                  args=(container_id,))

                with col2:
                    st.button(f"🔄 Restart",
                              key=f"restart_{i}",
                              use_container_width=True,
                              on_click=restart_container,
                              args=(container_id,))

                with col3:
                    if st.button(f"📋 Details", key=f"details_{i}", use_container_width=True):
                        st.session_state['selected_container_idx'] = i
                        st.session_state['page'] = "Container Details"
                        st.rerun()

    # PAGE: Container Details
    elif page == "Container Details":
        st.header(f"📊 Container: {selected_container.name}")

        selected_container.reload()
        attrs = selected_container.attrs

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Basic Info")
            st.text(f"Name: {selected_container.name}")
            st.text(f"ID: {selected_container.id[:12]}")
            image_name = selected_container.image.tags[0] if selected_container.image.tags else selected_container.image.id[:12]
            st.text(f"Image: {image_name}")
            st.text(f"Status: {selected_container.status}")
            st.text(f"Created: {attrs['Created'][:19].replace('T', ' ')}")

            st.subheader("Ports")
            ports = attrs['NetworkSettings']['Ports']
            if ports:
                for port, bindings in ports.items():
                    if bindings:
                        for binding in bindings:
                            st.text(f"{binding['HostPort']} → {port}")
                    else:
                        st.text(f"{port} (not published)")
            else:
                st.text("No ports exposed")

        with col2:
            st.subheader("Resources")

            if selected_container.status == "running":
                try:
                    stats = selected_container.stats(stream=False)

                    # CPU
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                    cpu_count = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
                    cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0 if system_delta > 0 else 0
                    st.metric("CPU Usage", f"{cpu_percent:.2f}%")

                    # Memory
                    mem_usage = stats['memory_stats'].get('usage', 0)
                    mem_limit = stats['memory_stats'].get('limit', 1)
                    mem_percent = (mem_usage / mem_limit) * 100
                    st.metric("Memory Usage", f"{mem_percent:.2f}%")
                    st.text(f"{format_size(mem_usage)} / {format_size(mem_limit)}")

                    # Network
                    if 'networks' in stats:
                        net_rx = sum(net['rx_bytes'] for net in stats['networks'].values())
                        net_tx = sum(net['tx_bytes'] for net in stats['networks'].values())
                        st.metric("Network RX", format_size(net_rx))
                        st.metric("Network TX", format_size(net_tx))

                except Exception as e:
                    st.warning(f"Cannot get stats: {e}")
            else:
                st.info("Container is not running")

        st.divider()

        # Environment Variables
        with st.expander("🔐 Environment Variables"):
            env_vars = attrs['Config']['Env']
            sensitive = ['API_KEY', 'PASSWORD', 'SECRET', 'TOKEN', 'ANTHROPIC']
            for env in sorted(env_vars):
                if '=' in env:
                    key, value = env.split('=', 1)
                    if any(s in key.upper() for s in sensitive):
                        st.text(f"{key} = ***HIDDEN***")
                    else:
                        st.text(f"{key} = {value}")
                else:
                    st.text(env)

        # Volumes
        with st.expander("💾 Volumes & Mounts"):
            mounts = attrs['Mounts']
            if mounts:
                for mount in mounts:
                    st.text(f"Type: {mount['Type']}")
                    if mount['Type'] == 'volume':
                        st.text(f"  Volume: {mount.get('Name', 'N/A')}")
                    st.text(f"  Source: {mount['Source']}")
                    st.text(f"  Destination: {mount['Destination']}")
                    st.text(f"  Mode: {mount.get('Mode', 'rw')}")
                    st.text("---")
            else:
                st.text("No volumes mounted")

        # Logs
        with st.expander("📜 Recent Logs (last 50 lines)"):
            if selected_container.status == "running":
                try:
                    logs = selected_container.logs(tail=50).decode('utf-8')
                    st.code(logs)
                except Exception as e:
                    st.error(f"Cannot get logs: {e}")
            else:
                st.info("Container is not running")

    # PAGE: File Browser
    elif page == "File Browser":
        st.header(f"📁 File Browser: {selected_container.name}")

        if selected_container.status != "running":
            st.warning("⚠️ Container must be running to browse files")
            st.stop()

        # Path input
        if 'current_path' not in st.session_state:
            st.session_state.current_path = "/home"

        current_path = st.text_input("Current Path", value=st.session_state.current_path)
        st.session_state.current_path = current_path

        # List directory
        try:
            exec_result = selected_container.exec_run(f'ls -la {current_path}')
            if exec_result.exit_code == 0:
                st.code(exec_result.output.decode('utf-8'))
            else:
                st.error(f"Error: {exec_result.output.decode('utf-8')}")
        except Exception as e:
            st.error(f"Cannot list directory: {e}")

        st.divider()

        # Quick navigation
        st.subheader("⚡ Quick Navigation")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📁 /home"):
                st.session_state.current_path = "/home"
                st.rerun()
        with col2:
            if st.button("📁 /tmp"):
                st.session_state.current_path = "/tmp"
                st.rerun()
        with col3:
            if st.button("📁 /var/log"):
                st.session_state.current_path = "/var/log"
                st.rerun()
        with col4:
            if st.button("📁 /etc"):
                st.session_state.current_path = "/etc"
                st.rerun()

        st.divider()

        # Download section
        st.subheader("📦 Download Files/Folders")

        download_path = st.text_input("Path to Download", value=current_path)
        archive_name = st.text_input("Archive Name", value=f"{selected_container.name}_download")

        if st.button("📥 Download as TAR", type="primary"):
            if download_path:
                with st.spinner("Creating archive..."):
                    try:
                        bits, stat = selected_container.get_archive(download_path)
                        tar_data = b''.join(bits)

                        st.success(f"✅ Archive created! Size: {format_size(len(tar_data))}")
                        st.download_button(
                            label="⬇️ Download Archive",
                            data=tar_data,
                            file_name=f"{archive_name}.tar",
                            mime="application/x-tar"
                        )
                    except docker.errors.NotFound:
                        st.error(f"❌ Path not found: {download_path}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

        st.divider()

        # Execute command
        st.subheader("⚙️ Execute Command")
        command = st.text_input("Command", placeholder="ls -la /home")

        if st.button("▶️ Execute"):
            if command:
                with st.spinner("Executing..."):
                    try:
                        exec_result = selected_container.exec_run(command)
                        output = exec_result.output.decode('utf-8')

                        if exec_result.exit_code == 0:
                            st.success(f"✅ Exit code: {exec_result.exit_code}")
                        else:
                            st.error(f"❌ Exit code: {exec_result.exit_code}")

                        st.code(output)
                    except Exception as e:
                        st.error(f"Error: {e}")

except docker.errors.DockerException as e:
    st.error(f"Docker error: {e}")
except Exception as e:
    st.error(f"Unexpected error: {e}")

# Footer
st.sidebar.divider()
st.sidebar.info("🐳 Container Manager v2.1")
st.sidebar.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
