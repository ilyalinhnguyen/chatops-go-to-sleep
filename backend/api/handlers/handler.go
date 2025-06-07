package handlers

import (
	"log/slog"

	"github.com/gofiber/fiber/v3"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/middleware"
)

type Handler struct {
	log            *slog.Logger
	authMiddleware *middleware.AuthenticationMiddleware
	router         *fiber.App
}

func (h *Handler) Run() error {
	return h.router.Listen(":8000")
}

func NewHandler(log *slog.Logger, auth *middleware.AuthenticationMiddleware) *Handler {
	return &Handler{
		log:            log,
		authMiddleware: auth,
	}
}

func (h *Handler) InitRoutes(cfg fiber.Config) {
	router := fiber.New(cfg)
	h.router = router

	api := router.Group("/api")

	// Unsecure ping
	api.Get("/ping", h.ping)

	v1 := api.Group("/v1")
	v1.Use(h.authMiddleware.Authenticate)

	v1.Get("/metrics", h.metricsHandler)
	v1.Post("/scale", h.scaleHandler)
	v1.Post("/restart", h.restartHandler)
	v1.Post("/rollback", h.rollbackHandler)

	// Secure ping
	v1.Get("/ping", h.ping)

}

func (h *Handler) metricsHandler(c fiber.Ctx) error {
	//implement...
	return nil
}

func (h *Handler) scaleHandler(c fiber.Ctx) error {
	//implement...
	return nil
}

func (h *Handler) restartHandler(c fiber.Ctx) error {
	//implement...
	return nil
}

func (h *Handler) rollbackHandler(c fiber.Ctx) error {
	//implement...
	return nil
}

func (h *Handler) ping(c fiber.Ctx) error {
	return c.Status(fiber.StatusOK).SendString("Pong")
}
