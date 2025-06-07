package kube

type KubeClient interface {
	GetServiceMetrics(namespace string) error
	RestartDeployment(namespace, name string) error
	ScaleDeployment(namespace, name string) error
	RollbackDeployment(namespace, name string) error
}
