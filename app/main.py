import streamlit as st
import os
import tarfile
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import psutil

st.set_page_config(page_title="Container Manager", page_icon="🐳", layout="wide")

st.title("🐳 Docker Container Manager")

# Sidebar for navigation
page = st.sidebar.selectbox("Select Page", ["Container Info", "File Manager"])

if page == "Container Info":
    st.header("📊 Container Information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("System Info")

        # Hostname
        hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()
        st.metric("Hostname", hostname)

        # Uptime
        try:
            uptime_output = subprocess.run(['uptime', '-p'], capture_output=True, text=True).stdout.strip()
            st.metric("Uptime", uptime_output)
        except:
            st.metric("Uptime", "N/A")

        # Current User
        current_user = os.getenv('USER', 'unknown')
        st.metric("Current User", current_user)

        # Python Version
        import sys
        st.metric("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    with col2:
        st.subheader("Resources")

        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        st.metric("CPU Usage", f"{cpu_percent}%")

        # Memory Usage
        memory = psutil.virtual_memory()
        st.metric("Memory Usage", f"{memory.percent}%",
                 delta=f"{memory.used / (1024**3):.2f}GB / {memory.total / (1024**3):.2f}GB")

        # Disk Usage
        disk = psutil.disk_usage('/')
        st.metric("Disk Usage", f"{disk.percent}%",
                 delta=f"{disk.used / (1024**3):.2f}GB / {disk.total / (1024**3):.2f}GB")

    st.divider()

    # Environment Variables
    with st.expander("🔐 Environment Variables"):
        env_vars = dict(os.environ)
        # Hide sensitive info
        sensitive_keys = ['API_KEY', 'PASSWORD', 'SECRET', 'TOKEN', 'ANTHROPIC']
        for key, value in sorted(env_vars.items()):
            if any(s in key.upper() for s in sensitive_keys):
                st.text(f"{key} = ***HIDDEN***")
            else:
                st.text(f"{key} = {value}")

    # Process List
    with st.expander("⚙️ Running Processes"):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        st.dataframe(processes, use_container_width=True)

elif page == "File Manager":
    st.header("📁 File Manager & Downloader")

    # Directory browser
    st.subheader("Browse Directory")

    # Get home directory
    home_dir = os.path.expanduser("~")

    # Directory input
    current_dir = st.text_input("Current Directory", value=home_dir, key="dir_input")

    if os.path.exists(current_dir) and os.path.isdir(current_dir):
        # List contents
        try:
            items = []
            for item in sorted(os.listdir(current_dir)):
                item_path = os.path.join(current_dir, item)
                try:
                    stat = os.stat(item_path)
                    is_dir = os.path.isdir(item_path)
                    size = stat.st_size if not is_dir else 0
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                    items.append({
                        'Name': f"📁 {item}" if is_dir else f"📄 {item}",
                        'Type': 'Directory' if is_dir else 'File',
                        'Size': f"{size / 1024:.2f} KB" if not is_dir else "-",
                        'Modified': modified,
                        'Path': item_path
                    })
                except (PermissionError, OSError):
                    continue

            if items:
                st.dataframe(items, use_container_width=True, hide_index=True)
            else:
                st.info("Empty directory")

        except PermissionError:
            st.error("❌ Permission denied to access this directory")
    else:
        st.error("❌ Directory does not exist")

    st.divider()

    # Download section
    st.subheader("📦 Download Files/Folders")

    download_path = st.text_input("Path to Download (file or folder)", value=home_dir)
    archive_name = st.text_input("Archive Name (without extension)", value="download")

    col1, col2 = st.columns([1, 4])

    with col1:
        download_button = st.button("📥 Create Archive", type="primary")

    if download_button:
        if not os.path.exists(download_path):
            st.error("❌ Path does not exist!")
        else:
            with st.spinner("Creating archive..."):
                try:
                    # Create temporary tar file
                    temp_dir = tempfile.mkdtemp()
                    tar_filename = f"{archive_name}.tar.gz"
                    tar_path = os.path.join(temp_dir, tar_filename)

                    # Create tar archive
                    with tarfile.open(tar_path, "w:gz") as tar:
                        if os.path.isdir(download_path):
                            # Add entire directory
                            tar.add(download_path, arcname=os.path.basename(download_path))
                        else:
                            # Add single file
                            tar.add(download_path, arcname=os.path.basename(download_path))

                    # Read the tar file
                    with open(tar_path, "rb") as f:
                        tar_data = f.read()

                    # Cleanup temp directory
                    shutil.rmtree(temp_dir)

                    # Provide download button
                    st.success(f"✅ Archive created successfully! Size: {len(tar_data) / 1024:.2f} KB")
                    st.download_button(
                        label="⬇️ Download Archive",
                        data=tar_data,
                        file_name=tar_filename,
                        mime="application/gzip"
                    )

                except Exception as e:
                    st.error(f"❌ Error creating archive: {str(e)}")

    st.divider()

    # Quick actions
    st.subheader("⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📁 Download Home Directory"):
            st.session_state['download_path'] = home_dir
            st.rerun()

    with col2:
        if st.button("📁 Download /tmp"):
            st.session_state['download_path'] = "/tmp"
            st.rerun()

    with col3:
        if st.button("📁 Download Current Working Dir"):
            st.session_state['download_path'] = os.getcwd()
            st.rerun()

    # Handle session state for quick actions
    if 'download_path' in st.session_state:
        st.info(f"Selected: {st.session_state['download_path']}")
        del st.session_state['download_path']

# Footer
st.sidebar.divider()
st.sidebar.info("🐳 Container Manager v1.0")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
