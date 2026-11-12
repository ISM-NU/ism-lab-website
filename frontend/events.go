package frontend

import (
	"html/template"
	"main/backend"
	"net/http"
)

func ShowEventsPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ShowEventsPageHandler"
	handler_route := "/events/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/events.html")
	if parseErr != nil {
		msg := "Something went wrong during the page retreival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, parseErr.Error())
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	execErr := tmpl.Execute(w, nil)
	if execErr != nil {
		msg := "Something went wrong during the page retreival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, execErr.Error())
	}
}

func ControlEventsPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ControlEventsPageHandler"
	handler_route := "/control/panel/events/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, is_signed := backend.AuthorizeRequest(handler_name, w, r)
	if !is_signed {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/control_events.html")
	if parseErr != nil {
		msg := "Something went wrong during page retrieval"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, parseErr.Error())
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	execErr := tmpl.Execute(w, nil)
	if execErr != nil {
		msg := "Something went wrong during page retrieval"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, execErr.Error())
		return
	}
}
