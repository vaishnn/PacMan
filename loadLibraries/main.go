package main

// This GO program was just because I wanted to learn GO
// I just found out it is much better to use pip inspect
// or just pip list directly

// No Longer Being Used

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
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

var debugFlag bool = false

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
			if debugFlag {
				fmt.Printf("Found virtual Env at %s\n", path)
			}
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

func getInstalledLibraries(venvPath string) ([]Library, string, error) {
	// I also need to implement the storage thingy
	// Here we need to consider different systems windows & macOS or linux
	// I'm currently on macOS
	binpath := "bin" // macOS or linux
	if runtime.GOOS == "windows" {
		binpath = "Scripts"
	}
	pipExec := filepath.Join(venvPath, binpath, "pip")
	pythonExec := filepath.Join(venvPath, binpath, "python")

	// siteCmd := exec.Command(pythonExec, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])")
	// siteOutput, err := siteCmd.Output()
	// if err != nil {
	// 	return nil, fmt.Errorf("error getting site packages path: %w", err)
	// }
	// sitePackagesPath := strings.TrimSpace(string(siteOutput))

	listCmd := exec.Command(pipExec, "list", "--format=json")
	listOutput, err := listCmd.Output()
	if err != nil {
		return nil, "", fmt.Errorf("Error Getting Installed Libraries: %w", err)
	}
	var pipPackages []PipPackage
	if err := json.Unmarshal(listOutput, &pipPackages); err != nil {
		fmt.Printf("Error Unmarshalling JSON: %v\n", err)
	}

	var libraries []Library
	for _, pkg := range pipPackages {
		tag := "installed"
		if _, isDefault := defaultPackages[strings.ToLower(pkg.Name)]; isDefault {
			tag = "default"
		}

		libraries = append(libraries, Library{
			Name:    pkg.Name,
			Version: pkg.Version,
			Tag:     tag,
		})
	}
	return libraries, pythonExec, nil

}

func main() {
	args := os.Args
	root := "."
	if len(args) > 1 {
		root = args[1]
		if len(args) > 2 {
			if args[2] == "--debug" {
				debugFlag = true
			}
		}
	}

	virtualEnvs, _ := findVirtualEnv(root)
	library, pythonExec, err := getInstalledLibraries(virtualEnvs[0])

	finalJSON, err := json.MarshalIndent(library, "", " ")
	if err != nil {
		fmt.Printf("Error Marshalling JSON: %v\n", err)
	}
	if debugFlag {
		fmt.Printf("---SCAN COMPLETE\n---")
	}
	var prettyJSON bytes.Buffer
	if err := json.Indent(&prettyJSON, finalJSON, "", " "); err != nil {
		fmt.Printf("Error Indenting JSON: %v\n", err)
	}
	outputToStdout := pythonExec + "--|--" + string(finalJSON) + "\n"
	fmt.Println(outputToStdout)
}
