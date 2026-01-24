# ADSB Feeder Image Analysis - Sammenligning med ADSB.lol

> **Repository:** https://github.com/dirkhh/adsb-feeder-image/
> **Analyseret:** 2026-01-24
> **Formål:** Identificere bedste praksis for INTERCEPT container migration

---

## 🎯 Kort Oprids: dirkhh/adsb-feeder-image

### Kernekoncept
**"Turnkey Appliance" tilgang** - Pre-built SD card images der "bare virker" ud af boksen med omfattende web UI til konfiguration.

### Hovedarkitektur

```
┌────────────────────────────────────────────┐
│  DietPi / Raspbian Base OS (Minimal)       │
│  - Docker + Docker Compose pre-installed   │
│  - CustomPiOS build framework              │
└─────────────┬──────────────────────────────┘
              │
    ┌─────────┴──────────────────────┐
    │  Flask Web UI (Port 1099)      │
    │  /opt/adsb/adsb-setup/app.py   │
    │  - Setup wizard                │
    │  - SDR management              │
    │  - Aggregator configuration    │
    │  - One-click updates           │
    │  - Backup/restore              │
    └─────────┬──────────────────────┘
              │
    ┌─────────┴─────────────────────────────┐
    │  Docker Compose (24+ containers)      │
    │  - ultrafeeder (ADS-B aggregator)     │
    │  - dump978 (UAT)                      │
    │  - acarsdec/acarshub (ACARS)          │
    │  - dumpvdl2 (VDL Mode 2)              │
    │  - dumphfdl (HF Data Link)            │
    │  - shipfeeder (AIS)                   │
    │  - radiosonde (Weather balloons)      │
    │  - dozzle (Log viewer)                │
    │  - webproxy (Nginx reverse proxy)     │
    └───────────────────────────────────────┘
```

### Brugeroplevelse Flow

```
1. Download .img.xz fil (280-863 MB)
   ↓
2. Flash til SD kort med Raspberry Pi Imager
   ↓
3. Boot Raspberry Pi (3-9 min bootstrap)
   ↓
4a. Ethernet tilsluttet:
    → Browse til http://adsb-feeder.local:1099
   ↓
4b. Ingen netværk:
    → Auto WiFi hotspot "adsb-feeder-image"
    → Captive portal til WiFi setup
    → Reboot og forbind
   ↓
5. Web setup wizard:
    Step 1: Site navn, GPS koordinater
    Step 2: SDR detection og tildeling
    Step 3: Aggregator valg (checkboxes)
    Step 4: Avancerede features
   ↓
6. Docker containers starter automatisk
   ↓
7. TAR1090 map tilgængelig på port 8080
```

**Total setup tid: 15-30 minutter**

---

## 🔍 Nøgle Funktioner

### 1. **Omfattende Web UI** (★★★★★)

**Flask Application** (`/opt/adsb/adsb-setup/app.py` - 2500+ linjer):

**Features:**
- ✅ Setup wizard med progressive disclosure
- ✅ SDR auto-detection og GUI tildeling
- ✅ Aggregator konfiguration via checkboxes
- ✅ One-click updates med release notes
- ✅ Backup/restore system
- ✅ Factory reset
- ✅ Real-time status dashboard
- ✅ Container log viewer (Dozzle integration)
- ✅ Diagnostics upload til support

**70+ endpoints** inkl. API for automation

### 2. **Stage2 Multi-Site Arkitektur** (★★★★★)

**Unik differentiator:**
- Central "coordinator" feeder
- Multiple remote "micro-feeders"
- Automatisk aggregering på tværs af sites
- Per-site container orkestrering
- Distributed coverage for store områder

**Use case:** Organisation med feeders i flere byer

### 3. **WiFi Hotspot Fallback** (★★★★★)

**Automatisk network recovery:**
```
No Ethernet → Auto hotspot "adsb-feeder-image"
                    ↓
            Captive portal (DNS hijacking)
                    ↓
            WiFi credentials entry
                    ↓
            Reboot til normal mode
```

**Undgår:** SSH, wpa_supplicant editing, keyboard/monitor

### 4. **Update System** (★★★★★)

**Multi-channel updates:**
- **Stable** - Production releases (default)
- **Beta** - Testing releases
- **Oldstable** - Legacy support

**Update process:**
```bash
# Automatisk via web UI:
1. Check GitHub for latest tag
2. Backup current config
3. Git pull new code
4. Docker pull new containers
5. Restart services
6. Show release notes
```

**Fallback:** Restore from timestamped backups

### 5. **Virtual Machine Support** (★★★★★)

**Native formats:**
- `.ova` - VirtualBox/VMware
- `.vhdx` - Hyper-V
- `.tar.xz` - Proxmox
- USB passthrough guidance

**Fordel:** Test uden hardware commitment

### 6. **Multi-Protokol Support** (★★★★☆)

**Ud over ADS-B:**
- UAT 978MHz (US specific)
- ACARS (aircraft messaging)
- VDL Mode 2 (aircraft datalink)
- HF Data Link (long-range aircraft)
- AIS (ship tracking)
- RadioSonde (weather balloons)

**Single platform for all SDR use cases**

### 7. **CustomPiOS Build Framework** (★★★☆☆)

**Automated image builds:**
- GitHub Actions matrix: 10 platforme
- Chroot-based customization
- Multi-arch support (armv7, aarch64, x86_64)
- Compressed output (xz)

**Platforms:**
- Raspberry Pi (Zero 2, 3, 4, 5)
- Orange Pi (multiple models)
- Le Potato, NanoPi NEO3
- Odroid C4/xu4
- x86-64 native + VMs

---

## 📊 Sammenligning: ADSB Feeder Image vs ADSB.lol vs INTERCEPT

| Aspekt | dirkhh/adsb-feeder-image | ADSB.lol | INTERCEPT (nuværende) |
|--------|-------------------------|----------|----------------------|
| **Installation** | Flash pre-built image | `curl \| bash` script | `./setup.sh` eller Docker |
| **Web UI** | ✅ Comprehensive Flask app | ❌ Ingen (CLI only) | ✅ Flask app (limited config) |
| **Setup tid** | 15-30 min (inkl. wizard) | 10-15 min (CLI) | 20-30 min (CLI) |
| **WiFi setup** | ✅ Captive portal hotspot | ❌ Manual wpa_supplicant | ❌ Manual |
| **SDR management** | ✅ Web GUI auto-detect | ❌ CLI manual | ✅ Web UI detection |
| **Updates** | ✅ One-click web UI | ✅ `adsblol-update` script | ⚠️ `git pull` manual |
| **Backup/Restore** | ✅ Built-in web UI | ❌ Manual | ❌ Manual |
| **Multi-site** | ✅ Stage2 built-in | ❌ Manual | ❌ Ikke supporteret |
| **Container count** | 24+ containers | 22+ containers | 1 container (current Docker) |
| **Protocols** | ADS-B+UAT+ACARS+VDL2+AIS+Sonde | Primært ADS-B+ACARS | Multi-protocol (pager, WiFi, BT, etc.) |
| **VM support** | ✅ Native .ova/.vhdx | ❌ Manual | ⚠️ Docker only |
| **Image size** | 280-863 MB | N/A (installer) | 3-4 GB (monolithic image) |
| **Update channels** | Stable/Beta/Oldstable | Single channel | N/A |
| **User skill** | Beginner | Intermediate | Intermediate |
| **Philosophy** | Turnkey appliance | Power user control | DIY flexibility |
| **Base OS** | DietPi / Raspbian | Any Linux | Raspberry Pi OS |
| **Build system** | CustomPiOS + GitHub Actions | N/A | GitHub Actions (monthly images) |
| **Container orchestration** | Docker Compose + wrapper | Docker Compose | Docker Compose (basic) |
| **Health monitoring** | Built-in (Dozzle) | Autoheal container | ❌ None |
| **Auto-updates** | Optional (via UI) | Optional (Watchtower) | ❌ None |
| **Config method** | Web UI + .env | .env + services.txt | Config files / Web UI |
| **Factory reset** | ✅ Web UI button | ❌ Manual reinstall | ❌ Manual reinstall |

---

## 💡 Hvad INTERCEPT Kan Lære

### 🌟 Top 5 Features at Adoptere

#### 1. **WiFi Hotspot Captive Portal** (Høj prioritet)

**Hvorfor:**
- Eliminerer behov for keyboard/monitor ved første boot
- Mobil-venlig setup
- Automatisk DNS hijacking redirect

**Implementation:**
```python
# hotspot-app.py inspireret tilgang:
- Detect ingen netværk → Start hostapd
- DNS server redirect alt til 192.168.199.1
- Captive portal til WiFi credential entry
- Gem til wpa_supplicant.conf
- Reboot til normal mode
```

**Use case:** Bruger flasher SD kort, sætter i Raspberry Pi, forbinder via mobil

#### 2. **Web-Based Setup Wizard** (Høj prioritet)

**Hvorfor:**
- Guided setup flow
- SDR auto-detection GUI
- Checkbox aggregator selection
- Validation og error messages

**Implementation:**
```python
# Flask routes:
/setup/step1 → Basis (location, timezone)
/setup/step2 → SDR detection + assignment
/setup/step3 → Feature selection (pager, WiFi, BT, etc.)
/setup/step4 → Aggregator credentials
/setup/step5 → Avanceret (docker options)

# Director route:
/setup → Redirect til næste ufuldførte step
```

**Fordel:** Non-technical users kan setup uden CLI

#### 3. **One-Click Update System** (Medium prioritet)

**Hvorfor:**
- User-venligt
- Automatisk backup før update
- Release notes visning
- Multi-channel support (stable/beta)

**Implementation:**
```bash
# intercept-update script med web trigger:
1. Backup config til /opt/intercept/config/backups/
2. Git pull latest code
3. Docker pull new containers
4. Restart services
5. Log completion

# Web UI:
/systemmgmt → Update button
             → Channel selection (stable/beta)
             → Progress indicator
```

#### 4. **Backup/Restore System** (Medium prioritet)

**Hvorfor:**
- Beskytter mod fejlkonfiguration
- Nem migration mellem devices
- Disaster recovery

**Implementation:**
```python
# Flask routes:
/backup → Generer .tar.gz af /opt/intercept/config/
        → Download til browser
        → Timestamp: intercept_backup_2026-01-24_14-30.tar.gz

/restore → Upload .tar.gz
         → Extract til /opt/intercept/config/
         → Restart containers
```

#### 5. **Container Health Monitoring** (Lav prioritet)

**Hvorfor:**
- Auto-restart af crashed containers
- Diagnostics ved problemer
- Better user experience

**Implementation:**
```yaml
# docker-compose.yml additions:
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5050/health"]
  interval: 30s
  timeout: 10s
  retries: 3

# Plus autoheal container:
autoheal:
  image: willfarrell/autoheal
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

---

## 🚫 Hvad IKKE at Adoptere

### 1. **CustomPiOS Build Framework** ❌

**Hvorfor ikke:**
- Kompleksitet uden stor værdi for INTERCEPT
- Docker Compose tilgang er mere flexibel
- Maintenance overhead af build system

**Alternativ:** Minimal base OS image + `intercept-init` script

### 2. **24+ Separate Containers** ❌

**Hvorfor ikke:**
- INTERCEPT har forskellige use cases (ikke kun aviation)
- Over-engineering for single-SDR setups
- Resource overhead på Raspberry Pi

**Alternativ:** 5-8 containers med optional profiles

### 3. **Stage2 Multi-Site Arkitektur** ❌

**Hvorfor ikke:**
- Niche use case for INTERCEPT brugere
- Betydelig kompleksitet
- Kan tilføjes senere hvis efterspørgsel

**Alternativ:** Focus på single-site excellence først

### 4. **Multiple Protocol Support i Hver Container** ❌

**Hvorfor ikke:**
- INTERCEPT allerede multi-protocol (WiFi, BT, etc.)
- Forskellige target audience (security vs aviation)

**Behold:** INTERCEPT's unikke features (TSCM, WiFi, BT)

---

## 🎨 Foreslået Hybrid Tilgang for INTERCEPT

### Kombiner det bedste fra begge verdener:

```
ADSB Feeder Image          ADSB.lol              INTERCEPT v3.0
    Styrker          +    Styrker          =    Hybrid Løsning
─────────────────────────────────────────────────────────────
✅ Web UI wizard           ✅ Minimal base OS       → Web wizard + installer
✅ WiFi hotspot            ✅ Update scripts        → Hotspot captive portal
✅ One-click updates       ✅ Docker Compose        → intercept-update script
✅ Backup/restore          ✅ Container isolation   → Backup/restore web UI
✅ VM support              ✅ Power user control    → Optional VM images
✅ Health monitoring       ✅ Lightweight           → 5-8 containers (not 24)
                           ✅ adsblol-init script   → intercept-init script
```

### Arkitektur Forslag:

```yaml
# docker-compose.yml (simplified fra adsb-feeder)
services:
  core:
    # Flask web UI (port 5050)
    # Setup wizard
    # API endpoints

  pager:
    # multimon-ng + rtl_fm
    profiles: [pager, full]

  adsb:
    # dump1090 (hvis bruger vælger det)
    profiles: [adsb, full]

  sensors:
    # rtl_433
    profiles: [sensors, full]

  wifi:
    # aircrack-ng
    profiles: [wifi, full]

  bluetooth:
    # bleak + hcitool
    profiles: [bluetooth, full]

  autoheal:
    # Container health monitoring
    profiles: [monitoring, full]
```

**Installation:**
```bash
# Metode 1: One-liner (ADSB.lol style)
curl -fsSL https://get.intercept.sh | sudo bash

# Metode 2: Pre-built image (adsb-feeder style)
# Download .img.xz → Flash → Boot → Web wizard

# Metode 3: Docker Compose (power users)
git clone https://github.com/smittix/intercept
cd intercept
docker-compose --profile full up -d
```

**Setup Flow:**
```
1. Boot device
   ↓
2. WiFi detection:
   → Ethernet tilsluttet: http://intercept.local:5050
   → Ingen netværk: Auto hotspot → Captive portal
   ↓
3. Web wizard:
   → Step 1: Location (GPS/manual)
   → Step 2: Features (checkboxes: Pager, ADS-B, WiFi, BT, etc.)
   → Step 3: SDR assignment (auto-detect + GUI)
   → Step 4: Advanced options
   ↓
4. Docker profiles aktiveres baseret på valg
   ↓
5. Containers starter automatisk
   ↓
6. Dashboard med feature status
```

---

## 📈 Implementerings Prioriteter

### Phase 1 (Must-Have - Uge 1-4):
- [ ] WiFi hotspot captive portal
- [ ] Web setup wizard (basic)
- [ ] SDR auto-detection GUI
- [ ] intercept-init installer script
- [ ] Core + 3 primary containers (pager, adsb, sensors)

### Phase 2 (Should-Have - Uge 5-7):
- [ ] One-click update system
- [ ] Backup/restore web UI
- [ ] Health monitoring (autoheal)
- [ ] 2 additional containers (wifi, bluetooth)

### Phase 3 (Nice-to-Have - Uge 8-10):
- [ ] VM image support (.ova)
- [ ] Multi-channel updates (stable/beta)
- [ ] Diagnostics upload
- [ ] Factory reset

---

## 🎯 Konklusion

**ADSB Feeder Image excellence:**
1. ⭐ WiFi hotspot captive portal - **MUST ADOPT**
2. ⭐ Web-based setup wizard - **MUST ADOPT**
3. ⭐ One-click updates - **MUST ADOPT**
4. ⭐ Backup/restore system - **SHOULD ADOPT**
5. ⚠️ 24+ containers - **TOO COMPLEX** for INTERCEPT
6. ⚠️ Stage2 multi-site - **NICHE** use case
7. ⚠️ CustomPiOS - **UNNECESSARY** overhead

**ADSB.lol excellence:**
1. ⭐ Minimal base OS - **KEEP THIS**
2. ⭐ Shell script installers - **ADAPT FOR INTERCEPT**
3. ⭐ Docker Compose orchestration - **KEEP THIS**
4. ⭐ Power user control - **MAINTAIN THIS**

**INTERCEPT unique value:**
1. ⭐ Multi-domain (RF + WiFi + BT + TSCM) - **PRESERVE**
2. ⭐ Security focus - **ENHANCE**
3. ⭐ Educational tool - **EXPAND**

**Recommended hybrid:** ADSB Feeder Image's **user-friendly web UI** + ADSB.lol's **lightweight container architecture** + INTERCEPT's **unique feature set**

---

**Document Version:** 1.0
**Analyzed By:** Claude (AI Assistant)
**Date:** 2026-01-24
