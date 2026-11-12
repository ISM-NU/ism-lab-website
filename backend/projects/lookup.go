package projects

import (
	"encoding/json"
	"errors"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"

	"github.com/jackc/pgx/v5"
)

func ListProjectsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "list"
	handler_route := fmt.Sprintf("/api/projects/%s/", handler_action)
	handler_method := http.MethodGet
	handler_name := fmt.Sprintf("%sProjectsApiCallHandler", "List")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	query := r.URL.Query()
	projectIDs, hasProjectID := query["project_id"]
	targets, hasTarget := query["target"]
	validProjectID := hasProjectID && len(projectIDs) == 1 && projectIDs[0] != ""
	validTarget := hasTarget && len(targets) == 1 && targets[0] == "all"
	if len(query) != 1 || !validProjectID && !validTarget {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect query format", "Incorrect query format")
		return
	}

	const selectProjects = `SELECT ProjectID, ProjectName, COALESCE(ProjectDescription, '') FROM Projects`

	if validProjectID {
		var project models.ProjectData
		err := database.DbConn.QueryRow(
			r.Context(),
			selectProjects+" WHERE ProjectID = $1",
			projectIDs[0],
		).Scan(&project.ProjectID, &project.ProjectName, &project.ProjectDescription)
		if errors.Is(err, pgx.ErrNoRows) {
			backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such a project does not exists", "Project was not found")
			return
		}
		if err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
			return
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(project); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
		}
		return
	}

	rows, err := database.DbConn.Query(r.Context(), selectProjects+" ORDER BY ProjectID")
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
		return
	}
	defer rows.Close()

	projects := make([]models.ProjectData, 0)
	for rows.Next() {
		var project models.ProjectData
		if err := rows.Scan(&project.ProjectID, &project.ProjectName, &project.ProjectDescription); err != nil {
			backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
			return
		}
		projects = append(projects, project)
	}
	if err := rows.Err(); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(projects); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
	}

}
