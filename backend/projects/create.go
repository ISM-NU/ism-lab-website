package projects

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
)

func CreateProjectsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "create"
	handler_route := fmt.Sprintf("/api/projects/%s/", handler_action)
	handler_method := http.MethodPost
	handler_name := fmt.Sprintf("%sProjectsApiCallHandler", "Create")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	var project models.ProjectData
	if err := json.NewDecoder(r.Body).Decode(&project); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect json format", err.Error())
		return
	}

	_, err := database.DbConn.Exec(
		r.Context(),
		`INSERT INTO Projects (ProjectName, ProjectDescription) VALUES ($1, $2)`,
		project.ProjectName,
		project.ProjectDescription,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
