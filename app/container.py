"""
Utilities to convert streamlit extracted parameters to docker parameters
and create a DockerEnvironment instance.
"""

from swe_lib.environment import docker_env

def convert_mount_to_docker_mount(mount):
    from docker.types import Mount
    # mount is a dict with source, target, type, read_only

    print("Loading a mount:")
    tx = mount.get("type", "bind")
    if tx == "bind":
        bdx = mount.get("bind_propagation", None)
        if bdx == "None":
            bdx = None 

        return Mount(source=mount["local_path"], 
                    target=mount["container_path"], 
                    type="bind", 
                    read_only=mount.get("read_only", False), 
                    consistency=mount.get("consistency", "default"), 
                    propagation=bdx, # Only valid for type bind
                    )  
    
    elif tx == "volume":
        return Mount(source=mount["local_path"], 
                    target=mount["container_path"], 
                    type="volume",
                    read_only=mount.get("read_only", False), 
                    consistency=mount.get("consistency", "default"), 
                    no_copy=mount.get("no_copy", False), # Only valid for type volume
                    labels=mount.get("labels", None) # Only valid for type volume
                    )  
    else:
        return Mount(source=mount["local_path"], 
                    target=mount["container_path"], 
                    type=mount.get("type", "tmpfs"), 
                    read_only=mount.get("read_only", False), 
                    consistency=mount.get("consistency", "default")
                    )


def convert_port_list_to_dict(port_lst):
    """No check is done on docker part.
    Only on the user/host part.
    """
    dic = {}
    for item in port_lst:
        d = item["docker"]
        u = item["local"]
        x = None

        if u is None:
            x = None
        elif ":" in u:
            a, b = u.split(":", 1)
            x = (a, int(b))
        elif u.isnumeric():
            x = int(u)
        else:
            # Set to none if not valid
            x = None
        
        if d not in dic:
            # 1. Create element
            dic[d] = x
        elif isinstance(dic[d], list):
            # 3. Add element to existing list
            dic[d].append(x)
        else:
            # 2. Convert element to list if several ports match
            dic[d] = [dic[d], x]



    return dic 

def create_container(timeout=120, ports={}, env={}, mounts=None, volumes=None):
    """
    Creates a DockerEnvironment instance with the specified image and working directory.
 
    :param timeout: Timeout for each command in seconds (not taken into account yet)
    :param env: Environment variable 
    :param mounts: List of mount object
    """
    print("Will connect to ports:")
    print(ports)
    # The histfile is loaded correctly, 
    # however, because of the weird config, history does not work.
    # We have done our custom config history, so logs are save
    #return docker.DockerEnvironment(image="python:3.11", cwd="/tmp", env={"HISTFILE": "/home/.bash_history"})
    return docker_env.DockerEnvironment(config={"image":"python:3.13", "cwd": "/tmp"}, 
                                        timeout=timeout, 
                                        env=env,
                                        ports=ports,
                                        mounts=mounts, 
                                        volumes=volumes
                                        )


def connect_to_existing_container(container_id):
    """
    Connect to an existing Docker container by its ID and return a DockerEnvironment-like object.
    
    :param container_id: The ID of the existing Docker container
    :return: DockerEnvironment instance connected to the existing container, or None if connection fails
    """
    import docker
    
    try:
        # Get Docker client
        client = docker.from_env()
        
        # Get the existing container
        container = client.containers.get(container_id)
        
        # Check if container is running
        container.reload()  # Refresh container state
        if container.status != 'running':
            print(f"Container {container_id[:12]} is not running (status: {container.status})")
            return None
        
        # Create a custom DockerEnvironment instance that connects to existing container
        # instead of creating a new one
        env_instance = ExistingDockerEnvironment(container)
        
        return env_instance
        
    except docker.errors.NotFound:
        print(f"Container {container_id} not found")
        return None
    except docker.errors.DockerException as e:
        print(f"Docker error while connecting to container {container_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error connecting to container {container_id}: {e}")
        return None


class ExistingDockerEnvironment(docker_env.DockerEnvironment):
    """
    A DockerEnvironment subclass that connects to an existing container
    instead of creating a new one.
    """
    
    def __init__(self, container):
        """
        Initialize with an existing Docker container.
        
        :param container: An existing docker.Container object
        """
        # Don't call parent __init__ to avoid creating a new container
        self.container = container
        self.container_id = container.id
        self.client = container.client
        
        # Set default config
        self.config = docker_env.DockerConfig(image="existing", cwd="/tmp")
        self.ports = {}
        self.env = {}
        self.mounts = []
        
        # Reload container to get latest state
        self.container.reload()
        
        print(f"Connected to existing container: {self.get_container_ID()}")
    
    def _start_container(self):
        """Override to prevent creating a new container."""
        # This method is called by parent __init__, but we don't need it
        # since we're connecting to an existing container
        pass
    
    def cleanup(self):
        """Override cleanup to not stop the container since we didn't create it."""
        print(f"Disconnecting from container: {self.container_id}")
        # Don't stop the container since we didn't create it
        return

