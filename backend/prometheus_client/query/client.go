package query

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"time"
)

// PrometheusClient provides methods to query a Prometheus server
type PrometheusClient struct {
	baseURL    string
	httpClient *http.Client
}

// NewPrometheusClient creates a new client for querying Prometheus
func NewPrometheusClient(baseURL string) *PrometheusClient {
	return &PrometheusClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 5 * time.Second,
			Transport: &http.Transport{
				DialContext: (&net.Dialer{
					Timeout:   2 * time.Second,
					KeepAlive: 30 * time.Second,
				}).DialContext,
				MaxIdleConns:          10,
				IdleConnTimeout:       90 * time.Second,
				TLSHandshakeTimeout:   2 * time.Second,
				ExpectContinueTimeout: 1 * time.Second,
			},
		},
	}
}

// QueryResult represents the result from a Prometheus query
type QueryResult struct {
	Status string `json:"status"`
	Data   Data   `json:"data"`
}

// Data contains the result data from a Prometheus query
type Data struct {
	ResultType string   `json:"resultType"`
	Result     []Result `json:"result"`
}

// Result represents a single result from a Prometheus query
type Result struct {
	Metric map[string]string `json:"metric"`
	Value  []interface{}     `json:"value"`
}

// Query executes an instant query against the Prometheus server
func (c *PrometheusClient) Query(ctx context.Context, query string, ts time.Time) (*QueryResult, error) {
	u, err := url.Parse(fmt.Sprintf("%s/api/v1/query", c.baseURL))
	if err != nil {
		return nil, err
	}

	q := u.Query()
	q.Set("query", query)
	if !ts.IsZero() {
		q.Set("time", fmt.Sprintf("%d", ts.Unix()))
	}
	u.RawQuery = q.Encode()

	req, err := http.NewRequestWithContext(ctx, "GET", u.String(), nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var result QueryResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &result, nil
}

// QueryRange executes a range query against the Prometheus server
func (c *PrometheusClient) QueryRange(ctx context.Context, query string, start, end time.Time, step time.Duration) (*QueryResult, error) {
	u, err := url.Parse(fmt.Sprintf("%s/api/v1/query_range", c.baseURL))
	if err != nil {
		return nil, err
	}

	q := u.Query()
	q.Set("query", query)
	q.Set("start", fmt.Sprintf("%d", start.Unix()))
	q.Set("end", fmt.Sprintf("%d", end.Unix()))
	q.Set("step", fmt.Sprintf("%ds", int(step.Seconds())))
	u.RawQuery = q.Encode()

	req, err := http.NewRequestWithContext(ctx, "GET", u.String(), nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var result QueryResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &result, nil
}

// FormatValue formats a Prometheus value into a more usable form
func FormatValue(value []interface{}) (float64, time.Time, error) {
	if len(value) != 2 {
		return 0, time.Time{}, fmt.Errorf("unexpected value length: %d", len(value))
	}

	timestamp, ok := value[0].(float64)
	if !ok {
		return 0, time.Time{}, fmt.Errorf("unexpected timestamp format")
	}

	valueStr, ok := value[1].(string)
	if !ok {
		return 0, time.Time{}, fmt.Errorf("unexpected value format")
	}

	var v float64
	if _, err := fmt.Sscanf(valueStr, "%f", &v); err != nil {
		return 0, time.Time{}, err
	}

	return v, time.Unix(int64(timestamp), 0), nil
}

// Alert represents a Prometheus alert
type Alert struct {
	Labels      map[string]string `json:"labels"`
	Annotations map[string]string `json:"annotations"`
	State       string            `json:"state"`
	ActiveAt    time.Time         `json:"activeAt"`
	Value       string            `json:"value"`
}

// AlertsResponse represents the response from the Prometheus alerts API
type AlertsResponse struct {
	Status string `json:"status"`
	Data   struct {
		Alerts []Alert `json:"alerts"`
	} `json:"data"`
}

// RulesResponse represents the response from the Prometheus rules API
type RulesResponse struct {
	Status string `json:"status"`
	Data   struct {
		Groups []RuleGroup `json:"groups"`
	} `json:"data"`
}

// RuleGroup represents a group of Prometheus rules
type RuleGroup struct {
	Name  string `json:"name"`
	Rules []Rule `json:"rules"`
}

// Rule represents a Prometheus rule
type Rule struct {
	Name        string            `json:"name"`
	Query       string            `json:"query"`
	Labels      map[string]string `json:"labels"`
	Annotations map[string]string `json:"annotations"`
	State       string            `json:"state"`
	Type        string            `json:"type"`
}

// GetAlerts retrieves all alerts from Prometheus
func (c *PrometheusClient) GetAlerts(ctx context.Context) ([]Alert, error) {
	u, err := url.Parse(fmt.Sprintf("%s/api/v1/alerts", c.baseURL))
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, "GET", u.String(), nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var result AlertsResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return result.Data.Alerts, nil
}

// QueryRules retrieves all alert rules from Prometheus
func (c *PrometheusClient) QueryRules(ctx context.Context) (*RulesResponse, error) {
	u, err := url.Parse(fmt.Sprintf("%s/api/v1/rules", c.baseURL))
	if err != nil {
		return nil, err
	}

	q := u.Query()
	q.Set("type", "alert")
	u.RawQuery = q.Encode()

	req, err := http.NewRequestWithContext(ctx, "GET", u.String(), nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var result RulesResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &result, nil
}

// QueryAlerts executes a custom query for alerts
func (c *PrometheusClient) QueryAlerts(ctx context.Context, query string) (*QueryResult, error) {
	return c.Query(ctx, query, time.Now())
}

// GetActiveAlerts retrieves only the currently firing alerts
func (c *PrometheusClient) GetActiveAlerts(ctx context.Context) ([]Alert, error) {
	alerts, err := c.GetAlerts(ctx)
	if err != nil {
		return nil, err
	}

	var activeAlerts []Alert
	for _, alert := range alerts {
		if alert.State == "firing" {
			activeAlerts = append(activeAlerts, alert)
		}
	}

	return activeAlerts, nil
}
