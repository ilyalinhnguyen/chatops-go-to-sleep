package kube

import (
	"flag"
	"os"
	"path/filepath"
	"sync"

	"k8s.io/client-go/kubernetes"
	rest "k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

type client struct {
	clientset *kubernetes.Clientset
}

var (
	once      sync.Once
	singleton *client
)

func NewClient() (KubeClient, error) {
	var err error
	once.Do(func() {
		var config *rest.Config
		config, err = loadKubeConfig()
		if err != nil {
			return
		}

		clientset, e := kubernetes.NewForConfig(config)
		if e != nil {
			err = e
			return
		}
		singleton = &client{clientset: clientset}
	})

	return singleton, err
}

func loadKubeConfig() (*rest.Config, error) {
	if config, err := rest.InClusterConfig(); err != nil {
		return config, nil
	}

	var kubeconfig *string
	if home := homeDir(); home != "" {
		kubeconfig = flag.String("kubeconfig", filepath.Join(home, ".kube", "config"), "")
	} else {
		kubeconfig = flag.String("kubeconfig", "", "kubeconfig file")
	}
	flag.Parse()

	return clientcmd.BuildConfigFromFlags("", *kubeconfig)
}

func homeDir() string {
	if h := os.Getenv("HOME"); h != "" {
		return h
	}

	return os.Getenv("USERPROFILE")
}
