package handlers

import (
	"log/slog"

	"github.com/gofiber/fiber/v3"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/handlers/kubernetes"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/handlers/prometheus"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/middleware"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/middleware/metrics"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/config"
	prometheusclient "github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/prometheus_client"
)

type Handler struct {
	log            *slog.Logger
	authMiddleware *middleware.AuthenticationMiddleware
	router         *fiber.App
	promClient     *prometheusclient.Client
	kubeMetrics    *kubernetes.MetricsHandler
	promMetrics    *prometheus.MetricsHandler
}

func (h *Handler) Run() error {
	return h.router.Listen(":8000")
}

func NewHandler(log *slog.Logger, auth *middleware.AuthenticationMiddleware) *Handler {
	cfg := config.NewConfig()
	promClient := prometheusclient.NewClient()
	kubeMetrics := kubernetes.NewMetricsHandler(cfg.PrometheusURL)
	promMetrics := prometheus.NewMetricsHandler(cfg.PrometheusURL)
	return &Handler{
		log:            log,
		authMiddleware: auth,
		promClient:     promClient,
		kubeMetrics:    kubeMetrics,
		promMetrics:    promMetrics,
	}
}

func (h *Handler) InitRoutes(cfg fiber.Config) {
	router := fiber.New(cfg)
	h.router = router

	// Add metrics middleware to all routes
	router.Use(metrics.Middleware(h.promClient))

	api := router.Group("/api")

	// Unsecure ping
	api.Get("/ping", h.ping)

	// Public metrics endpoint
	api.Get("/metrics", h.metricsHandler)

	v1 := api.Group("/v1")
	v1.Use(h.authMiddleware.Authenticate)

	v1.Post("/scale", h.scaleHandler)
	v1.Post("/restart", h.restartHandler)
	v1.Post("/rollback", h.rollbackHandler)

	// Kubernetes metrics endpoints
	kubernetes := v1.Group("/kubernetes")
	kubernetes.Get("/metrics/cluster", h.kubeMetrics.GetClusterMetrics)
	kubernetes.Get("/metrics/nodes", h.kubeMetrics.GetNodeMetrics)
	kubernetes.Get("/metrics/pods", h.kubeMetrics.GetPodMetrics)
	kubernetes.Get("/metrics/namespaces", h.kubeMetrics.GetNamespaceMetrics)

	// Prometheus metrics endpoints
	prometheusGroup := v1.Group("/prometheus")
	prometheusGroup.Get("/metrics/basic", h.promMetrics.GetBasicMetrics)
	prometheusGroup.Get("/metrics/list", h.promMetrics.MetricsList)
	prometheusGroup.Get("/metrics/:name", h.promMetrics.QueryMetric)
	prometheusGroup.Post("/query", h.promMetrics.CustomQuery)

	// Secure ping
	v1.Get("/ping", h.ping)
}

func (h *Handler) metricsHandler(c fiber.Ctx) error {
	// Use our custom metrics handler
	return h.promClient.MetricsHandler()(c)
}

func (h *Handler) scaleHandler(c fiber.Ctx) error {
	// TODO: implement
	return c.Status(fiber.StatusNotImplemented).JSON(fiber.Map{
		"status":  "error",
		"message": "Scaling operation not implemented",
	})
}

func (h *Handler) restartHandler(c fiber.Ctx) error {
	// TODO: implement
	return c.Status(fiber.StatusNotImplemented).JSON(fiber.Map{
		"status":  "error",
		"message": "Scaling operation not implemented",
	})
}

func (h *Handler) rollbackHandler(c fiber.Ctx) error {
	// TODO: implement
	return c.Status(fiber.StatusNotImplemented).JSON(fiber.Map{
		"status":  "error",
		"message": "Scaling operation not implemented",
	})
}

func (h *Handler) ping(c fiber.Ctx) error {
	return c.Status(fiber.StatusOK).SendString("Pong")
}
