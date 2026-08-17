# 🚀 DevBoard AI – Kubernetes Deployment with PostgreSQL, Ollama & AI Service

![Kubernetes](https://img.shields.io/badge/Kubernetes-Deployment-blue?logo=kubernetes)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Containers-blue?logo=docker)
![Ollama](https://img.shields.io/badge/Ollama-LLM-green)
![Go](https://img.shields.io/badge/Backend-Go-00ADD8?logo=go)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)

# 📌 Project Overview

**DevBoard AI** is a production-style Kubernetes project that demonstrates how to deploy a complete AI-enabled application on Kubernetes.

The project includes:

* React Frontend
* Go Backend API
* PostgreSQL Stateful Database
* Ollama LLM Server
* AI Microservice
* Persistent Storage
* ConfigMaps & Secrets
* Horizontal Pod Autoscaler (HPA)

This project is designed for **DevOps Engineers**, **Cloud Engineers**, and anyone learning **Kubernetes** through real-world deployments.

---

# 🏗 Architecture

```
                    User
                      │
                      ▼
           Frontend (React)
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   Backend API (Go)        AI Service
          │                       │
          │                       ▼
          │                 Ollama LLM
          │
          ▼
      PostgreSQL
```

---

# 📂 Project Structure

```
k8s/
│
├── namespace.yml
├── secrets.yml
├── configMap.yml
│
├── postgres-init.yml
├── persistent-volume.yml
├── postgres-statefulset.yml
├── postgres-service.yml
│
├── backend-deployment.yml
├── backend-service.yml
│
├── frontend-deployment.yml
├── frontend-service.yml
├── frontend-hpa.yml
│
├── ollama-pvc.yml
├── ollama-deployment.yml
├── ollama-service.yml
│
├── ai-service-deployment.yml
└── ai-service-service.yml
```

---

# 🚀 Components

## 1. Namespace

Creates an isolated Kubernetes namespace.

```
devboard
```

---

## 2. ConfigMap

Stores non-sensitive configuration.

Example:

* PostgreSQL User

---

## 3. Secret

Stores sensitive information.

* PostgreSQL Password
* Database Name

---

## 4. PostgreSQL StatefulSet

Uses:

* StatefulSet
* Persistent Storage
* ConfigMap
* Secret
* SQL Initialization Scripts

Features

* Persistent Database
* Automatic Schema Creation
* Seed Data
* Readiness Probe

---

## 5. Backend Deployment

The Go backend connects to PostgreSQL using environment variables.

Features

* REST API
* Health Checks
* Liveness Probe
* Database Connectivity

---

## 6. Frontend Deployment

React application deployed as a Deployment.

Accessible through

```
NodePort
```

Features

* React UI
* Lightweight Container
* Resource Limits

---

## 7. Ollama Deployment

Runs an LLM inside Kubernetes.

Automatically pulls

```
llama3.2:1b
```

Features

* Persistent Model Storage
* Readiness Probe
* Liveness Probe
* Automatic Model Download

---

## 8. AI Service

Acts as an AI layer between the frontend and Ollama.

Environment Variables

```
TASK_SERVICE_URL
MODEL_API_BASE
MODEL_NAME
```

Features

* Calls Backend API
* Sends prompts to Ollama
* Returns AI responses

---

## 9. Horizontal Pod Autoscaler

Automatically scales the frontend.

```
Min Pods : 1

Max Pods : 5
```

Scaling Metric

* CPU Utilization

---

# 💾 Persistent Storage

This project demonstrates:

* Persistent Volumes (PV)
* Persistent Volume Claims (PVC)
* StatefulSet VolumeClaimTemplates

Used by

* PostgreSQL
* Ollama

---

# 📊 Kubernetes Objects Used

✅ Namespace

✅ ConfigMap

✅ Secret

✅ PersistentVolume

✅ PersistentVolumeClaim

✅ StatefulSet

✅ Deployment

✅ Service

✅ HorizontalPodAutoscaler

---

# 🚀 Deployment Steps

## 1. Create Namespace

```bash
kubectl apply -f namespace.yml
```

---

## 2. Apply Configurations

```bash
kubectl apply -f configMap.yml
kubectl apply -f secrets.yml
```

---

## 3. Deploy PostgreSQL

```bash
kubectl apply -f postgres-init.yml
kubectl apply -f persistent-volume.yml
kubectl apply -f postgres-statefulset.yml
kubectl apply -f postgres-service.yml
```

---

## 4. Deploy Backend

```bash
kubectl apply -f backend-deployment.yml
kubectl apply -f backend-service.yml
```

---

## 5. Deploy Frontend

```bash
kubectl apply -f frontend-deployment.yml
kubectl apply -f frontend-service.yml
kubectl apply -f frontend-hpa.yml
```

---

## 6. Deploy Ollama

```bash
kubectl apply -f ollama-pvc.yml
kubectl apply -f ollama-deployment.yml
kubectl apply -f ollama-service.yml
```

---

## 7. Deploy AI Service

```bash
kubectl apply -f ai-service-deployment.yml
kubectl apply -f ai-service-service.yml
```

---

# 🔍 Verify Deployment

Pods

```bash
kubectl get pods -n devboard
```

Services

```bash
kubectl get svc -n devboard
```

StatefulSets

```bash
kubectl get statefulsets -n devboard
```

Deployments

```bash
kubectl get deployments -n devboard
```

HPA

```bash
kubectl get hpa -n devboard
```

---

# 🧠 Learning Outcomes

By completing this project, you'll gain hands-on experience with:

* Kubernetes Namespaces
* ConfigMaps
* Secrets
* Deployments
* StatefulSets
* Persistent Volumes
* Persistent Volume Claims
* Services
* Readiness & Liveness Probes
* Resource Requests & Limits
* Horizontal Pod Autoscaler (HPA)
* PostgreSQL on Kubernetes
* React Deployment
* Go Backend Deployment
* AI Microservice Deployment
* Ollama LLM Deployment
* Kubernetes Networking
* Production-style Kubernetes Architecture