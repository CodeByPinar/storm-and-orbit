# Fırtına ve Yörünge · Railway yayını

Canlı adres: https://storm-and-orbit.up.railway.app

Statik site: `site/` klasörü Caddy ile sunulur (`Dockerfile`, `Caddyfile`). Railway portu `PORT` ortam değişkeniyle verir.

## Güncelleme

Proje kökünden:

```powershell
python presentation\build_data.py
python deploy\build_site.py
```

Ardından `deploy` klasöründe:

```powershell
railway up --ci -y
```
