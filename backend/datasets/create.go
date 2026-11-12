package datasets

import (
	"encoding/json"
	"fmt"
	"main/backend"
	"main/database"
	"main/models"
	"net/http"
)

func CreateDatasetsApiCallHandler(w http.ResponseWriter, r *http.Request) {
	handler_action := "create"
	handler_route := fmt.Sprintf("/api/datasets/%s/", handler_action)
	handler_method := http.MethodPost
	handler_name := fmt.Sprintf("%sDatasetsApiCallHandler", backend.CapitalizeFirst(handler_action))
	ok := backend.RouteMethodValidation(handler_route, handler_method, handler_name, w, r)
	if !ok {
		return
	}

	_, signed_in := backend.AuthorizeRequest(handler_name, w, r)
	if !signed_in {
		return
	}

	var dataset models.Datasets
	if err := json.NewDecoder(r.Body).Decode(&dataset); err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusBadRequest, "Incorrect body format", err.Error())
		return
	}

	_, err := database.DbConn.Exec(
		r.Context(),
		`INSERT INTO Datasets (Name, Type, Description, Date, Version, Size, Format)
		VALUES ($1, $2, $3, $4, $5, $6, $7)`,
		dataset.DataName,
		dataset.DataType,
		dataset.DataDescription,
		dataset.Date.Format("2006-01-02"),
		dataset.Version,
		dataset.Size,
		dataset.Format,
	)
	if err != nil {
		backend.HandleCommonError(handler_name, w, r, http.StatusInternalServerError, "Something went wrond during transaction", err.Error())
		return
	}

	w.WriteHeader(http.StatusOK)
}
