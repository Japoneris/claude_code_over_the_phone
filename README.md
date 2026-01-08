# Claude Code over your Phone

## Goal

Interact with Claude Code on your smartphone with minimal configuration.

## Why?

My phone in an Android 16.

- I cannot install Termux as it is deprecated + OS prevents me from installing
- In developper mode, I do not have access to the Linux terminal ...

So, I have no way to get a shell on my phone

## Inspiration Sources

This first week of 2026, I found two articles on HackerNews, which have similar goals, but not the same config:

- [Claude Code on the go](https://granda.org/en/2026/01/02/claude-code-on-the-go/)
- [Doom Coding](https://github.com/rberg27/doom-coding)

Both use [Tailscale](https://tailscale.com) as a way to connect their phone to a VM/computer

## The Way it Works

### Setup the Docker 

1. Create an .env file with the `ANTROPIC_API_KEY` (adjust the docker compose if needed)
2. Run the docker compose

#### Useful Docker Commands

```sh
docker compose build # To build the containers
docker compose up -d # To run it, -d to get it on background
docker compose down # To stop it if it was on background
```

3. Go to [localhost:7681](http://127.0.0.1:7681/): You should get a terminal, and you can start with `claude`

Claude is installed by the docker, API key is also configured for you.

Now, claude can be run safely on your computer

### Accessing Claude Code from your Phone

Configure [Tailscale](https://tailscale.com/download) on both your phone and your computer.

When done, on the phone app, you should get the IP address of your computer / VM.
You can access the terminal using `<my_computer_ip_address>:7681`.

The first time, run claude in the main directory (`/home/terminal`) just to check everything is OK.
Then, create repo, run claude code, and build stuff!

## Other Features

- The docker compose has a volume that makes data persistant accross several sessions
- In the `app/` folder, there is a streamlit app, allowing you to collect data from your container.


# TODO

- [ ] Configure Tailscale so we connect directly to the container (not to the network of the computer)
- [ ] Configure the fontsize in the docker compose, not in the Dockerfile, so it is easier to modify
- [ ] Add a way to automatically configure git (using github, keybase, or other), so AI or you can push the code directly to a repo, without exporting manually

# Error you can get

- If you do some updates on the dockerfile or dockercompose, be aware that a volume is added. I will provide persistency. Remove it to be sure all data are reset.
- Ink problem: when running Claude, I got one config where it was impossible to run it, as I got a library issue. Environment variables in the docker compose should have fixed the issue.
- With the streamlit app, if the docker (python lib) version is incorrect, it will not work.

# Disclaimer

Made with AI.
Can contain errors