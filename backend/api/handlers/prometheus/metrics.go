package prometheus

import (
	"context"
	"fmt"
	"time"

	"github.com/gofiber/fiber/v3"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/prometheus_client/query"
)

// MetricsHandler handles Prometheus metrics requests
type MetricsHandler struct {
	promClient *query.PrometheusClient
}

func NewMetricsHandler(promURL string) *MetricsHandler {
	return &MetricsHandler{
		promClient: query.NewPrometheusClient(promURL),
	}
}

type BasicMetrics struct {
	UpStatus    bool    `json:"upStatus"`
	CPUUsage    float64 `json:"cpuUsage"`
	MemoryUsage float64 `json:"memoryUsage"`
	Timestamp   string  `json:"timestamp"`
}

func (h *MetricsHandler) GetBasicMetrics(c fiber.Ctx) error {
	ctx := context.Background()

	upQuery := "up"
	upResult, err := h.promClient.Query(ctx, upQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch up status: %v", err),
		})
	}

	cpuQuery := "rate(process_cpu_seconds_total[1m])"
	cpuResult, err := h.promClient.Query(ctx, cpuQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch CPU metrics: %v", err),
		})
	}

	memQuery := "process_resident_memory_bytes"
	memResult, err := h.promClient.Query(ctx, memQuery, time.Now())
	if err != nil {
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
	ctx := context.Background()

	// Query for all available metrics
	metricListQuery := "{__name__=~\".+\"}"
	result, err := h.promClient.Query(ctx, metricListQuery, time.Now())
	if err != nil {
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
	ctx := context.Background()

	metricName := c.Params("name")
	if metricName == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Metric name is required",
		})
	}

	metricQuery := metricName
	result, err := h.promClient.Query(ctx, metricQuery, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to fetch metric %s: %v", metricName, err),
		})
	}

	if len(result.Data.Result) == 0 {
		return c.Status(fiber.StatusNotFound).JSON(fiber.Map{
			"error": fmt.Sprintf("No data found for metric %s", metricName),
		})
	}

	return c.Status(fiber.StatusOK).JSON(result.Data)
}

// CustomQuery allows running a custom PromQL query
func (h *MetricsHandler) CustomQuery(c fiber.Ctx) error {
	ctx := context.Background()

	var body struct {
		Query string `json:"query"`
	}

	if err := c.Bind().Body(&body); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	if body.Query == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Query is required",
		})
	}

	result, err := h.promClient.Query(ctx, body.Query, time.Now())
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": fmt.Sprintf("Failed to execute query: %v", err),
		})
	}

	return c.Status(fiber.StatusOK).JSON(result)
}
