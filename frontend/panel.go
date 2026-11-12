package frontend

import (
	"html/template"
	"main/backend"
	"net/http"
)

func ControlPanelPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ControlPanelPageHandler"
	handler_route := "/control/panel/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/panel.html")
	if parseErr != nil {
		msg := "Something went wrong during page retrival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, parseErr.Error())
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	execErr := tmpl.Execute(w, nil)
	if execErr != nil {
		msg := "Something went wrong during page retrival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, execErr.Error())
		return
	}
}
