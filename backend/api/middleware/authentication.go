package middleware

import (
	"strings"

	"github.com/gofiber/fiber/v3"
)

type AuthenticationMiddleware struct {
	validAPIKeys map[string]bool
}

func NewAuthenticationMiddleware(validAPIKeys map[string]bool) *AuthenticationMiddleware {
	return &AuthenticationMiddleware{
		validAPIKeys: validAPIKeys,
	}
}

// TokenAuth is a simple middleware that checks if the request has a valid API key
func (am *AuthenticationMiddleware) Authenticate(c fiber.Ctx) error {

	// Get the Authorization header
	authHeader := c.Get("Authorization")

	// Check if the header is empty
	if authHeader == "" {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Authorization header is required",
		})
	}

	// Get the token from the header
	// Expected format: "Bearer {token}" or just "{token}"
	token := authHeader
	if strings.HasPrefix(authHeader, "Bearer ") {
		token = strings.TrimPrefix(authHeader, "Bearer ")
	}

	// Check if the token is valid
	if !am.isValidToken(token) {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Invalid API key",
		})
	}

	// Token is valid, proceed to the next handler
	return c.Next()

}

// isValidToken checks if the given token is valid
func (am *AuthenticationMiddleware) isValidToken(token string) bool {
	// Simply check if the token is in the map of valid API keys
	_, exists := am.validAPIKeys[token]
	return exists
}
