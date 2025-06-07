package prometheusclient

import (
	"bytes"
	"net/http"

	"github.com/gofiber/fiber/v3"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// MetricsHandler returns a Fiber handler function that exposes Prometheus metrics
func (c *Client) MetricsHandler() fiber.Handler {
	return func(ctx fiber.Ctx) error {
		var buf bytes.Buffer

		// Create a registry handler
		h := promhttp.HandlerFor(c.registry, promhttp.HandlerOpts{})

		// Create a response writer that writes to our buffer
		w := &responseWriter{
			buffer: &buf,
			header: make(http.Header),
		}

		// Create a minimal request
		req := &http.Request{
			Method: "GET",
		}

		// Call the Prometheus handler
		h.ServeHTTP(w, req)

		// Set the content type
		ctx.Set("Content-Type", "text/plain; version=0.0.4")

		// Write the buffer contents to the response
		return ctx.Status(w.statusCode).Send(buf.Bytes())
	}
}

// responseWriter implements http.ResponseWriter interface
type responseWriter struct {
	buffer     *bytes.Buffer
	header     http.Header
	statusCode int
}

func (w *responseWriter) Header() http.Header {
	return w.header
}

func (w *responseWriter) Write(b []byte) (int, error) {
	if w.statusCode == 0 {
		w.statusCode = http.StatusOK
	}
	return w.buffer.Write(b)
}

func (w *responseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
}
