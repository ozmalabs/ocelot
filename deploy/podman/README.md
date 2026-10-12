# Run the Ocelot API with rootless Podman

This setup builds the Rust `substrate_rs` extension from the checked-out source,
boots the validated connected conversation seed profile, and runs the
authenticated OpenAI-compatible API as an unprivileged container user. The
Quadlet publishes the API only on host loopback and persists namespace data in
`~/.local/share/ocelot-api`.

## Build the image

From the repository root:

```sh
podman build --pull=always -f deploy/podman/Containerfile \
  -t localhost/ocelot-api:local .
```

The root `.containerignore` keeps local corpora, model weights, Git data,
virtual environments, and runtime output out of the build context. Cargo
downloads the crate dependencies during the build, so the builder needs network
access. Rebuild the image after updating Ocelot or the Rust substrate source.

## Configure a bearer token

```sh
mkdir -p ~/.config
install -d -m 700 ~/.local/share/ocelot-api
install -m 600 deploy/podman/ocelot-api.env.example ~/.config/ocelot-api.env
```

Edit `~/.config/ocelot-api.env` and replace the sample token with a long random
secret mapped to a stable principal ID. The env file is read by the rootless
Quadlet service and is not copied into the image.

## Install and start the user service

```sh
install -d -m 700 ~/.config/containers/systemd
install -m 600 deploy/podman/ocelot-api.container \
  ~/.config/containers/systemd/ocelot-api.container
systemctl --user daemon-reload
systemctl --user start ocelot-api.service
```

The Quadlet's `[Install]` section wires the generated service to the user
default target. For it to continue running after logout and start at boot,
enable user lingering once with `loginctl enable-linger "$USER"`.

Check readiness and logs:

```sh
curl --fail http://127.0.0.1:8790/health
journalctl --user -u ocelot-api.service -f
```

The systemd unit can become active as soon as Podman starts the container,
before Ocelot has finished loading its seed profile. Treat the `/health`
response as readiness; the Quadlet health check restarts the container if it
does not become healthy or later stops responding.

The Quadlet binds the process to all interfaces inside its private container
network while Podman publishes only `127.0.0.1:8790` on the host. Keep that
loopback publish setting unless access is protected by a trusted TLS proxy and
network policy. The API requires bearer authentication for all `/v1` routes.

An OpenAI client can use `http://127.0.0.1:8790/v1` as its `base_url` and the
configured token as `api_key`. Session fork and clear routes are documented in
[`../../features/OPENAI_COMPATIBLE_COW_API.md`](../../features/OPENAI_COMPATIBLE_COW_API.md).

## Update and stop

After rebuilding the image, restart the service so Podman replaces the running
container with the locally tagged image:

```sh
systemctl --user restart ocelot-api.service
```

Stop it with `systemctl --user stop ocelot-api.service`. To remove the service,
delete `~/.config/containers/systemd/ocelot-api.container` and run
`systemctl --user daemon-reload`. User services stop when the account logs out
unless lingering is enabled with `loginctl enable-linger "$USER"`.
