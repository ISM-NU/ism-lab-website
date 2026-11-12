package projects

import (
	"fmt"
	"main/backend"
	"main/database"
	"net/http"
)

func EraseProjectsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "erase"
	handler_route := fmt.Sprintf("/api/projects/%s/", handler_action)
	handler_method := http.MethodDelete
	handler_name := fmt.Sprintf("%sProjectsApiCallHandler", "Erase")
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	isAdmin := backend.CheckAdministratorRole(handler_name, w, r)
	if !isAdmin {
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

	_, err = database.DbConn.Exec(r.Context(), `DELETE FROM Projects WHERE ProjectID = $1`, projectIDs[0])
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrong durint transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)

}
