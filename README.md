# 🤖 ChatOps: service to easilly resolve DevOps incidents

🚀 **Brief description**:  The main idea is to communicate and solve conflicts with APPs that deployed on Kubernetes via Telegram bot.

## 🛠 Technologies

![Go](https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![Aiogram](https://img.shields.io/badge/AIOgram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)


## 📦 Get started

### Preliminary technical requirements
-  [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### ❓ How to run the service 
- Set up the .env file in the source directory
- Set up the Kuberentes in his config file in the following route:
```bash
backend/config/kubeconfig
```
- Clone the repositry and navigate to it, then run the docker compose
```bash
docker compose up -d