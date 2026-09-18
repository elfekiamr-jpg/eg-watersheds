# Deploying as a real website

## Pick a host

The app needs a real VPS (not a bare static host) since it runs Python +
geopandas/rasterio and caches hydrology data for megabasin 17 (the whole
Nile Basin — Delta through Sudan, Ethiopia and the Lake Victoria region,
not just Egypt's slice of it).

**Size this up before you commit to a plan.** KSA's single basin (29, the
whole Arabian Peninsula) already needed "a few hundred MB–low GB" and a
real VPS. Basin 17 covers a river system spanning 11 countries and is
almost certainly bigger — I haven't been able to measure the actual
download size myself (network access here doesn't reach mghydro.com's
data host). Run `python predownload.py` once, locally, and check the
resulting size of `delineator_data/` before picking a host — it tells you
whether the numbers below are still realistic or need bumping up.

Starting point, cheapest-that-won't-struggle **assuming basin 17 is
roughly the same order of magnitude as basin 29 was**:

- **Hetzner Cloud CX22** — 2 vCPU / 4 GB RAM / 40 GB disk, ~€4.6/month.
- **DigitalOcean Basic Droplet** — 2 GB RAM / 50 GB disk, $12/month.

If basin 17 turns out to be several times bigger (plausible, given it's
several times the geographic area), step up disk size accordingly —
Hetzner CX32 (80 GB disk, ~€8.5/month) or DigitalOcean's next tier up are
the easy answers.

Avoid free-tier PaaS (Render/Railway free, Heroku free) for this one —
512 MB RAM is tight even for a basin-29-sized spatial index, and a
basin-17-sized one is likely worse.

You'll also want a domain (or subdomain) pointed at the server — any
registrar works, you just need an **A record** aiming at the VPS's IP.

## One-time server setup

SSH into the fresh VPS, then:

```bash
# Install Docker + Compose plugin (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin
```

## Deploy

```bash
# From your machine: copy the project to the server
scp -r eg-watersheds root@YOUR_SERVER_IP:/root/

# On the server
cd /root/eg-watersheds
```

Edit `Caddyfile` and replace `your-domain.com` with your actual domain —
Caddy uses this to request a free Let's Encrypt certificate automatically
on first boot. Then:

```bash
docker compose up -d --build
```

The build step downloads megabasin 17's data (unit catchments, rivers,
flow direction, flow accumulation for the whole Nile Basin) into the
image — this is the slow part, and likely slower than KSA's build was.
Give it real time depending on file size and your connection. Once it's
up, visit `https://your-domain.com` — Caddy handles HTTPS for you, no
certbot/nginx config needed.

Sinai, Western Desert, north-Sinai/Mediterranean and Red-Sea-south-of-Suez
clicks (basins 29, 15, 21, 11) aren't baked into the image — they download
on first click instead, and persist across restarts in the `egypt_data`
Docker volume that's already wired up in `docker-compose.yml`.

## After deploying

```bash
docker compose logs -f app       # tail the app's logs
docker compose restart app       # restart just the app
docker compose down && docker compose up -d --build   # rebuild after code changes
```

Since basin 17's data is baked into the image, redeploys after a *code*
change (editing `app.py` or `index.html`) will re-run the data download
step too unless you reorder the Dockerfile so `COPY app.py .` / `COPY
static/` come after the `RUN downloader(17)` line — they already do in the
Dockerfile provided, so Docker's layer cache will skip re-downloading as
long as `requirements.txt` hasn't changed.

## Costs to expect

- VPS: ~€4.60–$12/month as a starting point — confirm against the actual
  basin-17 size before committing (see above); could be more
- Domain: ~$10–15/year if you don't already have one
- Data transfer/bandwidth: negligible at portfolio-project traffic levels
