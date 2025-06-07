package metrics

import (
	"strconv"
	"time"

	"github.com/gofiber/fiber/v3"
	prometheusclient "github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/prometheus_client"
)

// Middleware creates a Fiber middleware that collects HTTP metrics
func Middleware(promClient *prometheusclient.Client) fiber.Handler {
	return func(c fiber.Ctx) error {
		// Start timer
		start := time.Now()
		
		// Get request path and method
		path := c.Route().Path
		method := c.Method()
		
		// Process request
		err := c.Next()
		
		// Calculate duration
		duration := time.Since(start).Seconds()
		
		// Get status code
		status := c.Response().StatusCode()
		
		// Record metrics
		promClient.GetHTTPMetrics().RequestsTotal.WithLabelValues(
			method,
			path,
			strconv.Itoa(status),
		).Inc()
		
		promClient.GetHTTPMetrics().RequestDuration.WithLabelValues(
			method,
			path,
		).Observe(duration)
		
		promClient.GetHTTPMetrics().ResponseSize.WithLabelValues(
			method,
			path,
		).Observe(float64(len(c.Response().Body())))
		
		// If there was an error, increment the error counter
		if err != nil {
			promClient.IncrementErrors()
		}
		
		return err
	}
}