package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
)

func isMatchAndExecutable(expression *regexp.Regexp, filePath string) bool {
	file_stat, err := os.Stat(filePath)
	if err != nil {
		return false
	}
	if file_stat.IsDir() {
		return false
	}
	if file_stat.Mode().Perm()&0111 != 0 {
		if expression.Match([]byte(filepath.Base(filePath))) {
			return true
		}
	}
	return false
}

func wherePythonLocation(searching_paths []string, searching_expression string) map[string]string {
	found_interpreters := map[string]string{}
	python_executable_pattern, err := regexp.Compile(searching_expression)

	if err != nil {
		log.Fatal(err)
	}

	for _, folder := range searching_paths {
		entries, err := os.ReadDir(folder)
		if err != nil {
			continue
		}
	outer_loop:
		for _, entry := range entries {
			full_path := filepath.Join(folder, entry.Name())

			// case for the framework path
			if strings.Contains(folder, "Framework") && entry.IsDir() && runtime.GOOS == "darwin" {
				bin_path := filepath.Join(full_path, "bin")
				if _, err := os.Stat(bin_path); err == nil {
					bin_entries, err := os.ReadDir(bin_path)
					if err != nil {
						continue
					}
					for _, bin_entry := range bin_entries {
						bin_full_path := filepath.Join(bin_path, bin_entry.Name())
						if isMatchAndExecutable(python_executable_pattern, bin_full_path) {
							if _, ok := found_interpreters[bin_full_path]; !ok {
								cmd := exec.Command(bin_full_path, "--version")
								version, err := cmd.CombinedOutput()
								if err != nil {
									continue
								}
								found_interpreters[bin_full_path] = strings.TrimSpace(string(version))
								goto outer_loop
							}
						}
					}
				}
			} else {
				if isMatchAndExecutable(python_executable_pattern, full_path) {
					if _, ok := found_interpreters[full_path]; !ok {
						cmd := exec.Command(full_path, "--version")
						version, err := cmd.CombinedOutput()
						if err != nil {
							continue
						}
						found_interpreters[full_path] = strings.TrimSpace(string(version))
						goto outer_loop
					}
				}
			}
		}
	}
	return found_interpreters
}

func interpreters() {
	// Turns out this much slower than python
	// searching_paths for mac
	searching_paths := []string{
		"/Library/Frameworks/Python.framework/Versions",
		"/opt/homebrew/bin",
		"/usr/local/bin",
		"/usr/bin",
	}
	python_expression := `^python(2|3)(\.\d+)?$`
	wherePython := wherePythonLocation(searching_paths, python_expression)

	fmt.Print(wherePython)
}
