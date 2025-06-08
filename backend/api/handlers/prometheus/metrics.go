package prometheus

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/gofiber/fiber/v3"
	"github.com/google/uuid"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/prometheus_client/query"
)

// MetricsHandler handles Prometheus metrics requests
type MetricsHandler struct {
	log        *slog.Logger
	promClient *query.PrometheusClient
}

func NewMetricsHandler(log *slog.Logger, promURL string) *MetricsHandler {
	return &MetricsHandler{
		log:        log,
		promClient: query.NewPrometheusClient(promURL),
	}
}

type BasicMetrics struct {
	UpStatus    bool    `json:"upStatus"`
	CPUUsage    float64 `json:"cpuUsage"`
	MemoryUsage float64 `json:"memoryUsage"`
	Timestamp   string  `json:"timestamp"`
}

type AlertInfo struct {
	Name        string            `json:"name"`
	Severity    string            `json:"severity"`
	State       string            `json:"state"`
	Summary     string            `json:"summary"`
	Description string            `json:"description"`
	ActiveSince *time.Time        `json:"activeSince,omitempty"`
	Labels      map[string]string `json:"labels"`
	Value       string            `json:"value,omitempty"`
}


func (h *MetricsHandler) GetBasicMetrics(c fiber.Ctx) error {
	op := "GetBasicMetrics" + uuid.NewString()
	log := h.log.With(slog.String("op", op))

	ctx := context.Background()

	upQuery := "up"
	upResult, err := h.promClient.Query(ctx, upQuery, time.Now())
	if err != nil {
		log.Error("Failed to fetch up status", "error", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch up status: %v", err),
		})
	}

	cpuQuery := "rate(process_cpu_seconds_total[1m])"
	cpuResult, err := h.promClient.Query(ctx, cpuQuery, time.Now())
	if err != nil {
		log.Error("Failed to fetch CPU metrics", "error", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch CPU metrics: %v", err),
		})
	}

	memQuery := "process_resident_memory_bytes"
	memResult, err := h.promClient.Query(ctx, memQuery, time.Now())
	if err != nil {
		log.Error("Failed to fetch memory metrics", "error", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch memory metrics: %v", err),
		})
	}

	// Parse results
	var upStatus bool = false
	var cpuUsage, memUsage float64
	var timestamp time.Time

	if len(upResult.Data.Result) > 0 {
		upValue, ts, err := query.FormatValue(upResult.Data.Result[0].Value)
		if err == nil {
			upStatus = upValue > 0
			timestamp = ts
		}
	}

	if len(cpuResult.Data.Result) > 0 {
		cpuUsage, _, err = query.FormatValue(cpuResult.Data.Result[0].Value)
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

	metrics := BasicMetrics{
		UpStatus:    upStatus,
		CPUUsage:    cpuUsage,
		MemoryUsage: memUsage,
		Timestamp:   timestamp.Format(time.RFC3339),
	}

	return c.Status(fiber.StatusOK).JSON(metrics)
}

func (h *MetricsHandler) MetricsList(c fiber.Ctx) error {
	op := "MetricsList" + uuid.NewString()
	log := h.log.With(slog.String("op", op))

	ctx := context.Background()

	// Query for all available metrics
	metricListQuery := "{__name__=~\".+\"}"
	result, err := h.promClient.Query(ctx, metricListQuery, time.Now())
	if err != nil {
		log.Error("Failed to fetch metrics list", "error", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch metrics list: %v", err),
		})
	}

	metricNames := make([]string, 0, len(result.Data.Result))
	for _, metric := range result.Data.Result {
		if name, ok := metric.Metric["__name__"]; ok {
			metricNames = append(metricNames, name)
		}
	}

	return c.Status(fiber.StatusOK).JSON(fiber.Map{
		"metrics": metricNames,
	})
}

func (h *MetricsHandler) QueryMetric(c fiber.Ctx) error {
	op := "QueryMetric" + uuid.NewString()
	log := h.log.With(slog.String("op", op))

	ctx := context.Background()

	metricName := c.Params("name")
	if metricName == "" {
		log.Error("Invalid metric name", "error", "metric name is empty string")
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Metric name is required",
		})
	}

	metricQuery := metricName
	result, err := h.promClient.Query(ctx, metricQuery, time.Now())
	if err != nil {
		log.Error("Failed to fetch metrics", "error", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch metric %s: %v", metricName, err),
		})
	}

	if len(result.Data.Result) == 0 {
		log.Error("Invalid data","error","data len is 0")
		return c.Status(fiber.StatusNotFound).JSON(fiber.Map{
			"error": fmt.Sprintf("No data found for metric %s", metricName),
		})
	}

	return c.Status(fiber.StatusOK).JSON(result.Data)
}

// CustomQuery allows running a custom PromQL query
func (h *MetricsHandler) CustomQuery(c fiber.Ctx) error {
	op := "CustomQuery" + uuid.NewString()
	log := h.log.With(slog.String("op", op))

	ctx := context.Background()

	var body struct {
		Query string `json:"query"`
	}

	if err := c.Bind().Body(&body); err != nil {
		log.Error("Failed to parse request body", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	if body.Query == "" {
		log.Error("Invalid query", "error", "query is empty string")
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Query is required",
		})
	}

	result, err := h.promClient.Query(ctx, body.Query, time.Now())
	if err != nil {
		log.Error("Failed to execute query", "error", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to execute query: %v", err),
		})
	}

	return c.Status(fiber.StatusOK).JSON(result)
}

func (h *MetricsHandler) GetAlerts(c fiber.Ctx) error {
	if h.promClient == nil {
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"error": "Prometheus client not available",
		})
	}

	ctx := context.Background()
	alerts, err := h.promClient.GetAlerts(ctx)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch alerts: %v", err),
		})
	}

	// Convert to our response format
	alertInfos := make([]AlertInfo, 0, len(alerts))
	for _, alert := range alerts {
		info := AlertInfo{
			Name:     alert.Labels["alertname"],
			Severity: alert.Labels["severity"],
			State:    alert.State,
			Labels:   alert.Labels,
			Value:    alert.Value,
		}

		// Extract summary and description from annotations
		if summary, ok := alert.Annotations["summary"]; ok {
			info.Summary = summary
		}
		if description, ok := alert.Annotations["description"]; ok {
			info.Description = description
		}

		// Add active time if available
		if !alert.ActiveAt.IsZero() {
			info.ActiveSince = &alert.ActiveAt
		}

		alertInfos = append(alertInfos, info)
	}

	return c.Status(fiber.StatusOK).JSON(alertInfos)
}

// GetAlertRules returns all alert rules from Prometheus
func (h *MetricsHandler) GetAlertRules(c fiber.Ctx) error {
	if h.promClient == nil {
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"error": "Prometheus client not available",
		})
	}

	ctx := context.Background()
	rules, err := h.promClient.QueryRules(ctx)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch alert rules: %v", err),
		})
	}

	return c.Status(fiber.StatusOK).JSON(rules)
}

// QueryAlerts allows custom PromQL queries for alerts
func (h *MetricsHandler) QueryAlerts(c fiber.Ctx) error {
	if h.promClient == nil {
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"error": "Prometheus client not available",
		})
	}

	query := c.Query("query")
	if query == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Query parameter is required",
		})
	}

	ctx := context.Background()
	result, err := h.promClient.QueryAlerts(ctx, query)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to execute query: %v", err),
		})
	}

	return c.Status(fiber.StatusOK).JSON(result)
}

// GetActiveAlerts returns only the currently firing alerts from Prometheus
func (h *MetricsHandler) GetActiveAlerts(c fiber.Ctx) error {
	if h.promClient == nil {
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"error": "Prometheus client not available",
		})
	}

	ctx := context.Background()
	alerts, err := h.promClient.GetActiveAlerts(ctx)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch active alerts: %v", err),
		})
	}

	// Convert to our response format
	alertInfos := make([]AlertInfo, 0, len(alerts))
	for _, alert := range alerts {
		info := AlertInfo{
			Name:     alert.Labels["alertname"],
			Severity: alert.Labels["severity"],
			State:    alert.State,
			Labels:   alert.Labels,
			Value:    alert.Value,
		}

		// Extract summary and description from annotations
		if summary, ok := alert.Annotations["summary"]; ok {
			info.Summary = summary
		}
		if description, ok := alert.Annotations["description"]; ok {
			info.Description = description
		}

		// Add active time if available
		if !alert.ActiveAt.IsZero() {
			info.ActiveSince = &alert.ActiveAt
		}

		alertInfos = append(alertInfos, info)
	}

	return c.Status(fiber.StatusOK).JSON(alertInfos)
}
