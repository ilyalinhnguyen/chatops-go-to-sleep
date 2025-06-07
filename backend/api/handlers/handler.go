package handlers

import (
	"log/slog"

	"github.com/gofiber/fiber/v3"
)

type Handler struct {
	log *slog.Logger
}

func NewHandler(log *slog.Logger) *Handler {
	return &Handler{log: log}
}

func (h *Handler) InitRoutes(cfg fiber.Config) {
	router := fiber.New(cfg)

	api := router.Group("/api")

	//TODO:add middleware 

	v1 := api.Group("/v1")

	v1.Get("/metrics", h.metricsHandler)
	v1.Post("/scale", h.scaleHandler)
	v1.Post("/restart", h.restartHandler)
	v1.Post("/rollback", h.rollbackHandler)

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
