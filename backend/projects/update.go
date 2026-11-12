package projects

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
)

func UpdateProjectsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "update"
	handler_route := fmt.Sprintf("/api/projects/%s/", handler_action)
	handler_method := http.MethodPut
	handler_name := fmt.Sprintf("%sProjectsApiCallHandler", "Update")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	query := r.URL.Query()
	projectIDs, hasProjectID := query["project_id"]
	validProjectID := hasProjectID && len(projectIDs) == 1 && projectIDs[0] != ""
	if len(query) != 1 || !validProjectID {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrec query format", "Incorrect query format")
		return
	}

	var projectExists bool
	err := database.DbConn.QueryRow(
		r.Context(),
		`SELECT EXISTS (SELECT 1 FROM Projects WHERE ProjectID = $1)`,
		projectIDs[0],
	).Scan(&projectExists)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
		return
	}
	if !projectExists {
		backend.HandleCommonError(handler_name, w, r, http.StatusNotFound, "Such a project with given ID does not exists", "Project was not found")
		return
	}

	var project models.ProjectData
	if err := json.NewDecoder(r.Body).Decode(&project); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect json body format", err.Error())
		return
	}

	_, err = database.DbConn.Exec(
		r.Context(),
		`UPDATE Projects SET ProjectName = $1, ProjectDescription = $2 WHERE ProjectID = $3`,
		project.ProjectName,
		project.ProjectDescription,
		projectIDs[0],
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
