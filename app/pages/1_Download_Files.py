"""
Download Files from Containers
"""
import streamlit as st
import docker
import os

st.set_page_config(page_title="Download Files", page_icon="📥", layout="wide")

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

def format_size(bytes_size):
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

# Header
st.title("📥 Download Files from Containers")

# Get Docker client
client = get_docker_client()
if client is None:
    st.stop()

# Get compose project for filtering
compose_project = get_compose_project()

try:
    # Get all containers
    all_containers = client.containers.list(all=True)

    # Filter containers by compose project
    if compose_project:
        containers = [c for c in all_containers
                     if c.labels.get('com.docker.compose.project') == compose_project]
    else:
        containers = all_containers

    if not containers:
        st.warning("No containers found.")
        st.stop()

    # Filter only running containers for file operations
    running_containers = [c for c in containers if c.status == "running"]

    if not running_containers:
        st.warning("No running containers found. Containers must be running to download files.")
        st.stop()

    # Container selection
    container_names = [c.name for c in running_containers]
    selected_name = st.selectbox("Select Container", container_names)
    selected_container = next(c for c in running_containers if c.name == selected_name)

    st.divider()

    # Path input
    if 'download_path' not in st.session_state:
        st.session_state.download_path = "/home"

    col1, col2 = st.columns([3, 1])
    with col1:
        current_path = st.text_input("Browse Path", value=st.session_state.download_path)
        st.session_state.download_path = current_path

    with col2:
        if st.button("📁 List Directory", use_container_width=True):
            st.rerun()

    # List directory contents
    st.subheader("Directory Contents")
    files = []
    try:
        exec_result = selected_container.exec_run(f'ls -lahp {current_path}')
        if exec_result.exit_code == 0:
            st.code(exec_result.output.decode('utf-8'), language="bash")
            
            # Get file list for dropdown
            for line in exec_result.output.decode('utf-8').splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 9:
                    name = parts[8]
                    if not name.endswith('/'):
                        files.append(name)
            
        else:
            st.error(f"Error: {exec_result.output.decode('utf-8')}")
    except Exception as e:
        st.error(f"Cannot list directory: {e}")

    st.divider()

    # Quick navigation
    st.subheader("Quick Navigation")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("📁 /home", use_container_width=True):
            st.session_state.download_path = "/home"
            st.rerun()
    with col2:
        if st.button("📁 /tmp", use_container_width=True):
            st.session_state.download_path = "/tmp"
            st.rerun()
    with col3:
        if st.button("📁 /var/log", use_container_width=True):
            st.session_state.download_path = "/var/log"
            st.rerun()
    with col4:
        if st.button("📁 /etc", use_container_width=True):
            st.session_state.download_path = "/etc"
            st.rerun()
    with col5:
        if st.button("📁 /app", use_container_width=True):
            st.session_state.download_path = "/app"
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

                    st.success(f"Archive created! Size: {format_size(len(tar_data))}")
                    st.download_button(
                        label="⬇️ Download Archive",
                        data=tar_data,
                        file_name=f"{archive_name}.tar",
                        mime="application/x-tar"
                    )
                except docker.errors.NotFound:
                    st.error(f"Path not found: {download_path}")
                except Exception as e:
                    st.error(f"Error: {e}")



    # Download a specific file directly (not as archive)
    st.subheader("📄 Download Individual File")
    
    if files:
        # File selection dropdown
        selected_file_name = st.selectbox(
            "Select a file to download",
            options=[""] + sorted(files),
            help="Choose the file you want to download"
        )
        
        if selected_file_name:
            # Construct full path
            selected_file_path = os.path.join(current_path, selected_file_name)
            
            # Show file info
            st.write(f"**Selected:** `{selected_file_path}`")
            
            # Try to get file size
            try:
                size_result = selected_container.exec_run(f"stat -c %s '{selected_file_path}'")
                if size_result.exit_code == 0:
                    size_bytes = int(size_result.output.decode('utf-8').strip())
                    st.write(f"**Size:** {format_size(size_bytes)}")
            except:
                pass
            
            # Download button
            if st.button("⬇️ Download File", type="primary", use_container_width=True, key="download_btn"):
                with st.spinner("Downloading file..."):
                    try:
                        # Get the file as archive and extract the content
                        bits, stat = selected_container.get_archive(selected_file_path)
                        tar_data = b''.join(bits)
                        
                        # Extract file content from tar
                        import tarfile
                        import io
                        
                        tar_buffer = io.BytesIO(tar_data)
                        with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
                            members = tar.getmembers()
                            if members:
                                file_member = members[0]
                                if file_member.isfile():
                                    file_data = tar.extractfile(file_member).read()
                                    
                                    st.session_state["download_data"] = file_data
                                    st.session_state["download_filename"] = selected_file_name
                                    st.success(f"✅ File ready for download: {selected_file_name}")
                                else:
                                    st.error("Selected item is not a file")
                            else:
                                st.error("No files found in archive")
                    except Exception as e:
                        st.error(f"Failed to download file: {e}")
            
            # Show download button if file is ready
            if "download_data" in st.session_state and "download_filename" in st.session_state:
                st.download_button(
                    label=f"💾 Save {st.session_state['download_filename']}",
                    data=st.session_state["download_data"],
                    file_name=st.session_state["download_filename"],
                    mime="application/octet-stream",
                    use_container_width=True
                )
                
                # Clear button
                if st.button("🗑️ Clear", help="Clear the download buffer"):
                    del st.session_state["download_data"]
                    del st.session_state["download_filename"]
                    st.rerun()
    else:
        st.info("No files found in current directory")
    

except Exception as e:
    st.error(f"Error: {e}")
