package main

import "sync"

type ProjectFile struct {
	Path    string   `json:"path"`
	Imports []string `json:"imports"`
}

type DependencyGraph struct {
	Nodes map[string]*Node
	mu    sync.Mutex
}

type Node struct {
	Name         string   `json:"name"`
	Version      string   `json:"version"`
	IsLocal      string   `json:"is_local"`
	Dependencies []string `json:"dependencies"`
}

func (g *DependencyGraph) AddNode(node *Node) {
	g.mu.Lock()
	defer g.mu.Unlock()

	if _, exists := g.Nodes[node.Name]; !exists {
		g.Nodes[node.Name] = node
	}
}
