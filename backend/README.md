# Backend

## How to run

Just docker-compose _should_ work:

```bash
docker-compose up
```

## How to use API

API uses token authentication, so...
To send request use header "Authentication" with token given to u from developers)

## Available Endpoints

### Authentication

All endpoints except `/api/ping` and `/api/metrics` require authentication with a valid API token in the "Authentication" header.

### Basic Endpoints

- `GET /api/ping` - Health check endpoint (no authentication required)
- `GET /api/metrics` - Prometheus metrics endpoint (no authentication required)
- `GET /api/v1/ping` - Authenticated health check endpoint

### Operations Endpoints

- `POST /api/v1/scale` - Scale application resources
- `POST /api/v1/restart` - Restart application services
- `POST /api/v1/rollback` - Rollback to previous version

### Kubernetes Service Operations

The following endpoints allow you to manage Kubernetes services:

#### Scale Service

`POST /api/v1/kubernetes/service/scale`

Scales a Kubernetes deployment to the specified number of replicas.

**Request Body:**

```json
{
  "namespace": "default",
  "name": "my-deployment",
  "replicas": 3
}
```

**Response Example:**

```json
{
  "status": "success",
  "message": "Service scaled successfully",
  "data": {
    "name": "my-deployment",
    "namespace": "default",
    "replicas": 3
  }
}
```

#### Restart Service

`POST /api/v1/kubernetes/service/restart`

Restarts all pods in a Kubernetes deployment by adding a restart annotation.

**Request Body:**

```json
{
  "namespace": "default",
  "name": "my-deployment" <-- THIS IS SERVICE NAME (NOT POD)
}
```

**Response Example:**

```json
{
  "status": "success",
  "message": "Service restarted successfully",
  "data": {
    "name": "my-deployment",
    "namespace": "default"
  }
}
```

#### Rollback Service

`POST /api/v1/kubernetes/service/rollback`

Rolls back a Kubernetes deployment to a specified revision or the previous revision.

**Request Body - Default Rollback (to previous revision):**

```json
{
  "namespace": "default",
  "name": "my-deployment" <-- THIS IS SERVICE NAME (NOT POD)
}
```

**Request Body - Rollback to Specific Revision ID:**

```json
{
  "namespace": "default",
  "name": "my-deployment", <-- THIS IS SERVICE NAME (NOT POD)
  "revisionId": "my-deployment-7d9c4b5f96"
}
```

**Request Body - Rollback to Specific Image:**

```json
{
  "namespace": "default",
  "name": "my-deployment", <-- THIS IS SERVICE NAME (NOT POD)
  "revisionImage": "company/my-service:v1.2.3"
}
```

**Request Body - Rollback to Specific Version:**

```json
{
  "namespace": "default",
  "name": "my-deployment", <-- THIS IS SERVICE NAME (NOT POD)
  "version": "v1.2.3"
}
```

**Response Example:**

```json
{
  "status": "success",
  "message": "Service rolled back successfully",
  "data": {
    "name": "my-deployment",
    "namespace": "default",
    "revisionId": "my-deployment-7d9c4b5f96",
    "revisionImage": "",
    "version": ""
  }
}
```

**Notes:**

- The deployment must have at least two revisions to rollback
- If no specific revision is specified, it defaults to the previous revision
- You can specify one of: `revisionId`, `revisionImage`, or `version`
- `revisionId` can be the full ReplicaSet name or the revision number
- When using `version`, the system will search for a revision with a matching image tag

#### Update Service

`POST /api/v1/kubernetes/service/update`

Updates a Kubernetes deployment with a new image or version.

**Request Body:**

```json
{
  "namespace": "default",
  "name": "my-deployment", <-- THIS IS SERVICE NAME (NOT POD)
  "image": "myapp:latest"
}
```

OR

```json
{
  "namespace": "default",
  "name": "my-deployment", <-- THIS IS SERVICE NAME (NOT POD)
  "version": "v2.0.1"
}
```

**Response Example:**

```json
{
  "status": "success",
  "message": "Service updated successfully",
  "data": {
    "name": "my-deployment",
    "namespace": "default",
    "image": "myapp:latest",
    "version": ""
  }
}
```

#### Get Service Status

`POST /api/v1/kubernetes/service/status`

!!!!! The same as `/api/v1/kubernetes/metrics/status/:name` !!!!!
Gets the current status of a Kubernetes deployment.

**Request Body:**

```json
{
  "namespace": "default",
  "name": "my-deployment" <-- THIS IS SERVICE NAME (NOT POD)
}
```

**Response Example:**

```json
{
  "status": "success",
  "message": "Service status retrieved successfully",
  "data": {
    "name": "my-deployment",
    "namespace": "default",
    "replicas": 3,
    "available": 3,
    "ready": 3,
    "updated": 3,
    "unavailable": 0
  }
}
```

### Prometheus Metrics Endpoints

The following endpoints allow you to retrieve metrics directly from Prometheus:

#### Basic Metrics

`GET /api/v1/prometheus/metrics/basic`

Returns basic metrics about your Prometheus-monitored services.

**Response Example:**

```json
{
  "upStatus": true,
  "cpuUsage": 0.00044443456812070885,
  "memoryUsage": 84594688,
  "timestamp": "2023-10-25T14:30:45Z"
}
```

#### List Available Metrics

`GET /api/v1/prometheus/metrics/list`

Returns a list of all available metric names from your Prometheus server.

**Response Example:**

```json
{
  "metrics": [
    "up",
    "process_cpu_seconds_total",
    "process_resident_memory_bytes",
    "prometheus_http_requests_total",
    "go_goroutines"
  ]
}
```

#### Query Specific Metric

`GET /api/v1/prometheus/metrics/:name`

Returns the current value for a specific metric by name.

**Response Example:**

```json
{
  "resultType": "vector",
  "result": [
    {
      "metric": {
        "__name__": "up",
        "instance": "localhost:9090",
        "job": "prometheus"
      },
      "value": [1749298784.856, "1"]
    }
  ]
}
```

#### Custom PromQL Query

`POST /api/v1/prometheus/query`

Execute a custom PromQL query against your Prometheus server.

**Request Body:**

```json
{
  "query": "rate(process_cpu_seconds_total[5m])"
}
```

**Response Example:**

```json
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [
      {
        "metric": {
          "instance": "localhost:9090",
          "job": "prometheus"
        },
        "value": [1749298784.859, "0.00044443456812070885"]
      }
    ]
  }
}
```

### Kubernetes Metrics Endpoints

The following endpoints allow you to retrieve metrics from Prometheus about your Kubernetes cluster (requires Kubernetes metrics in Prometheus):

#### Cluster Metrics

`GET /api/v1/kubernetes/metrics/cluster`

Returns overall metrics for the entire Kubernetes cluster.

**Response Example:**

```json
{
  "cpuUsage": 45.2,
  "memoryUsage": 62.7,
  "nodeCount": 3,
  "podCount": 42,
  "timestamp": "2023-10-25T14:30:45Z"
}
```

#### Node Metrics

`GET /api/v1/kubernetes/metrics/nodes`

Returns metrics for all nodes in the cluster.

**Response Example:**

```json
[
  {
    "name": "worker-node-1",
    "cpuUsage": 78.5,
    "memoryUsage": 82.3,
    "diskUsage": 56.7,
    "podCount": 15
  },
  {
    "name": "worker-node-2",
    "cpuUsage": 42.1,
    "memoryUsage": 51.9,
    "diskUsage": 43.2,
    "podCount": 12
  }
]
```

#### Pod Metrics

`GET /api/v1/kubernetes/metrics/pods`

Returns metrics for all pods in the cluster.

**Query Parameters:**

- `namespace` (optional): Filter pods by namespace

**Response Example:**

```json
[
  {
    "name": "app-backend-547d87fcb5-2jkl9",
    "namespace": "production",
    "cpuUsage": 0.156,
    "memoryUsage": 256000000,
    "restartCount": 0,
    "containerCount": 1
  },
  {
    "name": "app-frontend-65d9d79568-8k73h",
    "namespace": "production",
    "cpuUsage": 0.082,
    "memoryUsage": 128000000,
    "restartCount": 2,
    "containerCount": 1
  }
]
```

#### Deployment Metrics

`GET /api/v1/kubernetes/metrics/deployment`

Returns all the deployments

USE THIS NAME TO MANIPULATE SERVICE (restart, scale, and etc)

**Response Example:**

```json
[
    {
        "name": "nginx-test",
        "namespace": "default",
        "replicas": 6,
        "available": 2,
        "ready": 2
    },
    {
        "name": "coredns",
        "namespace": "kube-system",
        "replicas": 1,
        "available": 1,
        "ready": 1
    },
    {
        "name": "metrics-server",
        "namespace": "kube-system",
        "replicas": 1,
        "available": 0,
        "ready": 0
    }
```

#### Deployment metrics

`GET /api/v1/kubernetes/metrics/deployment/:name`

Returns metrics for a specific deployment.

**Response Example:**

```json
{
  "available": 2,
  "conditions": [
    {
      "lastTransitionTime": "2025-06-07T16:34:34Z",
      "lastUpdateTime": "2025-06-07T18:55:17Z",
      "message": "ReplicaSet \"nginx-test-6bff9d5d95\" has successfully progressed.",
      "reason": "NewReplicaSetAvailable",
      "status": "True",
      "type": "Progressing"
    },
    {
      "lastTransitionTime": "2025-06-07T20:58:08Z",
      "lastUpdateTime": "2025-06-07T20:58:08Z",
      "message": "Deployment does not have minimum availability.",
      "reason": "MinimumReplicasUnavailable",
      "status": "False",
      "type": "Available"
    }
  ],
  "creationTimestamp": "2025-06-07T16:34:34Z",
  "name": "nginx-test",
  "namespace": "default",
  "observedGeneration": 1,
  "ready": 2,
  "replicas": 6,
  "unavailable": 4,
  "updated": 6
}
```

#### Namespace Metrics

`GET /api/v1/kubernetes/metrics/namespaces`

Returns aggregated metrics for all namespaces.

**Response Example:**

```json
[
  {
    "name": "production",
    "cpuUsage": 1.25,
    "memoryUsage": 2048000000,
    "podCount": 12
  },
  {
    "name": "staging",
    "cpuUsage": 0.75,
    "memoryUsage": 1024000000,
    "podCount": 8
  }
]
```

## Configuration

The application reads configuration from environment variables:

- `DEBUG_LEVEL` - Log level (default: "prod")
- `PROMETHEUS_URL` - URL of the Prometheus server (default: "http://localhost:9090")
- `KUBECONFIG` - Path to Kubernetes configuration file (optional, will use in-cluster config if running in Kubernetes)

API keys are stored in `config/keys.json`.

## Using Prometheus Metrics

For proper functioning of the Kubernetes metrics endpoints, your Prometheus server must be configured to scrape Kubernetes metrics. This typically requires:

1. Installing kube-state-metrics in your Kubernetes cluster
2. Configuring Prometheus to scrape node-exporter for node metrics
3. Configuring Prometheus to scrape cadvisor for container metrics

If your Prometheus server doesn't have Kubernetes metrics, you can still use the `/api/v1/prometheus/*` endpoints to access available metrics.
