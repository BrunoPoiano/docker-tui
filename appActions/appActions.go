package appActions

import (
	"bytes"
	"docker-tui-go/models"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"strings"
	"syscall"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

func CommandItems(container models.Items, command string) tea.Cmd {

	return func() tea.Msg {

		cmd := exec.Command("docker", command, container.Id)

		var out bytes.Buffer
		cmd.Stdout = &out

		err := cmd.Run()
		if err != nil {
			fmt.Printf("Error docker %s \n", command)
			return models.Action{Error: "Error running Command"}
		}

		return models.Action{Finished: true}
	}

}

func DefaultStyles() *models.Styles {
	s := new(models.Styles)
	s.BorderColor = lipgloss.Color("36")

	return s
}

func GetMenuItems() []models.Items {

	menu := []models.Items{
		{Id: "shell", Name: "Shell"},
		{Id: "logs", Name: "Logs"},
		{Id: "stop", Name: "Stop"},
		{Id: "restart", Name: "Restart"},
		{Id: "list", Name: "List"},
	}

	return menu
}

func GetRunningItems() []models.Items {

	cmd := exec.Command("docker", "ps", "--format", "{{.ID}} {{.Names}}")

	var containers []models.Items
	var out bytes.Buffer
	cmd.Stdout = &out

	err := cmd.Run()
	if err != nil {
		fmt.Println("Error:", err)
		return containers
	}

	cmdReturn := strings.Split(out.String(), "\n")
	for _, item := range cmdReturn {
		itemFormated := strings.Split(item, " ")

		if len(itemFormated) == 2 {
			containers = append(containers, models.Items{
				Id:   itemFormated[0],
				Name: itemFormated[1],
			})
		}
	}

	return containers

}

func ShellItems(container models.Items) {
	cmd := exec.Command("docker", "exec", "-it", container.Id, "/bin/sh")

	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-signals
		if err := cmd.Process.Signal(syscall.SIGINT); err != nil {
			fmt.Println("Error sending signal to Docker process:", err)
		}
	}()

	fmt.Println("Running Command")

	if err := cmd.Start(); err != nil {
		fmt.Printf("Error starting Docker: %s\n", err)
		return
	}

	if err := cmd.Wait(); err != nil {
		fmt.Printf("Error waiting for Docker: %s\n", err)
	}

}