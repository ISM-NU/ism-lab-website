package frontend

import (
	"html/template"
	"main/backend"
	"net/http"
)

func PersonalAccountPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "PersonalAccountPageHandler"
	handler_route := "/control/panel/personal/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/personal.html")
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
