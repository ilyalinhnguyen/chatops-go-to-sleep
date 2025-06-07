package prometheusclient

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Client provides methods to interact with Prometheus metrics
type Client struct {
	registry    *prometheus.Registry
	httpMetrics *HTTPMetrics
	appMetrics  *AppMetrics
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

// NewClient creates a new Prometheus client
func NewClient() *Client {
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
		registry:    registry,
		httpMetrics: httpMetrics,
		appMetrics:  appMetrics,
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