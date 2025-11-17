# 📋 Pre-Deployment Checklist

Voordat je pusht naar GitHub, check deze items:

## ✅ Code Changes
- [x] `app_type` column toegevoegd aan File model
- [x] User-based storage geïmplementeerd (`/uploads/{owner_id}/{file_id}.ext`)
- [x] Content endpoints toegevoegd (GET/PUT `/api/files/{id}/content`)
- [x] CORS geconfigureerd voor port 30081 (EuType)
- [x] Database migratie script gemaakt (`migrate_to_multiapp.py`)
- [x] Test script gemaakt (`test_multiapp.py`)

## ✅ Documentation
- [x] API_CONTRACT.md - Complete API documentatie voor EuType
- [x] EU_CORE_BACKEND_README.md - Technical documentation
- [x] TRANSFORMATION_COMPLETE.md - Feature summary
- [x] DEPLOYMENT_GUIDE.md - CI/CD instructies

## ✅ CI/CD Updates
- [x] Database migration job toegevoegd aan pipeline
- [x] Deployment verificatie uitgebreid
- [x] Multi-app deployment support

## ✅ Lokale Tests
- [x] Backend draait lokaal zonder errors
- [x] Database migratie succesvol uitgevoerd
- [x] Files gemigreerd naar user directories

## 🚀 Ready to Deploy!

Alle changes zijn klaar. Volgende stap:

```bash
# 1. Check wat er gecommit gaat worden
git status

# 2. Add alle changes
git add .

# 3. Commit met duidelijke message
git commit -m "Transform to EU-CORE-BACKEND with multi-app support

Features:
- Multi-app file categorization (app_type field)
- User-based storage structure
- Content endpoints for document editing
- CORS support for multiple frontends
- Automatic database migration in CI/CD
- Complete API documentation

Breaking Changes: NONE (backward compatible)

Ready for EuType integration"

# 4. Push naar GitHub (start CI/CD automatisch)
git push origin main
```

## 📊 Verwachte Pipeline Flow

1. **Test Backend** (~2 min)
   - Python dependencies installeren
   - Run tests (pytest)
   - Lint check (flake8)

2. **Test Frontend** (~2 min)
   - npm install
   - npm run build
   - Lint check

3. **Build and Push** (~5 min)
   - Build backend Docker image
   - Build frontend Docker image
   - Push naar ghcr.io met SHA tags

4. **Deploy** (~3 min)
   - Run database migration (one-time job)
   - Apply Kubernetes manifests
   - Update deployments met nieuwe image tags
   - Wait for rollout completion
   - Verify deployment

**Totale tijd**: ~12-15 minuten

## 🎯 Na Deployment

Check deze URLs:
- Frontend: http://192.168.124.50:30080
- Backend API: http://192.168.124.50:30500
- API Docs: http://192.168.124.50:30500/docs
- Health: http://192.168.124.50:30500/health

Verify op VM:
```bash
kubectl get pods -n eucloud
kubectl logs -f deployment/eucloud-backend -n eucloud
```

## 🆘 Als Er Iets Misgaat

**GitHub Actions fails?**
- Check logs: https://github.com/Dylan0165/EUCLOUD/actions
- Check runner status op VM: `./run.sh --check`

**Pods crashen?**
```bash
kubectl get pods -n eucloud
kubectl logs deployment/eucloud-backend -n eucloud --previous
kubectl describe pod <pod-name> -n eucloud
```

**Migration failed?**
```bash
# Handmatig draaien
kubectl exec -it deployment/eucloud-backend -n eucloud -- python migrate_to_multiapp.py
```

**Rollback needed?**
```bash
kubectl rollout undo deployment/eucloud-backend -n eucloud
```

## 📝 Na Succesvolle Deployment

1. ✅ Test EuCloud frontend (file upload/download)
2. ✅ Test content endpoints via API docs
3. ✅ Verify files in user directories
4. ✅ Share API_CONTRACT.md met EuType team
5. ✅ Begin met EuType frontend development

---

**Status**: READY FOR DEPLOYMENT 🚀
