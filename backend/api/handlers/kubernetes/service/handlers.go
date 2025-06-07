package service

import (
	"context"
	"log/slog"
	"time"

	"github.com/gofiber/fiber/v3"
	"github.com/google/uuid"
	kuberclient "github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/kuber_client"
)

type Handler struct {
	log        *slog.Logger
	kubeClient *kuberclient.Client
}

// NewHandler creates a new Kubernetes service handler
// It accepts an existing kubeClient to avoid creating multiple instances
func NewHandler(log *slog.Logger, kubeClient *kuberclient.Client) (*Handler, error) {
	// If no client is provided, attempt to create one
	var err error
	if kubeClient == nil {
		kubeClient, err = kuberclient.NewClient()
		if err != nil {
			return nil, err
		}
	}

	return &Handler{
		log:        log,
		kubeClient: kubeClient,
	}, nil
}

type ScaleRequest struct {
	Namespace string `json:"namespace"`
	Name      string `json:"name"`
	Replicas  int32  `json:"replicas"`
}

type RestartRequest struct {
	Namespace string `json:"namespace"`
	Name      string `json:"name"`
}

type RollbackRequest struct {
	Namespace     string `json:"namespace"`
	Name          string `json:"name"`
	RevisionID    string `json:"revisionId,omitempty"`    // Specific revision ID
	RevisionImage string `json:"revisionImage,omitempty"` // Specific image
	Version       string `json:"version,omitempty"`       // Specific version
}

type UpdateRequest struct {
	Namespace string `json:"namespace"`
	Name      string `json:"name"`
	Image     string `json:"image,omitempty"`
	Version   string `json:"version,omitempty"`
}

type StatusRequest struct {
	Namespace string `json:"namespace"`
	Name      string `json:"name"`
}

func (h *Handler) ScaleService(c fiber.Ctx) error {
	op := "ScaleService" + uuid.NewString()
	log := h.log.With(slog.String("op", op))

	var req ScaleRequest
	if err := c.Bind().Body(&req); err != nil {
		log.Error("Failed to parse scale request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
		log.Error("Invalid name", "error", "name is empty string")
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Service name is required",
		})
	}

	if req.Replicas < 0 {
		log.Error("Invalid replicas", "error", "replicas num is negative")
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Replicas must be a non-negative integer",
		})
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	err := h.kubeClient.ScaleDeployment(ctx, kuberclient.ServiceConfig{
		Namespace: req.Namespace,
		Name:      req.Name,
		Replicas:  req.Replicas,
	})

	if err != nil {
		log.Error("Failed to scale service", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to scale service",
			"error":   err.Error(),
		})
	}

	log.Info("Service scaled successfully", "service", req.Name, "namespace", req.Namespace, "replicas", req.Replicas)
	return c.Status(fiber.StatusOK).JSON(fiber.Map{
		"status":  "success",
		"message": "Service scaled successfully",
		"data": fiber.Map{
			"name":      req.Name,
			"namespace": req.Namespace,
			"replicas":  req.Replicas,
		},
	})
}

func (h *Handler) RestartService(c fiber.Ctx) error {
	op := "RestartService" + uuid.NewString()
	log := h.log.With(slog.String("op", op))

	var req RestartRequest
	if err := c.Bind().Body(&req); err != nil {
		log.Error("Failed to parse restart request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
		log.Error("Invalid name", "error", "name is empty string")
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Service name is required",
		})
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	err := h.kubeClient.RestartDeployment(ctx, kuberclient.ServiceConfig{
		Namespace: req.Namespace,
		Name:      req.Name,
	})

	if err != nil {
		log.Error("Failed to restart service", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to restart service",
			"error":   err.Error(),
		})
	}

	log.Info("Service restarted successfully", "service", req.Name, "namespace", req.Namespace)
	return c.Status(fiber.StatusOK).JSON(fiber.Map{
		"status":  "success",
		"message": "Service restarted successfully",
		"data": fiber.Map{
			"name":      req.Name,
			"namespace": req.Namespace,
		},
	})
}

func (h *Handler) RollbackService(c fiber.Ctx) error {
	op := "RollbackService" + uuid.NewString()
	log := h.log.With(slog.String("op", op))

	var req RollbackRequest
	if err := c.Bind().Body(&req); err != nil {
		log.Error("Failed to parse rollback request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
		log.Error("Invalid name", "error", "name is empty string")
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Service name is required",
		})
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	err := h.kubeClient.RollbackDeployment(ctx, kuberclient.ServiceConfig{
		Namespace:     req.Namespace,
		Name:          req.Name,
		RevisionID:    req.RevisionID,
		RevisionImage: req.RevisionImage,
		Version:       req.Version,
	})

	if err != nil {
		log.Error("Failed to rollback service", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to rollback service",
			"error":   err.Error(),
		})
	}

	log.Info("Service rolled back successfully", "service", req.Name, "namespace", req.Namespace)
	return c.Status(fiber.StatusOK).JSON(fiber.Map{
		"status":  "success",
		"message": "Service rolled back successfully",
		"data": fiber.Map{
			"name":          req.Name,
			"namespace":     req.Namespace,
			"revisionId":    req.RevisionID,
			"revisionImage": req.RevisionImage,
			"version":       req.Version,
		},
	})
}

func (h *Handler) UpdateService(c fiber.Ctx) error {
	op := "UpdateService" + uuid.NewString()
	log := h.log.With(slog.String("op", op))

	var req UpdateRequest
	if err := c.Bind().Body(&req); err != nil {
		log.Error("Failed to parse update request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
		log.Error("Invalid name", "error", "name is empty string")
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Service name is required",
		})
	}

	if req.Image == "" && req.Version == "" {
		log.Error("Invalid image and version", "error", "image or version is empty string")
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Either image or version must be specified",
		})
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	err := h.kubeClient.UpdateDeployment(ctx, kuberclient.ServiceConfig{
		Namespace: req.Namespace,
		Name:      req.Name,
		Image:     req.Image,
		Version:   req.Version,
	})

	if err != nil {
		log.Error("Failed to update service", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to update service",
			"error":   err.Error(),
		})
	}

	log.Info("Service updated successfully", "service", req.Name, "namespace", req.Namespace)
	return c.Status(fiber.StatusOK).JSON(fiber.Map{
		"status":  "success",
		"message": "Service updated successfully",
		"data": fiber.Map{
			"name":      req.Name,
			"namespace": req.Namespace,
			"image":     req.Image,
			"version":   req.Version,
		},
	})
}

func (h *Handler) GetServiceStatus(c fiber.Ctx) error {
	op := "GetServiceStatus" + uuid.NewString()
	log := h.log.With(slog.String("op", op))

	var req StatusRequest
	if err := c.Bind().Body(&req); err != nil {
		log.Error("Failed to parse status request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
		log.Error("Invalid name", "error", "name is empty string")
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Service name is required",
		})
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	status, err := h.kubeClient.GetDeploymentStatus(ctx, req.Namespace, req.Name)
	if err != nil {
		log.Error("Failed to get service status", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to get service status",
			"error":   err.Error(),
		})
	}

	log.Info("Service status retrieved successfully", "service", req.Name, "namespace", req.Namespace)
	return c.Status(fiber.StatusOK).JSON(fiber.Map{
		"status":  "success",
		"message": "Service status retrieved successfully",
		"data":    status,
	})
}
