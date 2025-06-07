package config

import (
	"log"
	"os"
)

type Config struct {
	ValidAPIKeys map[string]bool
	DebugLevel   string
}

func NewConfig() *Config {
	keys, err := GetValidKeys()

	if err != nil {
		log.Fatal(err)
	}

	debugLevel := os.Getenv("DEBUG_LEVEL")
	if debugLevel == "" {
		debugLevel = "info"
	}

	return &Config{
		ValidAPIKeys: keys,
	}
}
