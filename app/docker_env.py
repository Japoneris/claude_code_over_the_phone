"""Try to reproduce the docker class in previous SWE script

The goal is to make it easier to manage / less copy past of subprocess.out
"""
import os
import time 
import uuid

from dataclasses import dataclass, field

import docker


from swe_lib.environment import tar_tools
from swe_lib.environment.base_env import BaseEnvironment

default_env = {
    "image": "python:3.13",
    "cwd": "/tmp"
}

@dataclass
class DockerConfig:
    image: str = "python:3.13"
    cwd: str = "/tmp"
    timeout: int = 120
    


class DockerEnvironment(BaseEnvironment):

    def __init__(self, config: dict = default_env, ports={}, env={}, mounts: list = [], *args, **kwds):
        self.container_id: str | None = None
        self.config = DockerConfig(**config)
        self.ports = ports
        self.env = env
        self.mounts = mounts
        self._start_container()
        #self.timeout = 100 # Only for execution

    def _start_container(self):
        # Client is here to interact with docker
        container_name = f"minisweagent2-{uuid.uuid4().hex[:8]}"

        self.client = docker.from_env()
        self.container = self.client.containers.run(
            self.config.image,
            name=container_name,
            detach=True,
            tty=True,
            #timeout=100,
            environment=self.env,
            ports=self.ports,
            mounts=self.mounts,
            working_dir=self.config.cwd,
            #**self.config
        )
        self.container_id = self.container.id

        print("DEBUG:")
        print("Before", self.container.ports)
        # RELOAD is necessary to apply ports mapping
        self.container.reload() 
        print("After", self.container.ports)
        return 
    
    def get_port_config(self):
        return self.container.ports

    def get_container_ID(self, length=12):
        """The container full ID is very long.
        In practice, docker command only use the 12 first characters
        """
        return self.container_id[:length]

    def execute(self, command: str, *args, **kwargs):
        """Execute a command in the Docker container."""
        return self._execute(command, *args, **kwargs)

    def _execute(self, command: str, *args, **kwargs):
        # API to call
        """Execute a command in the Docker container."""
        
        answer = self.container.exec_run(f"bash -lc '{command}'", *args, **kwargs)
        # TODO: decode and get output codes
        return {"returncode": answer.exit_code, "output": answer.output.decode("utf-8", errors="replace")}


    def update_env_variables(self, env_vars: dict):
        """Update environment variables in the Docker container."""
        for key, value in env_vars.items():
            self.container.exec_run(f"bash -lc 'export {key}={value}'")

        return

    def save_command(self, command: str, timestamp: int=None):
        """Here, save it with the normal history format.
        """
        return  self._execute(f"bash -lc 'echo {command} >> /home/.bash_history'")
    
    #def save_command_output(self, command: str, output: str, timestamp: int=None):

    def download_files(self, save_folder=None):
        """
        Get files from the current directory
        
        :param save_folder: Where to save the downloaded files. If None, returns raw data directly
        """

        pwd = self.execute("pwd")["output"].strip() # Strip necessary
        #print("Downloading files from: `{}`".format(pwd))

        # Create zip using all elements
        bits, stats = self.container.get_archive(pwd)

        if save_folder is not None:            
            ID = self.get_container_ID() 

            with open(f"{save_folder}/{ID}_{pwd.replace("/", "::")}.tar", "wb") as f:
                for data in bits:
                    f.write(data)

        return bits, stats 
    
    def copy_file_to_container(self, local_path: str, container_path: str):
        """Will copy and decompress a tar archive to docker

        :param local_path: path to tar file on the host.
        :param container_path: where the archive will be decompressed
        """
        with open(local_path, "rb") as f:
            self.container.put_archive(container_path, f)

        return {"returncode": 0, 'output': ''}

    def __del__(self):
        self.cleanup()
        return
    
    def cleanup(self):
        print("Stopping container: {}".format(self.container_id))
        self.container.stop(timeout=10)
        print("Done !")
        return
    



    # FX for str_tools
    def exists(self, path: str) -> bool:
        """Check if a path (file or directory) exists in the Docker container.
        
        :param path: Path to check
        :return: True if path exists, False otherwise
        """
        return self._execute(f"test -e '{path}'")["returncode"] == 0

    def is_directory(self, path: str) -> bool:
        # Implement Docker-specific directory checking logic
        # Check if bracket OK arond path
        return self._execute(f"test -d '{path}'")["returncode"] == 0

    def write_file(self, path: str, content: str):
        """Write file in a docker.

        1. Save the content to a regular file
        2. Compress it as a tar archive
        3. Send the archive to the docker container (auto decompress)
        4. Rename the document


        :param path: location in the docker file
        :param content: what to write in the file
        """
        # TODO: TOTEST

        #directory, filename = os.path.split(path)
        
        # Save content to temporary file
        t = int(time.time())
        tmp_file = f"tmpfile-{t}.tmp"
        with open(tmp_file, "w") as fp:
            fp.write(content)

        # Create archive that can be sent to docker container
        tar_name = tar_tools.create_tar_from_filename(tmp_file)
        # File is not necessary anymore 
        os.remove(tmp_file)

        # Send the archive to the docker container
        # The docker API should only push into directory (not as filename)

        # Always move to /tmp directory
        # Because name is random, should be fine before renaming
        res = self.copy_file_to_container(tar_name, "/tmp") 
        


        # Delete archive
        os.remove(tar_name)

        self.execute(f"mv /tmp/{tmp_file} {path}")

        return res


    def read_file(self, path: str):
        # Implement Docker-specific file reading logic
        result = self._execute(f"cat {path}")
        return result["output"]

    def view_directory(self, path: str):
        """List the contents of a directory in the Docker container."""
        return self._execute(f"ls -la {path}")["output"]
    
