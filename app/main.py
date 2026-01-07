import streamlit as st
import docker
import pandas as pd
import tarfile
import io
from datetime import datetime

st.set_page_config(page_title="Docker Container Manager", page_icon="🐳", layout="wide")

st.title("🐳 Docker Container Manager")

def get_docker_client():
    """Get Docker client with error handling."""
    try:
        client = docker.from_env()
        # Test connection
        client.ping()
        return client
    except docker.errors.DockerException as e:
        st.error(f"❌ Cannot connect to Docker daemon: {e}")
        st.info("💡 Make sure Docker is running and accessible")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
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

def format_size(bytes_size):
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

# Initialize Docker client
client = get_docker_client()

if client is None:
    st.stop()

# Sidebar for container selection
st.sidebar.header("📦 Select Container")

# Refresh button
if st.sidebar.button("🔄 Refresh", use_container_width=True):
    st.rerun()

show_all = st.sidebar.checkbox("Show all containers", value=False)

# Get containers
try:
    containers = client.containers.list(all=show_all)

    if not containers:
        if show_all:
            st.warning("No containers found on this system")
        else:
            st.warning("No running containers found. Check 'Show all containers' to see stopped ones.")
        st.stop()

    # Container selection
    container_names = [f"{c.name} ({c.status})" for c in containers]
    selected_idx = st.sidebar.selectbox(
        "Container",
        range(len(containers)),
        format_func=lambda x: container_names[x]
    )

    selected_container = containers[selected_idx]

    # Status indicator
    status_color = "🟢" if selected_container.status == "running" else "🔴"
    st.sidebar.metric("Status", f"{status_color} {selected_container.status}")
    st.sidebar.metric("ID", selected_container.short_id)

except Exception as e:
    st.error(f"Error listing containers: {e}")
    st.stop()

# Page selection
page = st.sidebar.selectbox("Page", ["Container Info", "File Manager", "All Containers"])

# Container actions
if page != "All Containers":
    st.sidebar.divider()
    st.sidebar.subheader("🎮 Actions")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if selected_container.status == "running":
            if st.button("⏸️ Stop", use_container_width=True):
                try:
                    selected_container.stop()
                    st.success(f"Stopped {selected_container.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            if st.button("▶️ Start", use_container_width=True):
                try:
                    selected_container.start()
                    st.success(f"Started {selected_container.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        if st.button("🔄 Restart", use_container_width=True):
            try:
                selected_container.restart()
                st.success(f"Restarted {selected_container.name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# PAGE: Container Info
if page == "Container Info":
    st.header(f"📊 {selected_container.name}")

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
    with st.expander("📜 Recent Logs (last 100 lines)"):
        if selected_container.status == "running":
            try:
                logs = selected_container.logs(tail=100).decode('utf-8')
                st.code(logs)
            except Exception as e:
                st.error(f"Cannot get logs: {e}")
        else:
            st.info("Container is not running")

# PAGE: File Manager
elif page == "File Manager":
    st.header(f"📁 File Manager: {selected_container.name}")

    if selected_container.status != "running":
        st.warning("⚠️ Container must be running to browse files")
        st.stop()

    # Path input
    if 'current_path' not in st.session_state:
        st.session_state.current_path = "/home/terminal"

    current_path = st.text_input("Path", value=st.session_state.current_path)
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

# PAGE: All Containers
elif page == "All Containers":
    st.header("📦 All Containers")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Refresh List"):
            st.rerun()

    try:
        all_containers = client.containers.list(all=show_all)

        if not all_containers:
            st.info("No containers found")
            st.stop()

        # Prepare data
        container_data = []
        for container in all_containers:
            attrs = container.attrs
            container_data.append({
                'Name': container.name,
                'ID': container.id[:12],
                'Image': container.image.tags[0] if container.image.tags else container.image.id[:12],
                'Status': container.status,
                'Ports': format_ports(attrs['NetworkSettings']['Ports']),
                'Created': attrs['Created'][:19].replace('T', ' ')
            })

        # Display table
        df = pd.DataFrame(container_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.caption(f"Total: {len(all_containers)} containers")

    except Exception as e:
        st.error(f"Error: {e}")

# Footer
st.sidebar.divider()
st.sidebar.info("🐳 Container Manager v2.1")
st.sidebar.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
