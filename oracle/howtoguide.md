# 🌩️ Oracle Cloud Free Tier Deployment Guide

Deploy **Ebook2Audiobook** on Oracle Cloud's Always Free Tier for a free, always-on audiobook converter.

## 📋 Prerequisites

- Oracle Cloud account (free signup at [cloud.oracle.com](https://cloud.oracle.com))
- Basic familiarity with SSH and Linux commands

## 🆓 Oracle Cloud Free Tier Resources

Oracle provides these **Always Free** resources (no time limit, no credit card charges):

| Resource | Specification |
|----------|---------------|
| **Ampere A1 Compute** | 4 ARM OCPUs + 24GB RAM |
| **Block Storage** | 200GB total |
| **Network** | 10TB outbound/month |

> **Note**: We'll use the Ampere A1 ARM instance because the AMD Micro instances (1GB RAM) are too small for TTS engines.

---

## 🚀 Step-by-Step Setup

### Step 1: Create an Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com)
2. Click **"Sign Up"** and complete registration
3. Verify your email and set up MFA (required)
4. Wait for account provisioning (~5 minutes)

### Step 2: Create an Ampere A1 Compute Instance

1. In the Oracle Cloud Console, go to **Compute → Instances**
2. Click **"Create Instance"**
3. Configure as follows:

   | Setting | Value |
   |---------|-------|
   | **Name** | `ebook2audiobook` |
   | **Compartment** | (your default) |
   | **Availability Domain** | (any available) |
   | **Image** | Oracle Linux 8 or Ubuntu 22.04 (Arm compatible) |
   | **Shape** | Click "Change Shape" → **Ampere** → **VM.Standard.A1.Flex** |
   | **OCPUs** | `4` (max free) |
   | **Memory** | `24 GB` (max free) |

4. Under **"Add SSH Keys"**:
   - Select **"Generate a key pair for me"**
   - Click **"Save Private Key"** (download `ssh-key.key`)
   - Keep this file safe!

5. Under **"Boot Volume"**:
   - Check **"Specify a custom boot volume size"**
   - Set to `100 GB` (within free limits)

6. Click **"Create"** and wait for the instance to be **RUNNING**

### Step 3: Connect to Your Instance

```bash
# Make your key file secure
chmod 400 ~/Downloads/ssh-key.key

# Connect (replace with your public IP from the Oracle console)
ssh -i ~/Downloads/ssh-key.key ubuntu@YOUR_PUBLIC_IP

# If using Oracle Linux:
ssh -i ~/Downloads/ssh-key.key opc@YOUR_PUBLIC_IP
```

### Step 4: Open Firewall Ports

**In Oracle Cloud Console:**
1. Go to **Networking → Virtual Cloud Networks**
2. Click your VCN → **Security Lists** → Default Security List
3. Add an **Ingress Rule**:
   - Source CIDR: `0.0.0.0/0`
   - Destination Port: `7860`
   - Description: `Ebook2Audiobook Web UI`

**On the instance (firewall):**
```bash
# For Oracle Linux:
sudo firewall-cmd --permanent --add-port=7860/tcp
sudo firewall-cmd --reload

# For Ubuntu:
sudo ufw allow 7860/tcp
```

### Step 5: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Logout and login again for group changes
exit
```

Then SSH back in.

### Step 6: Deploy Ebook2Audiobook

```bash
# Clone the repository
git clone https://github.com/3453-315h/ebook2audiobook-theotherversion.git
cd ebook2audiobook-theotherversion

# Start the application using the Oracle-optimized configuration
# (first run will take 10-15 minutes to build)
docker compose -f oracle/docker-compose.yml up -d --build

# Check logs
docker logs -f ebook2audiobook
```

> **Note**: The `oracle/docker-compose.yml` is specifically optimized for ARM64 architecture with CPU-only settings. It also sets memory limits to 12GB, leaving room for other processes on your 24GB instance.

### Step 7: Access the Web UI

Open your browser and go to:
```
http://YOUR_PUBLIC_IP:7860
```

---

## 🛠️ Configuration Details

### Docker Compose for ARM64 (Ampere A1)

The `oracle/docker-compose.yml` is pre-configured for:
- ARM64 architecture (Ampere A1)
- CPU-only operation (no GPU on free tier)
- Optimized memory settings (12GB limit) for 24GB RAM instances
- Automatic restart on failure (`unless-stopped`)

### Recommended TTS Engines for Free Tier

| Engine | Memory Usage | Speed | Recommendation |
|--------|-------------|-------|----------------|
| **VITS** | ~2GB | Fast | ⭐ Best for Free Tier |
| **Fairseq** | ~3GB | Fast | ✅ Good for Free Tier |
| **Tacotron2** | ~3GB | Fast | ✅ Good for Free Tier |
| **YourTTS** | ~4GB | Medium | ✅ Works on Free Tier |
| **XTTSv2** | ~6GB | Slow | ⚠️ May be slow on ARM |
| **Supertonic** | ~8GB | Medium | ⚠️ Check memory usage |
| **Bark** | ~12GB | Very Slow | ❌ Not recommended |

---

## 📁 Storage Options

### Option A: Local Storage (Default)
Audiobooks are saved in `./audiobooks/` on the instance (mapped via docker-compose).

```bash
# Download audiobooks via SCP
scp -i ~/Downloads/ssh-key.key ubuntu@YOUR_PUBLIC_IP:~/ebook2audiobook-theotherversion/oracle/audiobooks/*.m4b ./
```

### Option B: Oracle Object Storage (Optional)
For persistent cloud storage, mount an Object Storage bucket:

```bash
# Install s3fs
sudo apt install s3fs -y

# Create credentials file
echo "ACCESS_KEY:SECRET_KEY" > ~/.passwd-s3fs
chmod 600 ~/.passwd-s3fs

# Mount bucket
mkdir ~/audiobooks-cloud
s3fs your-bucket-name ~/audiobooks-cloud \
  -o url=https://YOUR_NAMESPACE.compat.objectstorage.REGION.oraclecloud.com \
  -o use_path_request_style \
  -o passwd_file=~/.passwd-s3fs
```

---

## 🔧 Maintenance

### Starting/Stopping the Service

```bash
# Navigate to the repo directory
cd ~/ebook2audiobook-theotherversion

# Stop
docker compose -f oracle/docker-compose.yml down

# Start
docker compose -f oracle/docker-compose.yml up -d

# Restart
docker compose -f oracle/docker-compose.yml restart

# View logs
docker logs -f ebook2audiobook
```

### Updating to Latest Version

```bash
cd ~/ebook2audiobook-theotherversion
git pull
docker compose -f oracle/docker-compose.yml up -d --build --force-recreate
```

### Monitoring Resources

```bash
# Check Docker container stats
docker stats ebook2audiobook

# Check system memory
free -h

# Check disk usage
df -h
```

---

## ⚠️ Troubleshooting

### "Out of Memory" Errors
- Use lighter TTS engines (VITS, Fairseq, Tacotron2)
- Set `SUNO_USE_SMALL_MODELS=True` for Bark (already set in docker-compose)
- Process smaller ebooks

### "Cannot connect to port 7860"
1. Check instance is running: Oracle Console → Compute → Instances
2. Verify security list rules (port 7860 ingress)
3. Check instance firewall: `sudo firewall-cmd --list-ports` or `sudo ufw status`
4. Ensure the container is running: `docker ps`

### Build Fails
```bash
# Clear Docker cache and rebuild
docker system prune -af
docker compose -f oracle/docker-compose.yml up -d --build --no-cache
```

### SSH Connection Refused
- Verify the correct public IP (not private IP)
- Check that SSH key file has correct permissions: `chmod 400 ssh-key.key`
- For Oracle Linux use `opc@`, for Ubuntu use `ubuntu@`

---

## 💡 Tips for Free Tier Usage

1. **Keep the instance running** - Oracle may reclaim idle instances after 7 days
2. **Use lightweight engines** - VITS and Fairseq work best on ARM
3. **Process ebooks in batches** - Don't overload with huge books
4. **Monitor your usage** - Stay within 10TB/month outbound data
5. **Set up monitoring** - Use `docker stats` to watch memory usage

---

## 📞 Support

- [Project GitHub](https://github.com/3453-315h/ebook2audiobook-theotherversion)
- [Discord Community](https://discord.gg/63Tv3F65k6)
