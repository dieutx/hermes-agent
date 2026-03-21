---
name: docker-management
description: Docker container and image management — build, run, debug, compose, and troubleshoot containerized applications
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [Docker, containers, DevOps, compose, debugging, infrastructure]
    related_skills: [systematic-debugging, plan]
    homepage: https://docs.docker.com
  prerequisites:
    commands: [docker]
---

# Docker Management

Use this skill when working with Docker containers, images, Compose stacks, or troubleshooting container issues.

## Capabilities

### Container Operations
- List, start, stop, restart, remove containers
- Inspect container state, logs, resource usage
- Execute commands inside running containers
- Attach to container processes for debugging

### Image Management
- Build images from Dockerfiles
- List, tag, push, pull images
- Inspect image layers and history
- Clean up dangling/unused images

### Docker Compose
- Start/stop multi-container applications
- View service logs across the stack
- Scale services up/down
- Validate compose files

### Troubleshooting
- Diagnose container crashes (exit codes, OOM kills)
- Debug networking issues between containers
- Inspect volume mounts and permissions
- Check resource constraints (memory, CPU limits)

## Common Workflows

### Debug a Crashing Container
```bash
# Check recent exit code and state
docker inspect <container> --format='{{.State.ExitCode}} {{.State.OOMKilled}} {{.State.Error}}'

# View last logs before crash
docker logs --tail 100 <container>

# Check events for OOM or restarts
docker events --since 1h --filter container=<container>

# Run interactively to reproduce
docker run -it --entrypoint sh <image>
```

### Analyze Disk Usage
```bash
# Overview of Docker disk usage
docker system df -v

# Find large images
docker images --format '{{.Size}}\t{{.Repository}}:{{.Tag}}' | sort -hr | head -20

# Clean up safely
docker system prune --volumes  # removes stopped containers, unused networks, dangling images, unused volumes
```

### Debug Container Networking
```bash
# List networks and connected containers
docker network ls
docker network inspect <network>

# Test connectivity from inside a container
docker exec <container> ping <other-container>
docker exec <container> nslookup <service-name>

# Check exposed ports
docker port <container>
```

### Compose Stack Management
```bash
# Start stack with build
docker compose up -d --build

# View logs for specific service
docker compose logs -f --tail 50 <service>

# Check health status of all services
docker compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'

# Restart a single service without touching others
docker compose restart <service>
```

## Best Practices

1. **Always check logs before restarting** — blind restarts hide root causes
2. **Use `--tail` with logs** — avoid dumping gigabytes of log output
3. **Prefer `docker compose` over `docker-compose`** — the latter is deprecated
4. **Use `docker system prune` carefully** — add `--filter` to avoid removing needed resources
5. **Check exit codes** — 137 = OOM killed, 143 = SIGTERM, 1 = application error
6. **Use health checks** in Dockerfiles and Compose files for automatic recovery

## Exit Code Reference

| Code | Meaning |
|------|---------|
| 0 | Clean exit |
| 1 | Application error |
| 125 | Docker daemon error |
| 126 | Command cannot execute |
| 127 | Command not found |
| 137 | SIGKILL (OOM or `docker kill`) |
| 143 | SIGTERM (graceful stop) |
| 255 | Exit status out of range |
