package main

import (
	"bytes"
	"encoding/csv"
	"encoding/json"
	"io"
	"io/fs"
	"log"
	"log/slog"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
)

type Metadata struct {
	Name                 string   `json:"name"`
	Version              string   `json:"version"`
	Summary              string   `json:"summary"`
	Size                 int64    `json:"size"`
	Author               string   `json:"author"`
	License              string   `json:"license"`
	LicenseExpression    string   `json:"license_expression"`
	LicenseFile          []string `json:"license_file"`
	Classifiers          []string `json:"classifier"`
	RequiresDistribution []string `json:"requires_dist"`
	RequiresPython       string   `json:"requires_python"`
	ProjectUrl           []string `json:"project_url"`
	ProvidesExtra        []string `json:"provides_extra"`
}

type Installed struct {
	Metadata         Metadata `json:"metadata"`
	MetadataLocation string   `json:"metadata_location"`
	Installer        string   `json:"installer"`
	Requested        bool     `json:"requested"`
}

type libraries struct {
	PipVersion string      `json:"pip_version"`
	Installed  []Installed `json:"installed"`
}

type Job struct {
	LibraryIdx  int
	PathsToScan []string
}

type result struct {
	LibraryIdx int
	size       int64
}

func (libraries *libraries) remove(name string) {
	for index, installed := range libraries.Installed {
		if name == installed.Metadata.Name {
			libraries.Installed = append(libraries.Installed[:index], libraries.Installed[index+1:]...)
			break
		}
	}
}

// Get the path to the site-packages directory within a virtual environment.
func get_site_package_main(python_exec *string) (string, error) {

	code := "import sysconfig; print(sysconfig.get_paths()['purelib'])"
	cmd := exec.Command(*python_exec, "-c", code)
	stdout, err := cmd.Output()
	if err != nil {
		slog.Error("Error getting site-packages path", "error", err)
		return "", err
	}
	return strings.TrimSpace(string(stdout)), nil
}

// Gets the size of the directory
func get_path_size(paths []string) int64 {

	var total_size int64 = 0
	for _, path := range paths {
		err := filepath.WalkDir(path, func(sub_path string, d fs.DirEntry, err error) error {
			if err != nil {
				return nil
			}
			if !d.IsDir() {
				info, err := d.Info()
				if err != nil {
					return nil
				}
				total_size += info.Size()
			}
			return nil
		})

		if err != nil {
			log.Printf("Error calculating size for %s: %v\n", path, err)
		}
	}
	return total_size
}

func worker(id int, wg *sync.WaitGroup, jobs <-chan Job, results chan<- result) {
	defer wg.Done()

	for job := range jobs {
		size := get_path_size(job.PathsToScan)
		results <- result{
			LibraryIdx: job.LibraryIdx,
			size:       size,
		}
	}
}

func get_installed_libraries_with_size(venv_path string) (libraries, error) {
	venv_path_abs, err := filepath.Abs(venv_path)
	if err != nil {
		slog.Error("Error while absoluting paths", "error", err)
		return libraries{}, err
	}
	bin_dir := filepath.Join(venv_path_abs, "bin")
	operating_system := runtime.GOOS
	if operating_system == "windows" {
		bin_dir = filepath.Join(venv_path_abs, "Scripts")
	}
	python_exec := filepath.Join(bin_dir, "python")
	pip_exec := filepath.Join(bin_dir, "pip")
	site_packages_path, site_err := get_site_package_main(&python_exec)
	if site_err != nil {
		slog.Error("Error while getting site packages path", "error", site_err)
		return libraries{}, err
	}

	cmd := exec.Command(pip_exec, "inspect")

	stdout, inspect_err := cmd.StdoutPipe()
	if inspect_err != nil {
		slog.Error("Error while creating stdout pipe", "error", inspect_err)
		return libraries{}, err
	}

	if err := cmd.Start(); err != nil {
		slog.Error("Error starting command", "error", err)
		return libraries{}, err
	}

	output, err := io.ReadAll(stdout)
	if err != nil {
		slog.Error("Error reading output stream", "error", err)
		return libraries{}, err
	}
	if err := cmd.Wait(); err != nil {
		slog.Error("Error waiting for command", "error", err)
		return libraries{}, err
	}
	var library_data libraries
	if err := json.Unmarshal(output, &library_data); err != nil {
		slog.Error("Error unmarshalling JSON", "error", err)
		return libraries{}, err
	}

	num_libraries := len(library_data.Installed)
	jobs := make(chan Job, num_libraries)
	results := make(chan result, num_libraries)

	number_of_worker := min(runtime.NumCPU(), 8)

	var wg sync.WaitGroup

	for w := range number_of_worker {
		wg.Add(1)
		go worker(w, &wg, jobs, results)
	}

	for index, installed_libraries := range library_data.Installed {
		metadata_location := installed_libraries.MetadataLocation
		record_path := filepath.Join(metadata_location, "RECORD")
		paths_to_Size := make(map[string]struct{})
		file, err := os.Open(record_path)
		if err == nil {
			defer file.Close()

			record_file := csv.NewReader(file)
			for {
				record, err := record_file.Read()
				if err == io.EOF {
					break
				} else if err != nil {
					continue
				}
				relative_row := record[0]
				abs_file_path, err := filepath.Abs(filepath.Join(site_packages_path, relative_row))
				if strings.HasPrefix(abs_file_path, site_packages_path) {
					parts := strings.Split(relative_row, string(filepath.Separator))
					if len(parts) > 0 && !strings.Contains("__pycache__", relative_row) {
						top_level := parts[0]
						paths_to_Size[filepath.Join(site_packages_path, top_level)] = struct{}{}
					}
				}
			}

		} else {
			paths_to_Size[metadata_location] = struct{}{}
		}

		paths := make([]string, 0, len(paths_to_Size))
		for p := range paths_to_Size {
			paths = append(paths, p)
		}
		jobs <- Job{LibraryIdx: index, PathsToScan: paths}
	}

	close(jobs)

	go func() {
		wg.Wait()
		close(results)
	}()

	for res := range results {
		library_data.Installed[res.LibraryIdx].Metadata.Size = res.size
	}

	return library_data, nil
}

func main() {
	handler := slog.NewJSONHandler(os.Stderr, nil)
	logger := slog.New(handler).With("service", "go-detail-api")
	slog.SetDefault(logger)

	// scanner := bufio.NewScanner(os.Stdin)
	var buffer bytes.Buffer
	multi_encoder := io.MultiWriter(os.Stdout, &buffer)
	encoder := json.NewEncoder(multi_encoder)
	encoder.SetEscapeHTML(false)

	virtual_env_dir := os.Args[1:][0]

	virtual_env_path := strings.TrimSpace(virtual_env_dir)
	site_packages_path, err := get_installed_libraries_with_size(virtual_env_path)
	site_packages_path.remove("")
	if err != nil {
		slog.Error("Error getting installed libraries", "error", err)
		return
	}
	if err := encoder.Encode(site_packages_path); err != nil {
		slog.Error("Failed to write JSON output", "error", err)
	}

	// for scanner.Scan() {
	// 	virtual_env_path := strings.TrimSpace(scanner.Text())
	// 	site_packages_path, err := get_installed_libraries_with_size(virtual_env_path)
	// 	if err != nil {
	// 		slog.Error("Error getting installed libraries", "error", err)
	// 		return
	// 	}
	// 	if err := encoder.Encode(site_packages_path); err != nil {
	// 		slog.Error("Failed to write JSON output", "error", err)
	// 	}
	// 	if err := scanner.Err(); err != nil {
	// 		slog.Error("Error reading from stdin", "error", err)
	// 	}
	// 	slog.Info("Stdin closed. Exiting.")
	// }
}
