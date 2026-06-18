# Local Kubernetes Notes

`k8s/base` is the tracked, applyable base:

```bash
kubectl apply -k k8s/base
```

The committed Secret file in base is an example with dummy values. If you want local-only secret values without editing tracked files, create your own ignored file such as `k8s/local/app-secret.yaml` and apply it after the base resources:

```bash
kubectl apply -f k8s/local/app-secret.yaml
kubectl rollout restart deployment/api deployment/worker deployment/postgres -n docker-event-pipeline
```

If you use a local secret file, keep the Secret name as `app-secret` so the Deployments continue to work.
