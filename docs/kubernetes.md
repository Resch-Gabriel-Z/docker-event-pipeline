# Kubernetes Setup

This project keeps Docker Compose as the primary local container workflow and adds Kubernetes as a second deployment option.

The Kubernetes manifests live in `k8s/base` and can be applied together with:

```bash
kubectl apply -k k8s/base
```

All namespaced resources use the `docker-event-pipeline` namespace.

## Prerequisites

- Docker Desktop installed.
- Kubernetes enabled in Docker Desktop.
- `kubectl` installed and pointing at the correct cluster.

## Enable Docker Desktop Kubernetes

1. Open Docker Desktop.
2. Go to `Settings` -> `Kubernetes`.
3. Enable Kubernetes.
4. Wait until Docker Desktop reports that Kubernetes is running.

Then confirm the context and cluster status:

```bash
kubectl config current-context
kubectl get nodes
```

## What Gets Deployed

The base manifests create:

- Namespace: `docker-event-pipeline`
- ConfigMap: application connection settings
- Secret: example PostgreSQL credentials
- Deployment and Service for `api`
- Deployment for `worker`
- Deployment and Service for `postgres`
- Deployment and Service for `redis`
- ConfigMap, Deployment, and Service for `nginx`

Notes:

- The API image is set to `gabrielsstuff/docker-event-api:0.1.0` as requested.
- No published worker image reference exists anywhere in this repository. The worker Deployment therefore contains a TODO placeholder image that you must replace before the worker will start successfully.
- PostgreSQL data is ephemeral in this Kubernetes learning setup because there is no PersistentVolume or StatefulSet here.

## Secrets

The committed file is [`k8s/base/app-secret.example.yaml`](/home/gabe_desktop/code/docker-event-pipeline/k8s/base/app-secret.example.yaml). It uses dummy values and is included in the base kustomization so the stack is applicable out of the box.

Before using this outside a throwaway local environment, replace the dummy values.

If you want a local-only secret file, create `k8s/local/app-secret.yaml`, keep the Secret name as `app-secret`, and apply it after the base manifests:

```bash
kubectl apply -f k8s/local/app-secret.yaml
kubectl rollout restart deployment/api deployment/worker deployment/postgres -n docker-event-pipeline
```

## Apply The Stack

```bash
kubectl apply -k k8s/base
```

## Inspect Resources

```bash
kubectl get all -n docker-event-pipeline
kubectl get pods -n docker-event-pipeline
kubectl get svc -n docker-event-pipeline
kubectl get configmap -n docker-event-pipeline
kubectl get secret -n docker-event-pipeline
kubectl describe deployment api -n docker-event-pipeline
kubectl describe deployment worker -n docker-event-pipeline
kubectl describe deployment nginx -n docker-event-pipeline
```

## View Logs

```bash
kubectl logs -n docker-event-pipeline deployment/api
kubectl logs -n docker-event-pipeline deployment/worker
kubectl logs -n docker-event-pipeline deployment/postgres
kubectl logs -n docker-event-pipeline deployment/redis
kubectl logs -n docker-event-pipeline deployment/nginx
```

Use `-f` to follow logs:

```bash
kubectl logs -f -n docker-event-pipeline deployment/api
```

## Port-Forward The API

This tests the API Service directly without Nginx:

```bash
kubectl port-forward -n docker-event-pipeline svc/api 8000:8000
curl http://localhost:8000/health
curl -X POST http://localhost:8000/click
curl http://localhost:8000/stats
```

## Port-Forward Nginx

This tests the external entrypoint inside the cluster:

```bash
kubectl port-forward -n docker-event-pipeline svc/nginx 8080:80
curl http://localhost:8080/health
curl -X POST http://localhost:8080/click
curl http://localhost:8080/stats
```

## Delete The Stack

```bash
kubectl delete -k k8s/base
```

## Troubleshooting

### `ImagePullBackOff`

- Check the image name in the Deployment.
- The worker manifest intentionally contains a TODO placeholder image because no published worker image could be confirmed from the repository.
- If the API image fails to pull, verify that `gabrielsstuff/docker-event-api:0.1.0` is available to your cluster.
- Run:

```bash
kubectl describe pods -n docker-event-pipeline
```

### `CrashLoopBackOff`

- Check logs for the failing Deployment.
- Confirm that `app-config` and `app-secret` exist in the `docker-event-pipeline` namespace.
- Confirm that PostgreSQL and Redis are running before expecting the API to become healthy.
- Remember that the worker will not start successfully until you replace the placeholder image.

### Wrong Namespace

- Most commands in this setup should include `-n docker-event-pipeline`.
- Confirm resources exist in the expected namespace:

```bash
kubectl get all -n docker-event-pipeline
```

### Missing Secret Or ConfigMap

- Re-apply the base manifests:

```bash
kubectl apply -k k8s/base
```

- Confirm the resource names:

```bash
kubectl get configmap -n docker-event-pipeline
kubectl get secret -n docker-event-pipeline
```

### Port-Forward Problems

- Make sure the target Service exists:

```bash
kubectl get svc -n docker-event-pipeline
```

- Check whether the backing pods are running and Ready.
- Confirm you used the right namespace and local port: `svc/api 8000:8000` or `svc/nginx 8080:80`.

## Exact Test Flow

Run these commands in order:

```bash
kubectl config current-context
kubectl get nodes

kubectl apply -k k8s/base

kubectl get all -n docker-event-pipeline
kubectl get pods -n docker-event-pipeline
kubectl get svc -n docker-event-pipeline
kubectl get configmap -n docker-event-pipeline
kubectl get secret -n docker-event-pipeline

kubectl logs -n docker-event-pipeline deployment/api
kubectl logs -n docker-event-pipeline deployment/worker
kubectl logs -n docker-event-pipeline deployment/nginx

kubectl port-forward -n docker-event-pipeline svc/api 8000:8000
curl http://localhost:8000/health

kubectl port-forward -n docker-event-pipeline svc/nginx 8080:80
curl http://localhost:8080/health

kubectl delete -k k8s/base
```

Worker-specific note:

- If you do not replace the placeholder worker image first, expect the worker pod to fail with `ImagePullBackOff`.
- After publishing or building a real worker image, update [`k8s/base/worker-deployment.yaml`](/home/gabe_desktop/code/docker-event-pipeline/k8s/base/worker-deployment.yaml) before testing worker behavior.
