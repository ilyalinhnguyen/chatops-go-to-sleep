package main

import (
	"fmt"
	"net/http"
)

const version = "1"

func serviceHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/service" {
		http.NotFound(w, r)
		return
	}
	fmt.Fprintf(w, "Hello, I'm service with version: %s", version)
}

func main() {
	http.HandleFunc("/service", serviceHandler)

	fmt.Println("Server is running on 8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		fmt.Println("Failed to start the server:", err)
	}
}
