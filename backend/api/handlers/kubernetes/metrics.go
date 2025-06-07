package kubernetes

import (
	"context"
	"fmt"
	"time"

	"github.com/gofiber/fiber/v3"
	kuberclient "github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/kuber_client"
)

type MetricsHandler struct {
	kubeClient *kuberclient.Client
}

func NewMetricsHandler(promURL string) *MetricsHandler {
	// We're ignoring the promURL parameter since we're now using the Kubernetes client directly
	client, err := kuberclient.NewClient()
	if err != nil {
		// Log the error but continue - the handler will return appropriate errors when methods are called
		fmt.Printf("Failed to initialize Kubernetes client: %v\n", err)
	}

	return &MetricsHandler{
		kubeClient: client,
	}
}

type ClusterMetrics struct {
	NodeCount     int    `json:"nodeCount"`
	NodesReady    int    `json:"nodesReady"`
	PodCount      int    `json:"podCount"`
	PodsRunning   int    `json:"podsRunning"`
	PodsPending   int    `json:"podsPending"`
	PodsFailed    int    `json:"podsFailed"`
	PodsSucceeded int    `json:"podsSucceeded"`
	Timestamp     string `json:"timestamp"`
}

type NodeMetrics struct {
	Name        string                 `json:"name"`
	Status      string                 `json:"status"`
	Allocatable map[string]interface{} `json:"allocatable"`
	Capacity    map[string]interface{} `json:"capacity"`
	Labels      map[string]string      `json:"labels"`
}

type PodMetrics struct {
	Name       string `json:"name"`
	Namespace  string `json:"namespace"`
	Status     string `json:"status"`
	HostIP     string `json:"hostIP"`
	PodIP      string `json:"podIP"`
	StartTime  string `json:"startTime,omitempty"`
	Containers int    `json:"containers"`
}

func (h *MetricsHandler) GetClusterMetrics(c fiber.Ctx) error {
	if h.kubeClient == nil {
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"error": "Kubernetes client not available",
		})
	}

	ctx := context.Background()
	metrics, err := h.kubeClient.GetClusterMetrics(ctx)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch cluster metrics: %v", err),
		})
	}

	// Convert to our response format
	clusterMetrics := ClusterMetrics{
		NodeCount:     metrics["nodes_total"].(int),
		NodesReady:    metrics["nodes_ready"].(int),
		PodCount:      metrics["pods_total"].(int),
		PodsRunning:   metrics["pods_running"].(int),
		PodsPending:   metrics["pods_pending"].(int),
		PodsFailed:    metrics["pods_failed"].(int),
		PodsSucceeded: metrics["pods_succeeded"].(int),
		Timestamp:     time.Now().Format(time.RFC3339),
	}

	return c.Status(fiber.StatusOK).JSON(clusterMetrics)
}

func (h *MetricsHandler) GetNodeMetrics(c fiber.Ctx) error {
	if h.kubeClient == nil {
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"error": "Kubernetes client not available",
		})
	}

	ctx := context.Background()
	nodeName := c.Query("name", "") // Optional node name filter

	metrics, err := h.kubeClient.GetNodeMetrics(ctx, nodeName)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch node metrics: %v", err),
		})
	}

	// Convert to our response format
	nodeMetrics := make([]NodeMetrics, 0, len(metrics))
	for _, nodeData := range metrics {
		node := NodeMetrics{
			Name:   nodeData["name"].(string),
			Status: nodeData["status"].(string),
		}

		if allocatable, ok := nodeData["allocatable"].(map[string]interface{}); ok {
			node.Allocatable = allocatable
		}

		if capacity, ok := nodeData["capacity"].(map[string]interface{}); ok {
			node.Capacity = capacity
		}

		if labels, ok := nodeData["labels"].(map[string]interface{}); ok {
			node.Labels = convertMapToStringString(labels)
		}

		nodeMetrics = append(nodeMetrics, node)
	}

	return c.Status(fiber.StatusOK).JSON(nodeMetrics)
}

func (h *MetricsHandler) GetPodMetrics(c fiber.Ctx) error {
	if h.kubeClient == nil {
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"error": "Kubernetes client not available",
		})
	}

	ctx := context.Background()
	namespace := c.Query("namespace", "") // Optional namespace filter

	metrics, err := h.kubeClient.GetPodMetrics(ctx, namespace)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch pod metrics: %v", err),
		})
	}

	// Convert to our response format
	podMetrics := make([]PodMetrics, 0, len(metrics))
	for _, podData := range metrics {
		pod := PodMetrics{
			Name:       podData["name"].(string),
			Namespace:  podData["namespace"].(string),
			Status:     podData["status"].(string),
			Containers: podData["containers"].(int),
		}

		if hostIP, ok := podData["hostIP"].(string); ok {
			pod.HostIP = hostIP
		}

		if podIP, ok := podData["podIP"].(string); ok {
			pod.PodIP = podIP
		}

		// Handle startTime which could be a time.Time or string
		if startTimeData, ok := podData["startTime"]; ok {
			switch st := startTimeData.(type) {
			case time.Time:
				pod.StartTime = st.Format(time.RFC3339)
			case string:
				pod.StartTime = st
			case *time.Time:
				if st != nil {
					pod.StartTime = st.Format(time.RFC3339)
				}
			case map[string]interface{}:
				// Sometimes Kubernetes returns a structured time object
				if timeStr, ok := st["time"].(string); ok {
					pod.StartTime = timeStr
				}
			}
		}

		podMetrics = append(podMetrics, pod)
	}

	return c.Status(fiber.StatusOK).JSON(podMetrics)
}

func (h *MetricsHandler) GetNamespaceMetrics(c fiber.Ctx) error {
	if h.kubeClient == nil {
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"error": "Kubernetes client not available",
		})
	}

	ctx := context.Background()

	// Get pod information to group by namespace
	pods, err := h.kubeClient.GetPodMetrics(ctx, "")
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch pod metrics: %v", err),
		})
	}

	// Group pods by namespace
	type NamespaceMetrics struct {
		Name      string `json:"name"`
		PodCount  int    `json:"podCount"`
		Running   int    `json:"running"`
		Pending   int    `json:"pending"`
		Failed    int    `json:"failed"`
		Succeeded int    `json:"succeeded"`
	}

	namespaceMap := make(map[string]*NamespaceMetrics)

	for _, pod := range pods {
		namespace := pod["namespace"].(string)
		if _, exists := namespaceMap[namespace]; !exists {
			namespaceMap[namespace] = &NamespaceMetrics{
				Name: namespace,
			}
		}

		// Increment pod count
		namespaceMap[namespace].PodCount++

		// Update status counts
		status := pod["status"].(string)
		switch status {
		case "Running":
			namespaceMap[namespace].Running++
		case "Pending":
			namespaceMap[namespace].Pending++
		case "Failed":
			namespaceMap[namespace].Failed++
		case "Succeeded":
			namespaceMap[namespace].Succeeded++
		}
	}

	// Convert map to slice for response
	namespaceMetrics := make([]NamespaceMetrics, 0, len(namespaceMap))
	for _, metrics := range namespaceMap {
		namespaceMetrics = append(namespaceMetrics, *metrics)
	}

	return c.Status(fiber.StatusOK).JSON(namespaceMetrics)
}

// Helper function to convert map[string]interface{} to map[string]string
func convertMapToStringString(m map[string]interface{}) map[string]string {
	result := make(map[string]string)
	for k, v := range m {
		if strValue, ok := v.(string); ok {
			result[k] = strValue
		} else {
			result[k] = fmt.Sprintf("%v", v)
		}
	}
	return result
}