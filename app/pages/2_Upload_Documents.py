"""
Upload Documents to Shared Volume
"""
import streamlit as st
import os
import tempfile

st.set_page_config(page_title="Upload Documents", page_icon="📤", layout="wide")

UPLOAD_DIR = "/shared_data"

def format_size(bytes_size):
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def check_directory_access(directory):
    """Check if directory exists and is accessible (readable and writable)."""
    if not os.path.exists(directory):
        return False, "Directory does not exist"
    
    if not os.path.isdir(directory):
        return False, "Path exists but is not a directory"
    
    if not os.access(directory, os.R_OK):
        return False, "Directory is not readable"
    
    if not os.access(directory, os.W_OK):
        return False, "Directory is not writable"
    
    # Try to actually write a test file to confirm write access
    try:
        test_file = os.path.join(directory, ".access_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return True, "Directory is accessible"
    except Exception as e:
        return False, f"Cannot write to directory: {str(e)}"

# Header
st.title("📤 Upload Documents")

st.write("Upload documents to the shared volume accessible by other containers.")

# Check directory access
is_accessible, access_message = check_directory_access(UPLOAD_DIR)

if not is_accessible:
    st.error(f"⚠️ Upload directory is not accessible: `{UPLOAD_DIR}`")
    st.error(f"Error: {access_message}")
    st.warning("""
    **Possible solutions:**
    - If running locally, create the directory: `mkdir -p /shared_data`
    - Ensure you have read/write permissions: `chmod 755 /shared_data`
    - Consider using a local directory like `./shared_data` instead
    - If running in Docker, ensure the volume is properly mounted
    """)
    st.stop()

st.success(f"✓ Upload directory accessible: `{UPLOAD_DIR}`")

# Ensure upload directory exists (should already exist if check passed, but just in case)
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception as e:
    st.error(f"Failed to create upload directory: {e}")
    st.stop()

st.divider()

# File uploader
st.subheader("Upload Files")

uploaded_files = st.file_uploader(
    "Choose files to upload",
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("📤 Upload Files", type="primary"):
        for uploaded_file in uploaded_files:
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Uploaded: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error uploading {uploaded_file.name}: {e}")
        st.rerun()

st.divider()

# List uploaded files
st.subheader("📁 Uploaded Files")

files = []
try:
    files = [f for f in os.listdir(UPLOAD_DIR) if not f.startswith('.')]
except Exception as e:
    st.error(f"Error listing files: {e}")

if files:
    for file in sorted(files):
        file_path = os.path.join(UPLOAD_DIR, file)
        try:
            file_size = os.path.getsize(file_path)

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 **{file}**")
            with col2:
                st.write(f"{format_size(file_size)}")
            with col3:
                if st.button("🗑️ Delete", key=f"del_{file}"):
                    try:
                        os.remove(file_path)
                        st.success(f"Deleted: {file}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting {file}: {e}")
        except Exception as e:
            st.warning(f"Error reading {file}: {e}")
else:
    st.info("No files uploaded yet.")

st.divider()

# Additional info
with st.expander("ℹ️ Information"):
    st.write("""
    **About Shared Volume:**
    - Files uploaded here are stored in the `shared_data` Docker volume
    - This volume is shared with other containers in the same docker-compose project
    - The `data-container` (nginx) serves these files at http://localhost:8080
    - Other containers can access files at `/usr/share/nginx/html` or their configured mount point
    """)
