# INTERCEPT GitHub Actions Workflows

Automated build pipelines for INTERCEPT Docker containers and Raspberry Pi images.

## Workflows

### 1. Docker Build (`docker-build.yml`)

**Purpose:** Build and publish multi-architecture Docker containers

**Triggers:**
- Push to `main` branch
- New release/tag (`v*`)
- Manual workflow dispatch
- Pull requests (build only, no push)

**What it does:**
1. Builds Docker image for 3 platforms:
   - `linux/amd64` (x86_64 PCs, servers)
   - `linux/arm64` (Raspberry Pi 3/4/5 64-bit)
   - `linux/arm/v7` (Raspberry Pi 2/3/4 32-bit)

2. Pushes to two registries:
   - **Docker Hub:** `smittix/intercept:latest`
   - **GHCR:** `ghcr.io/smittix/intercept:latest`

3. Tags images with:
   - `latest` (main branch)
   - Semantic version (`v1.2.3`, `v1.2`, `v1`)
   - Branch name (`main-sha123456`)
   - Git SHA

4. Tests container:
   - Starts container
   - Checks health endpoint
   - Validates stability

**Secrets required:**
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token

**Manual run:**
```bash
# Via GitHub UI:
Actions → Build and Push Docker Images → Run workflow

# Or via gh CLI:
gh workflow run docker-build.yml
```

---

### 2. Raspberry Pi Image (`build-rpi-image.yml`)

**Purpose:** Build pre-configured Raspberry Pi OS images with INTERCEPT

**Triggers:**
- Monthly schedule (1st of month, 03:00 UTC)
- Push to `main` branch
- New release/tag (`v*`)
- Manual workflow dispatch

**What it does:**
1. Downloads Raspberry Pi OS Lite (latest)
2. Expands image (+2GB for Docker)
3. Installs in chroot:
   - Docker + Docker Compose
   - INTERCEPT repository at `/opt/intercept`
   - CLI management tools
   - Systemd services (auto-start)
   - RTL-SDR kernel blacklists
4. Configures first-boot service:
   - Pulls Docker containers
   - Starts INTERCEPT
5. Compresses image (xz)
6. Uploads to GitHub Releases

**Output:**
- `intercept-rpi-{version}.img.xz` (~1.5-2GB compressed)
- SHA256 checksum file
- GitHub Release with installation instructions

**Manual run:**
```bash
# Via GitHub UI (with options):
Actions → Build Raspberry Pi Image → Run workflow
  ↳ Raspberry Pi OS version: 2024-11-19

# Or via gh CLI:
gh workflow run build-rpi-image.yml
```

**Image features:**
- SSH enabled by default
- Docker pre-installed
- Auto-start on boot
- WiFi hotspot fallback (if no network)
- All management scripts (`intercept-up`, `intercept-down`, etc.)

---

## Workflow Architecture

```
┌─────────────────────────────────────┐
│  Push to main / Create tag          │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼─────────────┐
│ Docker Build│  │ RPi Image Build    │
│             │  │                    │
│ Multi-arch  │  │ 1. DL RPi OS       │
│ Containers  │  │ 2. Install Docker  │
│             │  │ 3. Add INTERCEPT   │
│ Push to:    │  │ 4. Compress        │
│ - Docker Hub│  │ 5. Release         │
│ - GHCR      │  │                    │
└─────────────┘  └────────────────────┘
       │                │
       │                │
       ▼                ▼
┌─────────────────────────────────────┐
│    GitHub Releases                  │
│                                     │
│ - Docker images (auto)              │
│ - RPi .img.xz files                 │
│ - Checksums                         │
│ - Release notes                     │
└─────────────────────────────────────┘
```

---

## Setup Instructions

### Docker Hub Configuration

1. Create Docker Hub account: https://hub.docker.com
2. Create access token:
   - Account Settings → Security → New Access Token
   - Permissions: Read, Write, Delete
3. Add GitHub secrets:
   ```
   DOCKERHUB_USERNAME=your-username
   DOCKERHUB_TOKEN=your-access-token
   ```

### GitHub Container Registry (GHCR)

**No configuration needed!** Uses automatic `GITHUB_TOKEN` with package write permissions.

### Testing Locally

**Docker build:**
```bash
# Test multi-arch build
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t intercept:test .

# Test single platform
docker build -t intercept:test .
docker run -p 5050:5050 intercept:test
```

**RPi image build:**
```bash
# Requires Linux with loop device support
# Not recommended locally (complex, requires chroot)
# Use GitHub Actions instead
```

---

## Monitoring Builds

**GitHub Actions UI:**
```
Repository → Actions → Select workflow → View runs
```

**Notifications:**
- Email notifications for failed builds (repo admin)
- GitHub notifications for completed workflows

**Logs:**
- Available for 90 days
- Download via Actions UI
- Or via `gh` CLI:
  ```bash
  gh run list
  gh run view <run-id> --log
  ```

---

## Release Process

### Manual Release

1. Create and push tag:
   ```bash
   git tag -a v3.0.0 -m "Release v3.0.0"
   git push origin v3.0.0
   ```

2. Workflows trigger automatically:
   - Docker images build and push
   - RPi image builds and attaches to release

3. Create GitHub Release (optional):
   ```bash
   gh release create v3.0.0 --generate-notes
   ```

### Automated Release

1. GitHub Release created via UI or API
2. Workflows trigger on `release: published`
3. Artifacts automatically attached

---

## Troubleshooting

### Docker build fails

**Check:**
- Dockerfile syntax
- Base image availability
- Docker Hub credentials in secrets

**Common issues:**
- Rate limit on Docker Hub pulls (use GHCR as fallback)
- Multi-arch build timeout (increase workflow timeout)

**Fix:**
```bash
# Test locally first
docker build --no-cache -t intercept:test .
```

### RPi image build fails

**Check:**
- Loop device support on runner
- Chroot operations (requires root)
- Raspberry Pi OS availability

**Common issues:**
- Download timeout (retry automatic)
- Loop device busy (cleanup in `if: always()`)
- Out of disk space (increase runner disk)

**Logs:**
```bash
gh run view <run-id> --log | grep -i error
```

### Image too large

**Docker:**
- Multi-stage build already optimized
- Check for unnecessary `apt install` packages
- Remove build tools after compilation

**RPi:**
- Current: ~1.5-2GB compressed (good)
- If larger: Check for leftover temp files
- Cleanup in chroot script

---

## Performance

### Build Times

| Workflow | Duration | Notes |
|----------|----------|-------|
| Docker build | ~15-25 min | Multi-arch, 3 platforms |
| RPi image | ~20-30 min | Download + chroot + compress |

### Artifact Sizes

| Artifact | Size | Compressed |
|----------|------|------------|
| Docker image (amd64) | ~800MB | N/A (registry) |
| Docker image (arm64) | ~800MB | N/A (registry) |
| Docker image (armv7) | ~800MB | N/A (registry) |
| RPi image | ~4GB | ~1.5GB (.xz) |

### Rate Limits

- **Docker Hub:** 100 pulls/6h (anonymous), 200 pulls/6h (authenticated)
- **GHCR:** No rate limits for public repos
- **GitHub Actions:** 2000 min/month (free), 3000 min/month (Pro)

---

## Future Enhancements

- [ ] Nightly builds for testing
- [ ] ARM64 RPi OS variant (64-bit native)
- [ ] Multi-board support (Orange Pi, etc.)
- [ ] Automated vulnerability scanning
- [ ] Container signing (cosign)
- [ ] SBOM generation
- [ ] Release notes automation
- [ ] Changelog generation from commits

---

## Links

- [Docker Hub Repository](https://hub.docker.com/r/smittix/intercept)
- [GitHub Container Registry](https://github.com/smittix/intercept/pkgs/container/intercept)
- [GitHub Releases](https://github.com/smittix/intercept/releases)
- [Actions Documentation](https://docs.github.com/en/actions)
