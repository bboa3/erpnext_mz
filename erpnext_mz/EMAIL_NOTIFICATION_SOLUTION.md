# Email Notification Solution - Production

## ✅ Diagnostic Complete

Your production site diagnostic shows:

### What's Working:
- ✅ SMTP configured correctly (2 email accounts)
- ✅ Notifications configured (3 active notifications)
- ✅ Scheduler enabled in settings
- ✅ 15 emails sent successfully

### 🔴 CRITICAL ISSUE:

**Background Workers Not Running**

```
Last Scheduled Job: 1257.8 minutes ago (21 hours!)
```

**This is why notifications aren't sending** - the email queue is not being processed.

---

## 🔧 Solution

### Step 1: Check Worker Status

```bash
# On production server
cd /home/frappe/prod-bench
sudo supervisorctl status
```

You should see something like:
```
frappe-bench-workers:frappe-bench-frappe-default-worker-0   RUNNING
frappe-bench-workers:frappe-bench-frappe-long-worker-0      RUNNING
frappe-bench-workers:frappe-bench-frappe-schedule           RUNNING
frappe-bench-workers:frappe-bench-frappe-short-worker-0     RUNNING
frappe-bench-web:frappe-bench-frappe-web                    RUNNING
```

If they show **STOPPED** or **FATAL**, that's your problem.

### Step 2: Restart Workers

```bash
# Restart all workers
sudo supervisorctl restart frappe-bench-workers:
sudo supervisorctl restart frappe-bench-web:

# Or restart everything
sudo supervisorctl restart all
```

### Step 3: Verify Workers Started

```bash
# Check status again
sudo supervisorctl status

# All should show RUNNING
```

### Step 4: Test Email Queue Processing

```bash
cd /home/frappe/prod-bench
bench --site erp.mozeconomia.co.mz execute erpnext_mz.diagnose_email_notifications.diagnose_email_notifications
```

Look for:
```
Last Scheduled Job: X minutes ago
```

Should be **< 5 minutes** if workers are running properly.

### Step 5: Test Notification

Create or submit a Sales Invoice and check if the notification email is queued and sent.

---

## 📊 Understanding the Issue

### Why Direct Emails Work But Notifications Don't:

1. **Direct emails** (`frappe.sendmail()`) - Send immediately via SMTP
2. **Notifications** - Added to Email Queue → Processed by background workers

**Without workers running:**
- ✅ Direct emails work (SMTP is fine)
- ❌ Notifications don't send (queue not processed)
- ❌ Scheduled tasks don't run
- ❌ Background jobs frozen

---

## 🔍 Troubleshooting

### If Workers Won't Start:

**Check logs:**
```bash
tail -f /home/frappe/prod-bench/logs/worker.error.log
```

**Common issues:**

1. **Redis not running:**
```bash
sudo systemctl status redis
sudo systemctl restart redis
```

2. **Port conflicts:**
```bash
# Check if ports are in use
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :6379
```

3. **Permission issues:**
```bash
# Fix ownership
cd /home/frappe
sudo chown -R frappe:frappe prod-bench
```

4. **Supervisor config issues:**
```bash
# Regenerate supervisor config
cd /home/frappe/prod-bench
bench setup supervisor --yes
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all
```

### If Scheduler is Disabled:

```bash
bench --site erp.mozeconomia.co.mz scheduler enable
bench --site erp.mozeconomia.co.mz scheduler resume
```

### If Email Queue is Stuck:

```bash
bench --site erp.mozeconomia.co.mz console
```

```python
# Manually flush queue
from frappe.email.queue import flush
flush(from_test=False)
```

---

## 📝 Post-Fix Verification

After restarting workers, verify:

1. **Workers are running:**
```bash
sudo supervisorctl status
# All should show RUNNING
```

2. **Scheduler is active:**
```bash
bench --site erp.mozeconomia.co.mz execute erpnext_mz.diagnose_email_notifications.diagnose_email_notifications
# Last job should be < 5 minutes ago
```

3. **Email queue is processing:**
```bash
bench --site erp.mozeconomia.co.mz console
```
```python
import frappe
queue = frappe.get_all("Email Queue", 
    filters={"status": "Not Sent"}, 
    limit=10
)
print(f"Emails waiting: {len(queue)}")
```

4. **Test notification:**
   - Create/submit a Sales Invoice
   - Check Email Queue for new email
   - Verify email is sent within 1-2 minutes

---

## 🚀 Prevention

### Set Up Monitoring:

1. **Worker auto-restart:**
   - Supervisor already configured for this
   - Check `/etc/supervisor/conf.d/frappe-bench.conf`

2. **Monitor scheduler:**
```bash
# Add to cron for daily checks
0 9 * * * cd /home/frappe/prod-bench && bench --site erp.mozeconomia.co.mz execute erpnext_mz.diagnose_email_notifications.diagnose_email_notifications | mail -s "ERPNext Health Check" admin@mozeconomia.co.mz
```

3. **Check logs regularly:**
```bash
tail -f /home/frappe/prod-bench/logs/worker.error.log
tail -f /home/frappe/prod-bench/logs/web.error.log
```

---

## 📞 Quick Reference

```bash
# Check status
sudo supervisorctl status

# Restart workers
sudo supervisorctl restart frappe-bench-workers:

# Check logs
tail -f /home/frappe/prod-bench/logs/worker.error.log

# Run diagnostic
bench --site erp.mozeconomia.co.mz execute erpnext_mz.diagnose_email_notifications.diagnose_email_notifications

# Enable scheduler
bench --site erp.mozeconomia.co.mz scheduler enable

# Manually process queue
bench --site erp.mozeconomia.co.mz execute frappe.email.queue.flush
```

---

## ✅ Summary

**Problem:** Background workers stopped → Email queue not processed → Notifications not sent

**Solution:** Restart workers with `sudo supervisorctl restart frappe-bench-workers:`

**Verification:** Last scheduled job should be < 5 minutes ago

**Status:** Ready to fix - just need to restart the workers!

