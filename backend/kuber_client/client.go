package kuberclient

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"path/filepath"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/util/homedir"
	"k8s.io/client-go/util/retry"
)

// Client provides methods to interact with a Kubernetes cluster
type Client struct {
	clientset *kubernetes.Clientset
}

// ServiceConfig defines the configuration for Kubernetes service operations
type ServiceConfig struct {
	Namespace     string `json:"namespace"`
	Name          string `json:"name"`
	Replicas      int32  `json:"replicas,omitempty"`
	Image         string `json:"image,omitempty"`
	Version       string `json:"version,omitempty"`
	RevisionID    string `json:"revisionId,omitempty"`    // For specific revision rollback
	RevisionImage string `json:"revisionImage,omitempty"` // For specific image rollback
}

// NewClient creates a new Kubernetes client
func NewClient() (*Client, error) {
	var config *rest.Config
	var err error

	// Try in-cluster config first (for running inside a pod)
	// config, err = rest.InClusterConfig()
	// if err != nil {
	// 	// Fall back to kubeconfig file
	// 	kubeconfig := os.Getenv("KUBECONFIG")
	// 	if kubeconfig == "" {
	// 		if home := homedir.HomeDir(); home != "" {
	// 			kubeconfig = filepath.Join(home, ".kube", "config")
	// 		} else {
	// 			return nil, fmt.Errorf("could not locate kubeconfig file")
	// 		}
	// 	}

	// 	config, err = clientcmd.BuildConfigFromFlags("", kubeconfig)
	// 	if err != nil {
	// 		return nil, fmt.Errorf("failed to build config from kubeconfig: %v", err)
	// 	}
	// }

	// Oh. I get it. Look for my Dockerfile. I think i need to copy config file inside of container.

	// https://github.com/kubernetes/client-go/blob/master/examples/out-of-cluster-client-configuration/main.go

	var kubeconfig *string
	if home := homedir.HomeDir(); home != "" {
		kubeconfig = flag.String("kubeconfig", filepath.Join(home, ".kube", "config"), "(optional) absolute path to the kubeconfig file")
	} else {
		kubeconfig = flag.String("kubeconfig", "", "absolute path to the kubeconfig file")
	}
	flag.Parse()

	config, err = clientcmd.BuildConfigFromFlags("", *kubeconfig)
	if err != nil {
		panic(err.Error())
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create Kubernetes client: %v", err)
	}

	return &Client{
		clientset: clientset,
	}, nil
}

// ScaleDeployment scales a deployment to the specified number of replicas
func (c *Client) ScaleDeployment(ctx context.Context, config ServiceConfig) error {
	if config.Namespace == "" {
		config.Namespace = "default"
	}

	return retry.RetryOnConflict(retry.DefaultRetry, func() error {
		// Get the deployment
		deployment, err := c.clientset.AppsV1().Deployments(config.Namespace).Get(ctx, config.Name, metav1.GetOptions{})
		if err != nil {
			return fmt.Errorf("failed to get deployment %s in namespace %s: %v", config.Name, config.Namespace, err)
		}

		// Update replicas
		deployment.Spec.Replicas = &config.Replicas

		// Update the deployment
		_, err = c.clientset.AppsV1().Deployments(config.Namespace).Update(ctx, deployment, metav1.UpdateOptions{})
		return err
	})
}

// RestartDeployment restarts a deployment by adding a timestamp annotation
func (c *Client) RestartDeployment(ctx context.Context, config ServiceConfig) error {
	if config.Namespace == "" {
		config.Namespace = "default"
	}

	return retry.RetryOnConflict(retry.DefaultRetry, func() error {
		// Get the deployment
		deployment, err := c.clientset.AppsV1().Deployments(config.Namespace).Get(ctx, config.Name, metav1.GetOptions{})
		if err != nil {
			return fmt.Errorf("failed to get deployment %s in namespace %s: %v", config.Name, config.Namespace, err)
		}

		// Add/update restart annotation
		if deployment.Spec.Template.Annotations == nil {
			deployment.Spec.Template.Annotations = make(map[string]string)
		}
		// Add a timestamp annotation to force a restart
		deployment.Spec.Template.Annotations["kubectl.kubernetes.io/restartedAt"] = metav1.Now().Format(metav1.RFC3339Micro)

		// Update the deployment
		_, err = c.clientset.AppsV1().Deployments(config.Namespace).Update(ctx, deployment, metav1.UpdateOptions{})
		return err
	})
}

// RollbackDeployment rolls back a deployment to a specified revision or previous revision
func (c *Client) RollbackDeployment(ctx context.Context, config ServiceConfig) error {
	if config.Namespace == "" {
		config.Namespace = "default"
	}

	// Get the deployment's ReplicaSets (revision history)
	deploymentHistory, err := c.clientset.AppsV1().ReplicaSets(config.Namespace).List(ctx, metav1.ListOptions{
		LabelSelector: fmt.Sprintf("app=%s", config.Name),
	})
	if err != nil {
		return fmt.Errorf("failed to get deployment history: %v", err)
	}

	if len(deploymentHistory.Items) == 0 {
		return fmt.Errorf("no revisions found for deployment %s", config.Name)
	}

	// Find the target revision to roll back to
	var targetRevision *appsv1.ReplicaSet

	// Case 1: Specific revision ID requested
	if config.RevisionID != "" {
		for i := range deploymentHistory.Items {
			// Check if the ReplicaSet name or revision annotation matches the requested revision
			if deploymentHistory.Items[i].Name == config.RevisionID ||
				deploymentHistory.Items[i].Annotations["deployment.kubernetes.io/revision"] == config.RevisionID {
				targetRevision = &deploymentHistory.Items[i]
				break
			}
		}
		if targetRevision == nil {
			return fmt.Errorf("revision %s not found for deployment %s", config.RevisionID, config.Name)
		}
		// Case 2: Specific image requested
	} else if config.RevisionImage != "" || config.Version != "" {
		targetImage := config.RevisionImage
		if targetImage == "" && config.Version != "" {
			// If only version is specified, need to construct the full image name
			// This would require knowing the image name format
			// For simplicity, we'll search for any image ending with the specified version
			for i := range deploymentHistory.Items {
				for _, container := range deploymentHistory.Items[i].Spec.Template.Spec.Containers {
					if container.Image == config.Version || filepath.Ext(container.Image) == "."+config.Version {
						targetRevision = &deploymentHistory.Items[i]
						break
					}
				}
				if targetRevision != nil {
					break
				}
			}
		} else {
			// Search for the specific image
			for i := range deploymentHistory.Items {
				for _, container := range deploymentHistory.Items[i].Spec.Template.Spec.Containers {
					if container.Image == targetImage {
						targetRevision = &deploymentHistory.Items[i]
						break
					}
				}
				if targetRevision != nil {
					break
				}
			}
		}
		if targetRevision == nil {
			return fmt.Errorf("no revision found with image %s for deployment %s",
				config.RevisionImage != "")
		}
		// Case 3: Default to previous revision
	} else if len(deploymentHistory.Items) > 1 {
		// Sort revisions by creation timestamp (newest first)
		// For simplicity, we're just getting the previous revision
		for i := range deploymentHistory.Items {
			if i == 1 { // Second newest (current is index 0)
				targetRevision = &deploymentHistory.Items[i]
				break
			}
		}
	} else {
		return fmt.Errorf("only one revision found, cannot rollback deployment %s", config.Name)
	}

	if targetRevision == nil {
		return fmt.Errorf("could not find a valid revision to roll back to")
	}

	return retry.RetryOnConflict(retry.DefaultRetry, func() error {
		// Get the deployment
		deployment, err := c.clientset.AppsV1().Deployments(config.Namespace).Get(ctx, config.Name, metav1.GetOptions{})
		if err != nil {
			return fmt.Errorf("failed to get deployment %s in namespace %s: %v", config.Name, config.Namespace, err)
		}

		// Extract container specs from the target revision
		if len(targetRevision.Spec.Template.Spec.Containers) > 0 {
			deployment.Spec.Template.Spec.Containers = targetRevision.Spec.Template.Spec.Containers
		}

		// Add an annotation to indicate this was a rollback
		if deployment.Annotations == nil {
			deployment.Annotations = make(map[string]string)
		}
		deployment.Annotations["kubernetes.io/change-cause"] = fmt.Sprintf("Rollback to revision %s",
			targetRevision.Annotations["deployment.kubernetes.io/revision"])

		// Update the deployment
		_, err = c.clientset.AppsV1().Deployments(config.Namespace).Update(ctx, deployment, metav1.UpdateOptions{})
		return err
	})
}

// UpdateDeployment updates a deployment with a new image or version
func (c *Client) UpdateDeployment(ctx context.Context, config ServiceConfig) error {
	if config.Namespace == "" {
		config.Namespace = "default"
	}

	if config.Image == "" && config.Version == "" {
		return fmt.Errorf("either image or version must be specified")
	}

	return retry.RetryOnConflict(retry.DefaultRetry, func() error {
		// Get the deployment
		deployment, err := c.clientset.AppsV1().Deployments(config.Namespace).Get(ctx, config.Name, metav1.GetOptions{})
		if err != nil {
			return fmt.Errorf("failed to get deployment %s in namespace %s: %v", config.Name, config.Namespace, err)
		}

		// Update container image
		for i := range deployment.Spec.Template.Spec.Containers {
			if config.Image != "" {
				deployment.Spec.Template.Spec.Containers[i].Image = config.Image
			} else if config.Version != "" {
				// Extract the image name and repository, update the tag
				image := deployment.Spec.Template.Spec.Containers[i].Image
				// Simple image tag replacement - assumes format like "image:tag"
				// For more complex image references, you might need a more sophisticated parser
				deployment.Spec.Template.Spec.Containers[i].Image = fmt.Sprintf("%s:%s", image[:len(image)-len(filepath.Ext(image))], config.Version)
			}
		}

		// Update the deployment
		_, err = c.clientset.AppsV1().Deployments(config.Namespace).Update(ctx, deployment, metav1.UpdateOptions{})
		return err
	})
}

// GetDeploymentStatus gets the status of a deployment
func (c *Client) GetDeploymentStatus(ctx context.Context, namespace, name string) (map[string]interface{}, error) {
	if namespace == "" {
		namespace = "default"
	}

	// Get the deployment
	deployment, err := c.clientset.AppsV1().Deployments(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get deployment %s in namespace %s: %v", name, namespace, err)
	}

	// Extract status information
	status := map[string]interface{}{
		"name":               deployment.Name,
		"namespace":          deployment.Namespace,
		"replicas":           deployment.Status.Replicas,
		"available":          deployment.Status.AvailableReplicas,
		"ready":              deployment.Status.ReadyReplicas,
		"updated":            deployment.Status.UpdatedReplicas,
		"unavailable":        deployment.Status.UnavailableReplicas,
		"conditions":         deployment.Status.Conditions,
		"observedGeneration": deployment.Status.ObservedGeneration,
		"creationTimestamp":  deployment.CreationTimestamp,
	}

	// Convert to JSON and back to ensure it's serializable
	jsonData, err := json.Marshal(status)
	if err != nil {
		return nil, fmt.Errorf("error serializing status: %v", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(jsonData, &result); err != nil {
		return nil, fmt.Errorf("error deserializing status: %v", err)
	}

	return result, nil
}

// GetClusterMetrics retrieves overall cluster metrics
func (c *Client) GetClusterMetrics(ctx context.Context) (map[string]interface{}, error) {
	// Get nodes to calculate total cluster capacity
	nodes, err := c.clientset.CoreV1().Nodes().List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get nodes: %v", err)
	}

	// Calculate total cluster capacity and allocatable resources
	clusterMetrics := map[string]interface{}{
		"nodes_total":    len(nodes.Items),
		"nodes_ready":    0,
		"pods_total":     0,
		"pods_running":   0,
		"pods_pending":   0,
		"pods_failed":    0,
		"pods_succeeded": 0,
	}

	// Count ready nodes
	for _, node := range nodes.Items {
		for _, condition := range node.Status.Conditions {
			if condition.Type == "Ready" && condition.Status == "True" {
				clusterMetrics["nodes_ready"] = clusterMetrics["nodes_ready"].(int) + 1
				break
			}
		}
	}

	// Get pod information
	pods, err := c.clientset.CoreV1().Pods("").List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get pods: %v", err)
	}

	clusterMetrics["pods_total"] = len(pods.Items)

	// Count pods by phase
	for _, pod := range pods.Items {
		switch pod.Status.Phase {
		case "Running":
			clusterMetrics["pods_running"] = clusterMetrics["pods_running"].(int) + 1
		case "Pending":
			clusterMetrics["pods_pending"] = clusterMetrics["pods_pending"].(int) + 1
		case "Failed":
			clusterMetrics["pods_failed"] = clusterMetrics["pods_failed"].(int) + 1
		case "Succeeded":
			clusterMetrics["pods_succeeded"] = clusterMetrics["pods_succeeded"].(int) + 1
		}
	}

	return clusterMetrics, nil
}

// GetNodeMetrics retrieves metrics for all nodes or a specific node
func (c *Client) GetNodeMetrics(ctx context.Context, nodeName string) ([]map[string]interface{}, error) {
	// Set up list options
	listOptions := metav1.ListOptions{}
	if nodeName != "" {
		listOptions.FieldSelector = fmt.Sprintf("metadata.name=%s", nodeName)
	}

	// Get nodes
	nodes, err := c.clientset.CoreV1().Nodes().List(ctx, listOptions)
	if err != nil {
		return nil, fmt.Errorf("failed to get nodes: %v", err)
	}

	var nodeMetrics []map[string]interface{}

	for _, node := range nodes.Items {
		nodeInfo := map[string]interface{}{
			"name":        node.Name,
			"status":      getNodeStatus(node),
			"allocatable": node.Status.Allocatable,
			"capacity":    node.Status.Capacity,
			"labels":      node.Labels,
			"conditions":  node.Status.Conditions,
		}

		nodeMetrics = append(nodeMetrics, nodeInfo)
	}

	return nodeMetrics, nil
}

// Helper function to determine node status
func getNodeStatus(node corev1.Node) string {
	for _, condition := range node.Status.Conditions {
		if condition.Type == "Ready" {
			if condition.Status == "True" {
				return "Ready"
			} else {
				return "NotReady"
			}
		}
	}
	return "Unknown"
}

// GetPodMetrics retrieves metrics for all pods or pods in a specific namespace
func (c *Client) GetPodMetrics(ctx context.Context, namespace string) ([]map[string]interface{}, error) {
	// Get pods
	var pods *corev1.PodList
	var err error

	if namespace != "" {
		pods, err = c.clientset.CoreV1().Pods(namespace).List(ctx, metav1.ListOptions{})
	} else {
		pods, err = c.clientset.CoreV1().Pods("").List(ctx, metav1.ListOptions{})
	}

	if err != nil {
		return nil, fmt.Errorf("failed to get pods: %v", err)
	}

	var podMetrics []map[string]interface{}

	for _, pod := range pods.Items {
		podInfo := map[string]interface{}{
			"name":       pod.Name,
			"namespace":  pod.Namespace,
			"status":     string(pod.Status.Phase),
			"hostIP":     pod.Status.HostIP,
			"podIP":      pod.Status.PodIP,
			"startTime":  pod.Status.StartTime,
			"containers": len(pod.Spec.Containers),
		}

		podMetrics = append(podMetrics, podInfo)
	}

	return podMetrics, nil
}