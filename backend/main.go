package main

import (
	"fmt"

	"github.com/gofiber/fiber/v3"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/handlers"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/api/middleware"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/config"
	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/logger/handlers/slogpretty"
)

func main() {
	cfg := config.NewConfig()

	fmt.Println("***")
	fmt.Println("PROM URL:")
	fmt.Println(cfg.PrometheusURL)
	fmt.Println("***")

	logger := slogpretty.SetupLogger(cfg.DebugLevel)

	auth := middleware.NewAuthenticationMiddleware(cfg.ValidAPIKeys)
	app := handlers.NewHandler(logger, auth)
	app.InitRoutes(fiber.Config{})

	err := app.Run()
	if err != nil {
		logger.Error("Failed to start server", err)
	}
}
