package main

import (
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
	Storage string `json:"storage"`
	Author  string `json:"author"`
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

func getInstalledLibraries(venvPath string) {
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
		// return nil, fmt.Errorf("error getting site packages path: %w", err)
		fmt.Printf("Error getting site packages path: %v\n", err)
	}
	sitePackagesPath := strings.TrimSpace(string(siteOutput))

	listCmd := exec.Command(pipExec, "list", "--format=json")
	listOutput, err := listCmd.Output()
	if err != nil {
		// return fmt.Errorf("Error Getting Installed Libraries: %w", err)
		fmt.Printf("Error Getting Installed Libraries: %v\n", err)
	}

}

func main() {
	root := "."
	virtualEnvs, _ := findVirtualEnv(root)
	fmt.Printf(virtualEnvs[0])
	getInstalledLibraries(virtualEnvs[0])

}
