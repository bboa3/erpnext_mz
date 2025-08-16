# 🐳 Docker Deployment Guide (Clean Skeleton)

This clean skeleton does not include automation scripts or setup routines. Deploy like any Frappe app inside your Docker bench:

```bash
cd frappe_docker
docker compose exec backend bench --site your-site install-app erpnext_mz
```

No custom fields, fixtures, print formats, or schedules are created.
