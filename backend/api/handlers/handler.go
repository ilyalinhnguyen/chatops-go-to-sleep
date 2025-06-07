package handlers

import (
	"fmt"
	"log/slog"

	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/log"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/handlers/kubernetes"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/handlers/kubernetes/service"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/handlers/prometheus"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/middleware"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/middleware/metrics"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/config"
	kuberclient "github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/kuber_client"
	prometheusclient "github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/prometheus_client"
)

type Handler struct {
	log            *slog.Logger
	authMiddleware *middleware.AuthenticationMiddleware
	router         *fiber.App
	promClient     *prometheusclient.Client
	kubeClient     *kuberclient.Client
	kubeMetrics    *kubernetes.MetricsHandler
	promMetrics    *prometheus.MetricsHandler
	kubeService    *service.Handler
}

func (h *Handler) Run() error {

	for _, route := range h.router.GetRoutes() {
		fmt.Printf("[%s] %s\n", route.Method, route.Path)
	}

	return h.router.Listen(":8000")
}

func NewHandler(log *slog.Logger, auth *middleware.AuthenticationMiddleware) *Handler {
	cfg := config.NewConfig()
	promClient := prometheusclient.NewClient()

	// Initialize Kubernetes client once
	kubeClient, err := kuberclient.NewClient()
	if err != nil {
		log.Error("Failed to initialize Kubernetes client", "error", err)
		// Continue without Kubernetes client
	}

	// Pass the Kubernetes client to both the metrics handler and service handler
	kubeMetrics := kubernetes.NewMetricsHandler(log, kubeClient)
	promMetrics := prometheus.NewMetricsHandler(log, cfg.PrometheusURL)

	// Initialize Kubernetes service handler with the same client
	var kubeService *service.Handler
	if kubeClient != nil {
		kubeService, err = service.NewHandler(log, kubeClient)
		if err != nil {
			log.Error("Failed to initialize Kubernetes service handler", "error", err)
			// Continue without Kubernetes service handler
		}
	} else {
		log.Warn("Skipping Kubernetes service handler initialization due to missing Kubernetes client")
	}

	return &Handler{
		log:            log,
		authMiddleware: auth,
		promClient:     promClient,
		kubeClient:     kubeClient,
		kubeMetrics:    kubeMetrics,
		promMetrics:    promMetrics,
		kubeService:    kubeService,
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

	kubeMetrics := kubernetes.Group("/metrics")
	kubeMetrics.Get("/cluster", h.kubeMetrics.GetClusterMetrics)
	kubeMetrics.Get("/nodes", h.kubeMetrics.GetNodeMetrics)
	kubeMetrics.Get("/pods", h.kubeMetrics.GetPodMetrics)
	kubeMetrics.Get("/namespaces", h.kubeMetrics.GetNamespaceMetrics)
	kubeMetrics.Get("/deployments", h.kubeMetrics.GetDeploymentsMetrics)
	kubeMetrics.Get("/deployments/:name", h.kubeMetrics.GetDeploymentStatus)

	// Kubernetes service operations
	kubeServiceGroup := kubernetes.Group("/service")
	kubeServiceGroup.Post("/scale", h.kubeService.ScaleService)
	kubeServiceGroup.Post("/restart", h.kubeService.RestartService)
	kubeServiceGroup.Post("/rollback", h.kubeService.RollbackService)
	kubeServiceGroup.Post("/update", h.kubeService.UpdateService)
	kubeServiceGroup.Post("/status", h.kubeService.GetServiceStatus)

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
	if h.kubeService == nil {
		log.Error("Kubernetes service handler not available", "error", "kuber service is nil")
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"status":  "error",
			"message": "Kubernetes service handler not available",
		})
	}

	var req struct {
		Namespace string `json:"namespace"`
		Name      string `json:"name"`
		Replicas  int32  `json:"replicas"`
	}

	if err := c.Bind().Body(&req); err != nil {
		log.Error("Failed to parse request body", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
		})
	}

	return h.kubeService.ScaleService(c)
}

func (h *Handler) restartHandler(c fiber.Ctx) error {
	if h.kubeService == nil {
		log.Error("Kubernetes service handler not available", "error", "kuber service is nil")
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"status":  "error",
			"message": "Kubernetes service handler not available",
		})
	}

	var req struct {
		Namespace string `json:"namespace"`
		Name      string `json:"name"`
	}

	if err := c.Bind().Body(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
		})
	}

	return h.kubeService.RestartService(c)
}

func (h *Handler) rollbackHandler(c fiber.Ctx) error {
	if h.kubeService == nil {
		log.Error("Kubernetes service handler not available", "error", "kuber service is nil")
		return c.Status(fiber.StatusServiceUnavailable).JSON(fiber.Map{
			"status":  "error",
			"message": "Kubernetes service handler not available",
		})
	}

	var req struct {
		Namespace     string `json:"namespace"`
		Name          string `json:"name"`
		RevisionID    string `json:"revisionId,omitempty"`
		RevisionImage string `json:"revisionImage,omitempty"`
		Version       string `json:"version,omitempty"`
	}

	if err := c.Bind().Body(&req); err != nil {
		log.Error("Failed to parse request body", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
		})
	}

	return h.kubeService.RollbackService(c)
}

func (h *Handler) ping(c fiber.Ctx) error {
	return c.Status(fiber.StatusOK).SendString("Pong")
}
