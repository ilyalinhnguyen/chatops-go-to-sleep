package config

import (
	"encoding/json"

	"os"
	"path/filepath"
)

// GetValidKeys reads the keys.json file and returns a map of valid API keys
func GetValidKeys() (map[string]bool, error) {
	// Get the current directory
	dir, err := os.Getwd()
	if err != nil {
		return nil, err
	}

	// Construct path to the keys.json file
	keysPath := filepath.Join(dir, "config", "keys.json")

	// Read the file
	data, err := os.ReadFile(keysPath)
	data, err = os.ReadFile(keysPath)
	if err != nil {
		return nil, err
	}

	// Parse the JSON data
	var keys map[string]bool
	err = json.Unmarshal(data, &keys)
	if err != nil {
		return nil, err
	}

	return keys, nil
}
