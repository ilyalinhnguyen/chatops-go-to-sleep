package config

import (
	"log"
)

type Config struct {
	ValidAPIKeys map[string]bool
}

func NewConfig() *Config {
	keys, err := GetValidKeys()

	if err != nil {
		log.Fatal(err)
	}

	return &Config{
		ValidAPIKeys: keys,
	}
}
