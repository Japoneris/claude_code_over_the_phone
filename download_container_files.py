#!/usr/bin/env python3
"""
Docker Container File Manager

This script downloads files from or uploads files to Docker containers.
- Download: saves files in timestamped directories under data/
- Upload: pushes local files/folders to a specific location in the container
"""

import docker
import tarfile
import io
import os
import sys
from datetime import datetime
import argparse


def download_from_container(container_id, source_path, base_output_dir="data"):
    """
    Download files/folders from a Docker container
    
    Args:
        container_id: ID or name of the container
        source_path: Path to file/folder inside the container
        base_output_dir: Base directory to save downloaded files (default: data/)
    
    Returns:
        str: Path to the created directory with downloaded files
    """
    try:
        # Initialize Docker client
        client = docker.from_env()
        
        # Get the container
        try:
            container = client.containers.get(container_id)
        except docker.errors.NotFound:
            print(f"Error: Container '{container_id}' not found")
            return None
        except docker.errors.APIError as e:
            print(f"Error accessing container: {e}")
            return None

        output_dir = os.path.join(base_output_dir, container.name)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Downloading from container '{container.name}' ({container_id[:12]})")
        print(f"Source path: {source_path}")
        print(f"Destination: {output_dir}")
        
        # Get archive from container
        try:
            bits, stat = container.get_archive(source_path)
        except docker.errors.NotFound:
            print(f"Error: Path '{source_path}' not found in container")
            # Clean up empty directory
            os.rmdir(output_dir)
            return None
        except docker.errors.APIError as e:
            print(f"Error retrieving files: {e}")
            os.rmdir(output_dir)
            return None
        
        # Extract the tar archive
        tar_stream = io.BytesIO()
        for chunk in bits:
            tar_stream.write(chunk)
        tar_stream.seek(0)
        
        # Extract files
        with tarfile.open(fileobj=tar_stream) as tar:
            tar.extractall(path=output_dir)
        
        print(f"✓ Successfully downloaded to: {output_dir}")
        
        # Show what was downloaded
        downloaded_items = os.listdir(output_dir)
        print(f"Downloaded {len(downloaded_items)} item(s):")
        for item in downloaded_items:
            item_path = os.path.join(output_dir, item)
            if os.path.isdir(item_path):
                print(f"  📁 {item}/")
            else:
                size = os.path.getsize(item_path)
                print(f"  📄 {item} ({size} bytes)")
        
        return output_dir
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def upload_to_container(container_id, local_path, container_path):
    """
    Upload files/folders to a Docker container
    
    Args:
        container_id: ID or name of the container
        local_path: Path to local file/folder to upload
        container_path: Destination path inside the container
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize Docker client
        client = docker.from_env()
        
        # Get the container
        try:
            container = client.containers.get(container_id)
        except docker.errors.NotFound:
            print(f"Error: Container '{container_id}' not found")
            return False
        except docker.errors.APIError as e:
            print(f"Error accessing container: {e}")
            return False
        
        # Check if local path exists
        if not os.path.exists(local_path):
            print(f"Error: Local path '{local_path}' does not exist")
            return False
        
        print(f"Uploading to container '{container.name}' ({container_id[:12]})")
        print(f"Source: {local_path}")
        print(f"Destination: {container_path}")
        
        # Create tar archive from local path
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            # Get the base name to preserve structure
            arcname = os.path.basename(local_path)
            tar.add(local_path, arcname=arcname)
        
        tar_stream.seek(0)
        
        # Upload to container
        try:
            success = container.put_archive(container_path, tar_stream)
            if success:
                print(f"✓ Successfully uploaded to: {container_path}")
                
                # Show what was uploaded
                if os.path.isdir(local_path):
                    item_count = sum(1 for _ in os.walk(local_path))
                    print(f"Uploaded directory with {item_count} item(s)")
                else:
                    size = os.path.getsize(local_path)
                    print(f"Uploaded file: {os.path.basename(local_path)} ({size} bytes)")
                
                return True
            else:
                print("Upload failed")
                return False
                
        except docker.errors.APIError as e:
            print(f"Error uploading files: {e}")
            return False
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def list_containers():
    """List all running containers"""
    try:
        client = docker.from_env()
        containers = client.containers.list()
        
        if not containers:
            print("No running containers found")
            return
        
        print("\nRunning containers:")
        print("-" * 80)
        print(f"{'CONTAINER ID':<15} {'NAME':<30} {'STATUS':<20}")
        print("-" * 80)
        
        for container in containers:
            print(f"{container.id[:12]:<15} {container.name:<30} {container.status:<20}")
        print("-" * 80)
        
    except Exception as e:
        print(f"Error listing containers: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Download files from or upload files to Docker containers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a file from container
  %(prog)s download abc123 /app/config.json
  
  # Download a directory from container
  %(prog)s download my-container /var/log
  
  # Download with custom output directory
  %(prog)s download abc123 /app/data --output /backups
  
  # Upload a file to container
  %(prog)s upload abc123 ./myfile.txt /app/data/
  
  # Upload a directory to container
  %(prog)s upload my-container ./logs /var/log/
  
  # List running containers
  %(prog)s --list
        """
    )
    
    parser.add_argument(
        "action",
        nargs="?",
        choices=["download", "upload"],
        help="Action to perform: download or upload"
    )
    
    parser.add_argument(
        "container_id",
        nargs="?",
        help="Container ID or name"
    )
    
    parser.add_argument(
        "source_path",
        nargs="?",
        help="For download: path inside container; For upload: local path"
    )
    
    parser.add_argument(
        "dest_path",
        nargs="?",
        help="For upload: destination path inside container (required for upload)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="data",
        help="Base output directory for downloads (default: data/)"
    )
    
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List all running containers"
    )
    
    args = parser.parse_args()
    
    # List containers if requested
    if args.list:
        list_containers()
        return 0
    
    # Validate action is provided
    if not args.action:
        parser.print_help()
        print("\nError: Please specify an action (download or upload) or use --list")
        return 1
    
    # Validate required arguments for download
    if args.action == "download":
        if not args.container_id or not args.source_path:
            parser.print_help()
            print("\nError: download requires container_id and source_path")
            return 1
        
        result = download_from_container(
            args.container_id,
            args.source_path,
            args.output
        )
        return 0 if result else 1
    
    # Validate required arguments for upload
    elif args.action == "upload":
        if not args.container_id or not args.source_path or not args.dest_path:
            parser.print_help()
            print("\nError: upload requires container_id, source_path (local), and dest_path (container)")
            return 1
        
        result = upload_to_container(
            args.container_id,
            args.source_path,
            args.dest_path
        )
        return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
