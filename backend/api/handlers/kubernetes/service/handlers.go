package service

import (
	"context"
	"log/slog"
	"time"

	"github.com/gofiber/fiber/v3"
	kuberclient "github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/kuber_client"
)

type Handler struct {
	log        *slog.Logger
	kubeClient *kuberclient.Client
}

func NewHandler(log *slog.Logger) (*Handler, error) {
	kubeClient, err := kuberclient.NewClient()
	if err != nil {
		return nil, err
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
	var req ScaleRequest
	if err := c.Bind().Body(&req); err != nil {
		h.log.Error("Failed to parse scale request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Service name is required",
		})
	}

	if req.Replicas < 0 {
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
		h.log.Error("Failed to scale service", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to scale service",
			"error":   err.Error(),
		})
	}

	h.log.Info("Service scaled successfully", "service", req.Name, "namespace", req.Namespace, "replicas", req.Replicas)
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
	var req RestartRequest
	if err := c.Bind().Body(&req); err != nil {
		h.log.Error("Failed to parse restart request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
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
		h.log.Error("Failed to restart service", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to restart service",
			"error":   err.Error(),
		})
	}

	h.log.Info("Service restarted successfully", "service", req.Name, "namespace", req.Namespace)
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
	var req RollbackRequest
	if err := c.Bind().Body(&req); err != nil {
		h.log.Error("Failed to parse rollback request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
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
		h.log.Error("Failed to rollback service", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to rollback service",
			"error":   err.Error(),
		})
	}

	h.log.Info("Service rolled back successfully", "service", req.Name, "namespace", req.Namespace)
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
	var req UpdateRequest
	if err := c.Bind().Body(&req); err != nil {
		h.log.Error("Failed to parse update request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Service name is required",
		})
	}

	if req.Image == "" && req.Version == "" {
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
		h.log.Error("Failed to update service", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to update service",
			"error":   err.Error(),
		})
	}

	h.log.Info("Service updated successfully", "service", req.Name, "namespace", req.Namespace)
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
	var req StatusRequest
	if err := c.Bind().Body(&req); err != nil {
		h.log.Error("Failed to parse status request", "error", err)
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Invalid request format",
			"error":   err.Error(),
		})
	}

	if req.Name == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"status":  "error",
			"message": "Service name is required",
		})
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	status, err := h.kubeClient.GetDeploymentStatus(ctx, req.Namespace, req.Name)
	if err != nil {
		h.log.Error("Failed to get service status", "error", err, "service", req.Name, "namespace", req.Namespace)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"status":  "error",
			"message": "Failed to get service status",
			"error":   err.Error(),
		})
	}

	h.log.Info("Service status retrieved successfully", "service", req.Name, "namespace", req.Namespace)
	return c.Status(fiber.StatusOK).JSON(fiber.Map{
		"status":  "success",
		"message": "Service status retrieved successfully",
		"data":    status,
	})
}
