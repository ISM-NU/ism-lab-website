package frontend

import (
	"main/backend"
	"net/http"
	"text/template"
)

func ManagersControlPageHandler(w http.ResponseWriter, r *http.Request) {
	handler_name := "ManagersControlPageHandler"
	handler_route := "/control/panel/managers/"
	handler_method := http.MethodGet
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, is_signed := backend.AuthorizeRequest(handler_name, w, r)
	if !is_signed {
		return
	}

	isAdmin := backend.CheckAdministratorRole(handler_name, w, r)
	if !isAdmin {
		return
	}

	tmpl, parseErr := template.ParseFiles("./web/UI/templates/managers.html")
	if parseErr != nil {
		msg := "Some error occured during page retreival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, parseErr.Error())
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	execErr := tmpl.Execute(w, nil)
	if execErr != nil {
		msg := "Some error occured during page retreival"
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, msg, execErr.Error())
		return
	}
}
