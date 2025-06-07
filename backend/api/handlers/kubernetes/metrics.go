package kubernetes

import (
	"context"
	"fmt"
	"time"

	"github.com/gofiber/fiber/v3"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/prometheus_client/query"
)

// MetricsHandler handles Kubernetes metrics requests
type MetricsHandler struct {
	promClient *query.PrometheusClient
}

// NewMetricsHandler creates a new Kubernetes metrics handler
func NewMetricsHandler(promURL string) *MetricsHandler {
	return &MetricsHandler{
		promClient: query.NewPrometheusClient(promURL),
	}
}

// ClusterMetrics represents overall cluster metrics
type ClusterMetrics struct {
	CPUUsage    float64 `json:"cpuUsage"`    // Percentage of CPU usage across the cluster
	MemoryUsage float64 `json:"memoryUsage"` // Percentage of memory usage across the cluster
	NodeCount   int     `json:"nodeCount"`   // Number of nodes in the cluster
	PodCount    int     `json:"podCount"`    // Number of pods running in the cluster
	Timestamp   string  `json:"timestamp"`   // Time when metrics were collected
}

// NodeMetrics represents metrics for a single node
type NodeMetrics struct {
	Name        string  `json:"name"`
	CPUUsage    float64 `json:"cpuUsage"`    // Percentage of CPU usage
	MemoryUsage float64 `json:"memoryUsage"` // Percentage of memory usage
	DiskUsage   float64 `json:"diskUsage"`   // Percentage of disk usage
	PodCount    int     `json:"podCount"`    // Number of pods running on this node
}

// PodMetrics represents metrics for a single pod
type PodMetrics struct {
	Name           string  `json:"name"`
	Namespace      string  `json:"namespace"`
	CPUUsage       float64 `json:"cpuUsage"`       // CPU usage in cores
	MemoryUsage    float64 `json:"memoryUsage"`    // Memory usage in bytes
	RestartCount   int     `json:"restartCount"`   // Number of restarts
	ContainerCount int     `json:"containerCount"` // Number of containers
}

// GetClusterMetrics returns overall cluster metrics
func (h *MetricsHandler) GetClusterMetrics(c fiber.Ctx) error {
	ctx := context.Background()
	
	// Query for CPU usage across the cluster
	cpuQuery := "sum(rate(container_cpu_usage_seconds_total{container!=''}[5m])) / sum(machine_cpu_cores) * 100"
	cpuResult, err := h.promClient.Query(ctx, cpuQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch CPU metrics: %v", err),
		})
	}
	
	// Query for memory usage across the cluster
	memQuery := "sum(container_memory_usage_bytes{container!=''}) / sum(machine_memory_bytes) * 100"
	memResult, err := h.promClient.Query(ctx, memQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch memory metrics: %v", err),
		})
	}
	
	// Query for node count
	nodeQuery := "count(kube_node_info)"
	nodeResult, err := h.promClient.Query(ctx, nodeQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch node count: %v", err),
		})
	}
	
	// Query for pod count
	podQuery := "count(kube_pod_info)"
	podResult, err := h.promClient.Query(ctx, podQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch pod count: %v", err),
		})
	}
	
	// Parse results
	var cpuUsage, memUsage float64
	var nodeCount, podCount int
	var timestamp time.Time
	
	if len(cpuResult.Data.Result) > 0 {
		cpuUsage, timestamp, err = query.FormatValue(cpuResult.Data.Result[0].Value)
		if err != nil {
			cpuUsage = 0
		}
	}
	
	if len(memResult.Data.Result) > 0 {
		memUsage, _, err = query.FormatValue(memResult.Data.Result[0].Value)
		if err != nil {
			memUsage = 0
		}
	}
	
	if len(nodeResult.Data.Result) > 0 {
		nodeCountFloat, _, err := query.FormatValue(nodeResult.Data.Result[0].Value)
		if err == nil {
			nodeCount = int(nodeCountFloat)
		}
	}
	
	if len(podResult.Data.Result) > 0 {
		podCountFloat, _, err := query.FormatValue(podResult.Data.Result[0].Value)
		if err == nil {
			podCount = int(podCountFloat)
		}
	}
	
	metrics := ClusterMetrics{
		CPUUsage:    cpuUsage,
		MemoryUsage: memUsage,
		NodeCount:   nodeCount,
		PodCount:    podCount,
		Timestamp:   timestamp.Format(time.RFC3339),
	}
	
	return c.Status(fiber.StatusOK).JSON(metrics)
}

// GetNodeMetrics returns metrics for all nodes
func (h *MetricsHandler) GetNodeMetrics(c fiber.Ctx) error {
	ctx := context.Background()
	
	// Query for node CPU usage
	cpuQuery := "sum(rate(node_cpu_seconds_total{mode!='idle'}[5m])) by (instance) / on(instance) group_left count(node_cpu_seconds_total{mode='idle'}) by (instance) * 100"
	cpuResult, err := h.promClient.Query(ctx, cpuQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch node CPU metrics: %v", err),
		})
	}
	
	// Query for node memory usage
	memQuery := "node_memory_Active_bytes / node_memory_MemTotal_bytes * 100"
	memResult, err := h.promClient.Query(ctx, memQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch node memory metrics: %v", err),
		})
	}
	
	// Query for node disk usage
	diskQuery := "100 - ((node_filesystem_avail_bytes{mountpoint='/'} * 100) / node_filesystem_size_bytes{mountpoint='/'})"
	diskResult, err := h.promClient.Query(ctx, diskQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch node disk metrics: %v", err),
		})
	}
	
	// Query for pod count per node
	podQuery := "count(kube_pod_info) by (node)"
	podResult, err := h.promClient.Query(ctx, podQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch pod count per node: %v", err),
		})
	}
	
	// Map to store node metrics
	nodeMetricsMap := make(map[string]*NodeMetrics)
	
	// Process CPU metrics
	for _, result := range cpuResult.Data.Result {
		nodeName := result.Metric["instance"]
		if _, exists := nodeMetricsMap[nodeName]; !exists {
			nodeMetricsMap[nodeName] = &NodeMetrics{Name: nodeName}
		}
		
		cpuUsage, _, err := query.FormatValue(result.Value)
		if err == nil {
			nodeMetricsMap[nodeName].CPUUsage = cpuUsage
		}
	}
	
	// Process memory metrics
	for _, result := range memResult.Data.Result {
		nodeName := result.Metric["instance"]
		if _, exists := nodeMetricsMap[nodeName]; !exists {
			nodeMetricsMap[nodeName] = &NodeMetrics{Name: nodeName}
		}
		
		memUsage, _, err := query.FormatValue(result.Value)
		if err == nil {
			nodeMetricsMap[nodeName].MemoryUsage = memUsage
		}
	}
	
	// Process disk metrics
	for _, result := range diskResult.Data.Result {
		nodeName := result.Metric["instance"]
		if _, exists := nodeMetricsMap[nodeName]; !exists {
			nodeMetricsMap[nodeName] = &NodeMetrics{Name: nodeName}
		}
		
		diskUsage, _, err := query.FormatValue(result.Value)
		if err == nil {
			nodeMetricsMap[nodeName].DiskUsage = diskUsage
		}
	}
	
	// Process pod count
	for _, result := range podResult.Data.Result {
		nodeName := result.Metric["node"]
		if _, exists := nodeMetricsMap[nodeName]; !exists {
			nodeMetricsMap[nodeName] = &NodeMetrics{Name: nodeName}
		}
		
		podCount, _, err := query.FormatValue(result.Value)
		if err == nil {
			nodeMetricsMap[nodeName].PodCount = int(podCount)
		}
	}
	
	// Convert map to slice
	nodeMetrics := make([]NodeMetrics, 0, len(nodeMetricsMap))
	for _, metrics := range nodeMetricsMap {
		nodeMetrics = append(nodeMetrics, *metrics)
	}
	
	return c.Status(fiber.StatusOK).JSON(nodeMetrics)
}

// GetPodMetrics returns metrics for all pods
func (h *MetricsHandler) GetPodMetrics(c fiber.Ctx) error {
	ctx := context.Background()
	namespace := c.Query("namespace")
	
	// Build namespace filter
	namespaceFilter := ""
	if namespace != "" {
		namespaceFilter = fmt.Sprintf(`,namespace="%s"`, namespace)
	}
	
	// Query for pod CPU usage
	cpuQuery := fmt.Sprintf("sum(rate(container_cpu_usage_seconds_total{container!=''}[5m])) by (pod%s)", namespaceFilter)
	cpuResult, err := h.promClient.Query(ctx, cpuQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch pod CPU metrics: %v", err),
		})
	}
	
	// Query for pod memory usage
	memQuery := fmt.Sprintf("sum(container_memory_usage_bytes{container!=''}) by (pod%s)", namespaceFilter)
	memResult, err := h.promClient.Query(ctx, memQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch pod memory metrics: %v", err),
		})
	}
	
	// Query for pod restart count
	restartQuery := fmt.Sprintf("sum(kube_pod_container_status_restarts_total) by (pod%s)", namespaceFilter)
	restartResult, err := h.promClient.Query(ctx, restartQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch pod restart metrics: %v", err),
		})
	}
	
	// Query for container count per pod
	containerQuery := fmt.Sprintf("count(kube_pod_container_info) by (pod%s)", namespaceFilter)
	containerResult, err := h.promClient.Query(ctx, containerQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch container count: %v", err),
		})
	}
	
	// Map to store pod metrics
	podMetricsMap := make(map[string]*PodMetrics)
	
	// Process CPU metrics
	for _, result := range cpuResult.Data.Result {
		podName := result.Metric["pod"]
		ns := result.Metric["namespace"]
		
		key := fmt.Sprintf("%s/%s", ns, podName)
		if _, exists := podMetricsMap[key]; !exists {
			podMetricsMap[key] = &PodMetrics{Name: podName, Namespace: ns}
		}
		
		cpuUsage, _, err := query.FormatValue(result.Value)
		if err == nil {
			podMetricsMap[key].CPUUsage = cpuUsage
		}
	}
	
	// Process memory metrics
	for _, result := range memResult.Data.Result {
		podName := result.Metric["pod"]
		ns := result.Metric["namespace"]
		
		key := fmt.Sprintf("%s/%s", ns, podName)
		if _, exists := podMetricsMap[key]; !exists {
			podMetricsMap[key] = &PodMetrics{Name: podName, Namespace: ns}
		}
		
		memUsage, _, err := query.FormatValue(result.Value)
		if err == nil {
			podMetricsMap[key].MemoryUsage = memUsage
		}
	}
	
	// Process restart count
	for _, result := range restartResult.Data.Result {
		podName := result.Metric["pod"]
		ns := result.Metric["namespace"]
		
		key := fmt.Sprintf("%s/%s", ns, podName)
		if _, exists := podMetricsMap[key]; !exists {
			podMetricsMap[key] = &PodMetrics{Name: podName, Namespace: ns}
		}
		
		restartCount, _, err := query.FormatValue(result.Value)
		if err == nil {
			podMetricsMap[key].RestartCount = int(restartCount)
		}
	}
	
	// Process container count
	for _, result := range containerResult.Data.Result {
		podName := result.Metric["pod"]
		ns := result.Metric["namespace"]
		
		key := fmt.Sprintf("%s/%s", ns, podName)
		if _, exists := podMetricsMap[key]; !exists {
			podMetricsMap[key] = &PodMetrics{Name: podName, Namespace: ns}
		}
		
		containerCount, _, err := query.FormatValue(result.Value)
		if err == nil {
			podMetricsMap[key].ContainerCount = int(containerCount)
		}
	}
	
	// Convert map to slice
	podMetrics := make([]PodMetrics, 0, len(podMetricsMap))
	for _, metrics := range podMetricsMap {
		podMetrics = append(podMetrics, *metrics)
	}
	
	return c.Status(fiber.StatusOK).JSON(podMetrics)
}

// GetNamespaceMetrics returns aggregated metrics per namespace
func (h *MetricsHandler) GetNamespaceMetrics(c fiber.Ctx) error {
	ctx := context.Background()
	
	// Query for namespace CPU usage
	cpuQuery := "sum(rate(container_cpu_usage_seconds_total{container!=''}[5m])) by (namespace)"
	cpuResult, err := h.promClient.Query(ctx, cpuQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch namespace CPU metrics: %v", err),
		})
	}
	
	// Query for namespace memory usage
	memQuery := "sum(container_memory_usage_bytes{container!=''}) by (namespace)"
	memResult, err := h.promClient.Query(ctx, memQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch namespace memory metrics: %v", err),
		})
	}
	
	// Query for pod count per namespace
	podQuery := "count(kube_pod_info) by (namespace)"
	podResult, err := h.promClient.Query(ctx, podQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch pod count: %v", err),
		})
	}
	
	// Build response with namespace metrics
	type NamespaceMetrics struct {
		Name        string  `json:"name"`
		CPUUsage    float64 `json:"cpuUsage"`    // CPU usage in cores
		MemoryUsage float64 `json:"memoryUsage"` // Memory usage in bytes
		PodCount    int     `json:"podCount"`    // Number of pods
	}
	
	namespaceMetricsMap := make(map[string]*NamespaceMetrics)
	
	// Process CPU metrics
	for _, result := range cpuResult.Data.Result {
		namespace := result.Metric["namespace"]
		if _, exists := namespaceMetricsMap[namespace]; !exists {
			namespaceMetricsMap[namespace] = &NamespaceMetrics{Name: namespace}
		}
		
		cpuUsage, _, err := query.FormatValue(result.Value)
		if err == nil {
			namespaceMetricsMap[namespace].CPUUsage = cpuUsage
		}
	}
	
	// Process memory metrics
	for _, result := range memResult.Data.Result {
		namespace := result.Metric["namespace"]
		if _, exists := namespaceMetricsMap[namespace]; !exists {
			namespaceMetricsMap[namespace] = &NamespaceMetrics{Name: namespace}
		}
		
		memUsage, _, err := query.FormatValue(result.Value)
		if err == nil {
			namespaceMetricsMap[namespace].MemoryUsage = memUsage
		}
	}
	
	// Process pod count
	for _, result := range podResult.Data.Result {
		namespace := result.Metric["namespace"]
		if _, exists := namespaceMetricsMap[namespace]; !exists {
			namespaceMetricsMap[namespace] = &NamespaceMetrics{Name: namespace}
		}
		
		podCount, _, err := query.FormatValue(result.Value)
		if err == nil {
			namespaceMetricsMap[namespace].PodCount = int(podCount)
		}
	}
	
	// Convert map to slice
	namespaceMetrics := make([]NamespaceMetrics, 0, len(namespaceMetricsMap))
	for _, metrics := range namespaceMetricsMap {
		namespaceMetrics = append(namespaceMetrics, *metrics)
	}
	
	return c.Status(fiber.StatusOK).JSON(namespaceMetrics)
}