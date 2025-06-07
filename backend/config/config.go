package config

import (
	"log"
	"os"
	"path/filepath"

	"github.com/ilyalinhnguyen/chatops-go-to-sleep/backend/logger/handlers/slogpretty"
	"github.com/joho/godotenv"
)

type Config struct {
	ValidAPIKeys  map[string]bool
	DebugLevel    string
	PrometheusURL string
}

func NewConfig() *Config {
	// Load .env file
	LoadEnv()
	
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
		prometheusURL = "http://localhost:9090"
	}

	return &Config{
		ValidAPIKeys:  keys,
		DebugLevel:    debugLevel,
		PrometheusURL: prometheusURL,
	}
}

// LoadEnv loads environment variables from .env file
func LoadEnv() {
	// Try to load from current directory
	err := godotenv.Load()
	if err == nil {
		return
	}
	
	// If not found, try to load from backend directory
	dir, err := os.Getwd()
	if err != nil {
		log.Printf("Warning: Could not determine working directory: %v", err)
		return
	}
	
	// Try different relative paths
	paths := []string{
		filepath.Join(dir, ".env"),
		filepath.Join(dir, "backend", ".env"),
		filepath.Join(dir, "..", ".env"),
	}
	
	for _, path := range paths {
		if err := godotenv.Load(path); err == nil {
			log.Printf("Loaded environment from %s", path)
			return
		}
	}
	
	log.Printf("Warning: .env file not found, using default environment variables")
}
