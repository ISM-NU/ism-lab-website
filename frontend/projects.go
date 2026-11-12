package frontend

import (
	"html/template"
	"main/backend"
	"net/http"
)

func ProjectsPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ProjectsPageHandler"
	handler_route := "/projects/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/projects.html")
	if parseErr != nil {
		msg := "Something went wrong during page retreival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, parseErr.Error())
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	execErr := tmpl.Execute(w, nil)
	if execErr != nil {
		msg := "Something went wrong during page retreival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, execErr.Error())
		return
	}
}

func ControlProjectsPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ControlProjectsPageHandler"
	handler_route := "/control/panel/projects/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/control_projects.html")
	if parseErr != nil {
		msg := "Something went wrong during page retreival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, parseErr.Error())
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	execErr := tmpl.Execute(w, nil)
	if execErr != nil {
		msg := "Something went wrong during page retreival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, execErr.Error())
		return
	}
}
