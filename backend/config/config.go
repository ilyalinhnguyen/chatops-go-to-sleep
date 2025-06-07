package config

import (
	"log"
	"os"

	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/logger/handlers/slogpretty"
)

type Config struct {
	ValidAPIKeys  map[string]bool
	DebugLevel    string
	PrometheusURL string
}

func NewConfig() *Config {
	keys, err := GetValidKeys()

	if err != nil {
		log.Fatal(err)
	}

	debugLevel := os.Getenv("DEBUG_LEVEL")
	if debugLevel == "" {
		debugLevel = slogpretty.EnvProd
	}

	prometheusURL := os.Getenv("PROMETHEUS_URL")
	if prometheusURL == "" {
		prometheusURL = "http://prometheus:9090"
	}

	return &Config{
		ValidAPIKeys:  keys,
		DebugLevel:    debugLevel,
		PrometheusURL: prometheusURL,
	}
}
