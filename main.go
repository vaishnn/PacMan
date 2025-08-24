package main

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

var defaultPackages = map[string]bool{
	"pip":        true,
	"setuptools": true,
	"wheel":      true,
}

type Library struct {
	Name    string `json:"name"`
	Version string `json:"version"`
	Tag     string `json:"tag"`
	// Storage string `json:"storage"`
	// Author  string `json:"author"`
}

type VirtualEnv struct {
	Path      string    `json:"path"`
	Libraries []Library `json:"libraries"`
}

type PipPackage struct {
	Name    string `json:"name"`
	Version string `json:"version"`
}

func findVirtualEnv(root string) ([]string, error) {
	var virtualEnvs []string
	err := filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() && d.Name() == "pyvenv.cfg" {
			venvPath := filepath.Dir(path)
			fmt.Printf("Found virtual Env at %s\n", path)
			virtualEnvs = append(virtualEnvs, venvPath)
			return filepath.SkipDir
		}
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("error walking directory: %w", err)
	}
	return virtualEnvs, nil
}

func getInstalledLibraries(venvPath string) ([]Library, error) {
	// Here we need to consider different systems windows & macOS or linux
	// I'm currently on macOS
	binpath := "bin" // macOS or linux
	if runtime.GOOS == "windows" {
		binpath = "Scripts"
	}
	pipExec := filepath.Join(venvPath, binpath, "pip")
	fmt.Printf("%s\n", pipExec)
	pythonExec := filepath.Join(venvPath, binpath, "python")

	siteCmd := exec.Command(pythonExec, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])")
	siteOutput, err := siteCmd.Output()
	if err != nil {
		return nil, fmt.Errorf("error getting site packages path: %w", err)
	}
	fmt.Printf("%s\n", siteOutput)
	// sitePackagesPath := strings.TrimSpace(string(siteOutput))

	listCmd := exec.Command(pipExec, "list", "--format=json")
	listOutput, err := listCmd.Output()
	if err != nil {
		return nil, fmt.Errorf("Error Getting Installed Libraries: %w", err)
	}
	var pipPackages []PipPackage
	if err := json.Unmarshal(listOutput, &pipPackages); err != nil {
		fmt.Printf("Error Unmarshalling JSON: %v\n", err)
	}

	var libraries []Library
	for _, pkg := range pipPackages {
		tag := "default"
		if _, isDefault := defaultPackages[strings.ToLower(pkg.Name)]; isDefault {
			tag = "default"
		}
		libraries = append(libraries, Library{
			Name:    pkg.Name,
			Version: pkg.Version,
			Tag:     tag,
		})
	}
	return libraries, nil

}

func main() {
	root := "."
	virtualEnvs, _ := findVirtualEnv(root)
	fmt.Printf(virtualEnvs[0])
	library, err := getInstalledLibraries(virtualEnvs[0])
	if err == nil {
		fmt.Printf("%v\n", library)
	}
}
