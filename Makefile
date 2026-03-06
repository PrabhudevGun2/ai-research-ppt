NAMESPACE     := ai-research-ppt
BACKEND_IMG   := ai-research-ppt-backend:latest
FRONTEND_IMG  := ai-research-ppt-frontend:latest

.PHONY: help build deploy port-forward clean logs status

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Local dev ────────────────────────────────────────────────────────────────

dev:  ## Run with docker-compose (local dev)
	docker-compose up --build

dev-down:  ## Stop local dev stack
	docker-compose down -v

# ── Minikube / K8s ──────────────────────────────────────────────────────────

minikube-start:  ## Start minikube
	minikube start --cpus=4 --memory=4096 --driver=docker

minikube-env:  ## Print eval command for minikube docker env
	@echo "Run: eval \$$(minikube docker-env)"

build:  ## Build Docker images inside minikube's Docker daemon
	eval $$(minikube docker-env) && \
	docker build -f docker/Dockerfile.backend -t $(BACKEND_IMG) . && \
	docker build -f docker/Dockerfile.frontend -t $(FRONTEND_IMG) .

build-backend:  ## Build only the backend image
	eval $$(minikube docker-env) && docker build -f docker/Dockerfile.backend -t $(BACKEND_IMG) .

build-frontend:  ## Build only the frontend image
	eval $$(minikube docker-env) && docker build -f docker/Dockerfile.frontend -t $(FRONTEND_IMG) .

deploy:  ## Apply all K8s manifests (requires API key secret first)
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/redis/
	kubectl apply -f k8s/backend/
	kubectl apply -f k8s/frontend/
	@echo "Waiting for pods to be ready..."
	kubectl rollout status deployment/redis   -n $(NAMESPACE) --timeout=120s
	kubectl rollout status deployment/backend  -n $(NAMESPACE) --timeout=120s
	kubectl rollout status deployment/frontend -n $(NAMESPACE) --timeout=120s

set-secret:  ## Create OpenRouter API key secret (prompts for key)
	@read -s -p "Enter OPENROUTER_API_KEY: " KEY && echo && \
	kubectl create secret generic api-keys \
	  --from-literal=OPENROUTER_API_KEY=$$KEY \
	  -n $(NAMESPACE) \
	  --dry-run=client -o yaml | kubectl apply -f -

port-forward:  ## Port-forward frontend to localhost:8501
	kubectl port-forward svc/frontend 8501:80 -n $(NAMESPACE)

port-forward-backend:  ## Port-forward backend to localhost:8000
	kubectl port-forward svc/backend 8000:8000 -n $(NAMESPACE)

open:  ## Open frontend in browser via minikube service
	minikube service frontend -n $(NAMESPACE)

status:  ## Show pod status
	kubectl get pods -n $(NAMESPACE) -o wide

logs-backend:  ## Tail backend logs
	kubectl logs -f deployment/backend -n $(NAMESPACE)

logs-frontend:  ## Tail frontend logs
	kubectl logs -f deployment/frontend -n $(NAMESPACE)

logs-redis:  ## Tail redis logs
	kubectl logs -f deployment/redis -n $(NAMESPACE)

rollout-backend:  ## Rolling restart backend
	kubectl rollout restart deployment/backend -n $(NAMESPACE)

rollout-frontend:  ## Rolling restart frontend
	kubectl rollout restart deployment/frontend -n $(NAMESPACE)

clean:  ## Delete all K8s resources (keeps namespace)
	kubectl delete -f k8s/frontend/ -n $(NAMESPACE) --ignore-not-found
	kubectl delete -f k8s/backend/ -n $(NAMESPACE) --ignore-not-found
	kubectl delete -f k8s/redis/ -n $(NAMESPACE) --ignore-not-found

destroy:  ## Delete namespace (removes everything)
	kubectl delete namespace $(NAMESPACE) --ignore-not-found

minikube-stop:  ## Stop minikube
	minikube stop
