package frontend

import (
	"html/template"
	"main/backend"
	"net/http"
)

func ShowParticipantsPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ShowParticipantsPageHandler"
	handler_route := "/participants/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/participants.html")
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
		return
	}
}

func ControlParticipantsPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ControlParticipantsPageHandler"
	handler_route := "/control/panel/participants/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, is_signed := backend.AuthorizeRequest(handler_name, w, r)
	if !is_signed {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/control_participants.html")
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
		return
	}
}
