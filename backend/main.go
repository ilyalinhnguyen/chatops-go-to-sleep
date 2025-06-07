package main

import (
	"log/slog"
	"os"

	"github.com/gofiber/fiber/v3"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/handlers"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/middleware"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/config"
)

func main() {
	cfg := config.NewConfig()
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))

	auth := middleware.NewAuthenticationMiddleware(cfg.ValidAPIKeys)
	app := handlers.NewHandler(logger, auth)
	app.InitRoutes(fiber.Config{})

	app.Run()
}
