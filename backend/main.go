package main

import (
	"github.com/gofiber/fiber/v3"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/handlers"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/middleware"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/config"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/logger/handlers/slogpretty"
)

func main() {
	cfg := config.NewConfig()

	logger := slogpretty.SetupLogger("dev")

	auth := middleware.NewAuthenticationMiddleware(cfg.ValidAPIKeys)
	app := handlers.NewHandler(logger, auth)
	app.InitRoutes(fiber.Config{})

	app.Run()
}
