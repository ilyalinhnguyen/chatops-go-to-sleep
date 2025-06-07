package prometheusclient

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Client provides methods to interact with Prometheus metrics
type Client struct {
	registry      *prometheus.Registry
	httpMetrics   *HTTPMetrics
	appMetrics    *AppMetrics
	prometheusURL string
	httpClient    *http.Client
}

// HTTPMetrics contains HTTP-related metrics
type HTTPMetrics struct {
	RequestsTotal   *prometheus.CounterVec
	RequestDuration *prometheus.HistogramVec
	ResponseSize    *prometheus.HistogramVec
}

// AppMetrics contains application-specific metrics
type AppMetrics struct {
	ScaleOperationsTotal  prometheus.Counter
	RestartOperationsTotal prometheus.Counter
	RollbackOperationsTotal prometheus.Counter
	ErrorsTotal           prometheus.Counter
}

// Alert represents a Prometheus alert
type Alert struct {
	Labels      map[string]string `json:"labels"`
	Annotations map[string]string `json:"annotations"`
	State       string            `json:"state"`
	ActiveAt    time.Time         `json:"activeAt"`
	Value       string            `json:"value"`
}

// AlertsResponse represents the Prometheus alerts API response
type AlertsResponse struct {
	Status string `json:"status"`
	Data   struct {
		Alerts []Alert `json:"alerts"`
	} `json:"data"`
}

// NewClient creates a new Prometheus client
func NewClient(prometheusURL string) *Client {
	registry := prometheus.NewRegistry()
	registry.MustRegister(prometheus.NewProcessCollector(prometheus.ProcessCollectorOpts{}))
	registry.MustRegister(prometheus.NewGoCollector())

	httpMetrics := &HTTPMetrics{
		RequestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "http_requests_total",
				Help: "Total number of HTTP requests",
			},
			[]string{"method", "path", "status"},
		),
		RequestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "http_request_duration_seconds",
				Help:    "Duration of HTTP requests in seconds",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"method", "path"},
		),
		ResponseSize: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "http_response_size_bytes",
				Help:    "Size of HTTP responses in bytes",
				Buckets: []float64{100, 1000, 10000, 100000, 1000000},
			},
			[]string{"method", "path"},
		),
	}

	appMetrics := &AppMetrics{
		ScaleOperationsTotal: promauto.NewCounter(prometheus.CounterOpts{
			Name: "app_scale_operations_total",
			Help: "Total number of scale operations",
		}),
		RestartOperationsTotal: promauto.NewCounter(prometheus.CounterOpts{
			Name: "app_restart_operations_total",
			Help: "Total number of restart operations",
		}),
		RollbackOperationsTotal: promauto.NewCounter(prometheus.CounterOpts{
			Name: "app_rollback_operations_total",
			Help: "Total number of rollback operations",
		}),
		ErrorsTotal: promauto.NewCounter(prometheus.CounterOpts{
			Name: "app_errors_total",
			Help: "Total number of application errors",
		}),
	}

	registry.MustRegister(
		httpMetrics.RequestsTotal,
		httpMetrics.RequestDuration,
		httpMetrics.ResponseSize,
		appMetrics.ScaleOperationsTotal,
		appMetrics.RestartOperationsTotal,
		appMetrics.RollbackOperationsTotal,
		appMetrics.ErrorsTotal,
	)

	return &Client{
		registry:      registry,
		httpMetrics:   httpMetrics,
		appMetrics:    appMetrics,
		prometheusURL: prometheusURL,
		httpClient:    &http.Client{},
	}
}

// GetRegistry returns the Prometheus registry
func (c *Client) GetRegistry() *prometheus.Registry {
	return c.registry
}

// GetHTTPMetrics returns the HTTP metrics
func (c *Client) GetHTTPMetrics() *HTTPMetrics {
	return c.httpMetrics
}

// GetAppMetrics returns the application-specific metrics
func (c *Client) GetAppMetrics() *AppMetrics {
	return c.appMetrics
}

// IncrementScaleOperations increments the scale operations counter
func (c *Client) IncrementScaleOperations() {
	c.appMetrics.ScaleOperationsTotal.Inc()
}

// IncrementRestartOperations increments the restart operations counter
func (c *Client) IncrementRestartOperations() {
	c.appMetrics.RestartOperationsTotal.Inc()
}

// IncrementRollbackOperations increments the rollback operations counter
func (c *Client) IncrementRollbackOperations() {
	c.appMetrics.RollbackOperationsTotal.Inc()
}

// IncrementErrors increments the error counter
func (c *Client) IncrementErrors() {
	c.appMetrics.ErrorsTotal.Inc()
}


// GetAllAlerts retrieves all alerts from Prometheus
func (c *Client) GetAllAlerts(ctx context.Context) ([]Alert, error) {
	if c.prometheusURL == "" {
		return nil, fmt.Errorf("prometheus URL not set, use WithPrometheusURL()")
	}

	endpoint := fmt.Sprintf("%s/api/v1/alerts", c.prometheusURL)

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("error creating request: %v", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error querying Prometheus: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("error response from Prometheus: %s", resp.Status)
	}

	var response AlertsResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return nil, fmt.Errorf("error decoding response: %v", err)
	}

	return response.Data.Alerts, nil
}

// GetActiveAlerts retrieves only the currently firing alerts from Prometheus
func (c *Client) GetActiveAlerts(ctx context.Context) ([]Alert, error) {
	// Get all alerts
	alerts, err := c.GetAllAlerts(ctx)
	if err != nil {
		return nil, err
	}

	// Filter for only firing alerts
	var activeAlerts []Alert
	for _, alert := range alerts {
		if alert.State == "firing" {
			activeAlerts = append(activeAlerts, alert)
		}
	}

	return activeAlerts, nil
}

// QueryAlerts executes a PromQL query and returns the results
func (c *Client) QueryAlerts(ctx context.Context, query string) (map[string]interface{}, error) {
	if c.prometheusURL == "" {
		return nil, fmt.Errorf("prometheus URL not set, use WithPrometheusURL()")
	}

	endpoint := fmt.Sprintf("%s/api/v1/query", c.prometheusURL)

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("error creating request: %v", err)
	}

	q := req.URL.Query()
	q.Add("query", query)
	req.URL.RawQuery = q.Encode()

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error querying Prometheus: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("error response from Prometheus: %s", resp.Status)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("error decoding response: %v", err)
	}

	return result, nil
}

// GetActiveAlertsWithQuery retrieves only firing alerts using a direct PromQL query
func (c *Client) GetActiveAlertsWithQuery(ctx context.Context) ([]Alert, error) {
	// This PromQL query gets all firing alerts
	const query = "ALERTS{state=\"firing\"}"

	result, err := c.QueryAlerts(ctx, query)
	if err != nil {
		return nil, err
	}

	// Convert query results to Alert objects
	var alerts []Alert

	// Parse the nested data structure
	if data, ok := result["data"].(map[string]interface{}); ok {
		if resultList, ok := data["result"].([]interface{}); ok {
			for _, item := range resultList {
				if resultItem, ok := item.(map[string]interface{}); ok {
					// Extract metric labels
					var labels map[string]string
					if metric, ok := resultItem["metric"].(map[string]interface{}); ok {
						labels = make(map[string]string)
						for k, v := range metric {
							if strVal, ok := v.(string); ok {
								labels[k] = strVal
							}
						}
					}

					// Extract value
					var value string
					if valueArr, ok := resultItem["value"].([]interface{}); ok && len(valueArr) >= 2 {
						value = fmt.Sprintf("%v", valueArr[1])
					}

					alert := Alert{
						Labels: labels,
						State:  "firing", // These are all firing alerts
						Value:  value,
					}

					alerts = append(alerts, alert)
				}
			}
		}
	}

	return alerts, nil
}

// GetAlertRules retrieves all alert rules from Prometheus
func (c *Client) GetAlertRules(ctx context.Context) (map[string]interface{}, error) {
	if c.prometheusURL == "" {
		return nil, fmt.Errorf("prometheus URL not set, use WithPrometheusURL()")
	}

	endpoint := fmt.Sprintf("%s/api/v1/rules", c.prometheusURL)

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("error creating request: %v", err)
	}

	// Add alerting filter to only get alerts
	q := req.URL.Query()
	q.Add("type", "alert")
	req.URL.RawQuery = q.Encode()

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error querying Prometheus: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("error response from Prometheus: %s", resp.Status)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("error decoding response: %v", err)
	}

	return result, nil
}
