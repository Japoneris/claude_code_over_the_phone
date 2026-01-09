import streamlit as st
import docker
import os


def get_docker_client():
    """Get Docker client with error handling."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        st.error(f"Cannot connect to Docker: {e}")
        return None

def get_compose_project():
    """Get the compose project name of the current container."""
    try:
        client = get_docker_client()
        if client:
            hostname = os.environ.get('HOSTNAME', '')
            if hostname:
                container = client.containers.get(hostname)
                labels = container.labels
                return labels.get('com.docker.compose.project', None)
    except:
        pass
    return None

def stop_container(container_id):
    """Stop a container."""
    try:
        client = get_docker_client()
        if client:
            container = client.containers.get(container_id)
            container.stop()
            st.success(f"Container stopped successfully!")
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
            st.success(f"Container started successfully!")
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
            st.success(f"Container restarted successfully!")
            st.rerun()
    except Exception as e:
        st.error(f"Error restarting container: {e}")

def show_container_info(container_id):
    """Show detailed information about a container."""
    try:
        client = get_docker_client()
        if client:
            container = client.containers.get(container_id)
            st.session_state[f"show_info_{container_id}"] = not st.session_state.get(f"show_info_{container_id}", False)
    except Exception as e:
        st.error(f"Error getting container info: {e}")

# Header
st.title("🐳 Container List")

# Sidebar
if st.sidebar.button("🔄 Refresh"):
    st.rerun()

# Get Docker client
client = get_docker_client()
if client is None:
    st.stop()

# Get compose project for filtering
compose_project = get_compose_project()

if compose_project:
    st.sidebar.info(f"📦 Project: **{compose_project}**")

try:
    # Get all containers
    all_containers = client.containers.list(all=True)

    # Filter containers by compose project
    if compose_project:
        containers = [c for c in all_containers
                     if c.labels.get('com.docker.compose.project') == compose_project]
    else:
        containers = all_containers
        st.warning("Could not detect compose project. Showing all containers.")

    if not containers:
        st.info("No containers found in this compose project.")
        st.stop()

    st.write(f"Found **{len(containers)}** container(s) in this project")
    st.divider()

    for container in containers:
        with st.expander(f"📦 {container.name}", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Status indicator
                status_emoji = "🟢" if container.status == "running" else "🔴"
                st.write(f"**Status:** {status_emoji} {container.status}")

                st.write(f"**Image:** {container.image.tags[0] if container.image.tags else container.image.id[:12]}")
                st.write(f"**ID:** {container.short_id}")

                # Show ports if any
                attrs = container.attrs
                ports = attrs['NetworkSettings']['Ports']
                if ports:
                    port_list = []
                    for port, bindings in ports.items():
                        if bindings:
                            for binding in bindings:
                                port_list.append(f"{binding['HostPort']}→{port}")
                    if port_list:
                        st.write(f"**Ports:** {', '.join(port_list)}")

            with col2:
                if container.status == "running":
                    st.button(
                        "🔄 Restart",
                        key=f"restart_{container.id}",
                        use_container_width=True,
                        on_click=restart_container,
                        args=(container.id,)
                    )
                    st.button(
                        "ℹ️ More Info",
                        key=f"info_{container.id}",
                        use_container_width=True,
                        on_click=show_container_info,
                        args=(container.id,)
                    )
                else:
                    st.button(
                        "▶️ Start",
                        key=f"start_{container.id}",
                        use_container_width=True,
                        on_click=start_container,
                        args=(container.id,)
                    )
            
            # Show detailed info if requested
            if st.session_state.get(f"show_info_{container.id}", False):
                st.divider()
                st.subheader("📊 Detailed Information")
                
                # Container stats (only for running containers)
                if container.status == "running":
                    try:
                        stats = container.stats(stream=False)
                        
                        # CPU Usage
                        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                        cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0 if system_delta > 0 else 0.0
                        
                        # Memory Usage
                        mem_usage = stats['memory_stats'].get('usage', 0)
                        mem_limit = stats['memory_stats'].get('limit', 1)
                        mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit > 0 else 0.0
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("CPU Usage", f"{cpu_percent:.2f}%")
                            st.metric("Memory Usage", f"{mem_usage / (1024**2):.1f} MB")
                        with col_b:
                            st.metric("Memory %", f"{mem_percent:.2f}%")
                            st.metric("Memory Limit", f"{mem_limit / (1024**2):.1f} MB")
                    except Exception as e:
                        st.warning(f"Could not fetch stats: {e}")
                
                # Environment variables
                env_vars = container.attrs['Config'].get('Env', [])
                if env_vars:
                    with st.expander("🔐 Environment Variables", expanded=False):
                        for env in sorted(env_vars):
                            st.code(env, language="bash")
                
                # Mounts/Volumes
                mounts = container.attrs.get('Mounts', [])
                if mounts:
                    with st.expander("💾 Volumes & Mounts", expanded=False):
                        for mount in mounts:
                            st.write(f"**Type:** {mount['Type']}")
                            if mount['Type'] == 'bind':
                                st.write(f"**Source:** `{mount['Source']}`")
                            elif mount['Type'] == 'volume':
                                st.write(f"**Volume:** `{mount['Name']}`")
                            st.write(f"**Destination:** `{mount['Destination']}`")
                            st.write(f"**Mode:** {mount.get('Mode', 'rw')}")
                            st.divider()
                
                # Networks
                networks = container.attrs['NetworkSettings'].get('Networks', {})
                if networks:
                    with st.expander("🌐 Networks", expanded=False):
                        for net_name, net_info in networks.items():
                            st.write(f"**Network:** {net_name}")
                            st.write(f"**IP Address:** {net_info.get('IPAddress', 'N/A')}")
                            st.write(f"**Gateway:** {net_info.get('Gateway', 'N/A')}")
                            st.divider()
                
                # Labels
                labels = container.labels
                if labels:
                    with st.expander("🏷️ Labels", expanded=False):
                        for key, value in sorted(labels.items()):
                            st.write(f"**{key}:** `{value}`")

except Exception as e:
    st.error(f"Error: {e}")

