package server

import (
	"log"
	"main/backend"
	"main/backend/announcements"
	"main/backend/datasets"
	"main/backend/events"
	"main/backend/members"
	"main/backend/participants"
	"main/backend/projects"
	"main/backend/publications"
	"main/frontend"
	"net/http"
)

func ShutDownFaviconLogs(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func StartApplication() {
	nerve := http.NewServeMux()
	nerve.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("./web/UI/static/"))))
	nerve.HandleFunc("/", frontend.MainPageHandler)
	nerve.HandleFunc("/projects/", frontend.ProjectsPageHandler)
	nerve.HandleFunc("/members/", frontend.MembersPageHandler)
	nerve.HandleFunc("/publications/", frontend.PublicationsPageHandler)
	nerve.HandleFunc("/events/", frontend.ShowEventsPageHandler)
	nerve.HandleFunc("/participants/", frontend.ShowParticipantsPageHandler)
	nerve.HandleFunc("/announcements/", frontend.AnnouncementsPageHandler)
	nerve.HandleFunc("/datasets/", frontend.DatasetsPageHandler)
	nerve.HandleFunc("/control/panel/", frontend.ControlPanelPageHandler)
	nerve.HandleFunc("/control/panel/login/", frontend.ControlPanelLoginPageHandler)
	nerve.HandleFunc("/control/panel/managers/", frontend.ManagersControlPageHandler)
	nerve.HandleFunc("/control/panel/events/", frontend.ControlEventsPageHandler)
	nerve.HandleFunc("/control/panel/participants/", frontend.ControlParticipantsPageHandler)
	nerve.HandleFunc("/control/panel/members/", frontend.ControlMembersPageHandler)
	nerve.HandleFunc("/control/panel/projects/", frontend.ControlProjectsPageHandler)
	nerve.HandleFunc("/control/panel/announcements/", frontend.ControlAnnouncementsPageHandler)
	nerve.HandleFunc("/control/panel/publications/", frontend.ControlPublicationsPageHandler)
	nerve.HandleFunc("/control/panel/datasets/", frontend.ControlDatasetsPageHandler)
	nerve.HandleFunc("/control/panel/personal/", frontend.PersonalAccountPageHandler)
	nerve.HandleFunc("/api/photo/list/", backend.ListPhotoApiCallHandler)
	nerve.HandleFunc("/api/photo/create/", backend.CreatePhotoApiCallHandler)
	nerve.HandleFunc("/api/photo/update/", backend.UpdatePhotoApiCallHandler)
	nerve.HandleFunc("/api/photo/erase/", backend.ErasePhotoApiCallHandler)
	nerve.HandleFunc("/api/manager/list/", backend.ListManagerApiCallHandler)
	nerve.HandleFunc("/api/manager/create/", backend.CreateManagerApiCallHandler)
	nerve.HandleFunc("/api/manager/update/", backend.UpdateManagerApiCallHandler)
	nerve.HandleFunc("/api/manager/erase/", backend.EraseManagerApiCallHandler)
	nerve.HandleFunc("/api/sessions/active/", backend.ActiveSessionsApiCallHandler)
	nerve.HandleFunc("/api/sessions/login/", backend.LoginSessionsApiCallHandler)
	nerve.HandleFunc("/api/sessions/refresh/", backend.RefreshSessionsApiCallHandler)
	nerve.HandleFunc("/api/sessions/logout/", backend.LogoutSessionsApiCallHandler)
	nerve.HandleFunc("/api/events/list/", events.ListEventsApiCallHandler)
	nerve.HandleFunc("/api/events/create/", events.CreateEventsApiCallHandler)
	nerve.HandleFunc("/api/events/update/", events.UpdateEventsApiCallHandler)
	nerve.HandleFunc("/api/events/erase/", events.EraseEventsApiCallHandler)
	nerve.HandleFunc("/api/participants/list/", participants.ListParticipantsApiCallHandler)
	nerve.HandleFunc("/api/participants/create/", participants.CreateParticipantsApiCallHandler)
	nerve.HandleFunc("/api/participants/update/", participants.UpdateParticipantsApiCallHandler)
	nerve.HandleFunc("/api/participants/erase/", participants.EraseParticipantsApiCallHandler)
	nerve.HandleFunc("/api/members/list/", members.ListMembersApiCallHandler)
	nerve.HandleFunc("/api/members/create/", members.CreateMembersApiCallHandler)
	nerve.HandleFunc("/api/members/update/", members.UpdateMembersApiCallHandler)
	nerve.HandleFunc("/api/members/erase/", members.EraseMembersApiCallHandler)
	nerve.HandleFunc("/api/projects/list/", projects.ListProjectsApiCallHandler)
	nerve.HandleFunc("/api/projects/create/", projects.CreateProjectsApiCallHandler)
	nerve.HandleFunc("/api/projects/update/", projects.UpdateProjectsApiCallHandler)
	nerve.HandleFunc("/api/projects/erase/", projects.EraseProjectsApiCallHandler)
	nerve.HandleFunc("/api/announcements/list/", announcements.ListAnnouncementsApiCallHandler)
	nerve.HandleFunc("/api/announcements/create/", announcements.CreateAnnouncementsApiCallHandler)
	nerve.HandleFunc("/api/announcements/update/", announcements.UpdateAnnouncementsApiCallHandler)
	nerve.HandleFunc("/api/announcements/erase/", announcements.EraseAnnouncementsApiCallHandler)
	nerve.HandleFunc("/api/publications/list/", publications.ListPublicationsApiCallHandler)
	nerve.HandleFunc("/api/publications/create/", publications.CreatePublicationsApiCallHandler)
	nerve.HandleFunc("/api/publications/update/", publications.UpdatePublicationsApiCallHandler)
	nerve.HandleFunc("/api/publications/erase/", publications.ErasePublicationsApiCallHandler)
	nerve.HandleFunc("/api/datasets/list/", datasets.ListDatasetsApiCallHandler)
	nerve.HandleFunc("/api/datasets/create/", datasets.CreateDatasetsApiCallHandler)
	nerve.HandleFunc("/api/datasets/update/", datasets.UpdateDatasetsApiCallHandler)
	nerve.HandleFunc("/api/datasets/erase/", datasets.EraseDatasetsApiCallHandler)
	nerve.HandleFunc("/api/password/update/", backend.UpdatePasswordApiCallHandler)
	nerve.HandleFunc("/api/admin/update/", backend.UpdateAdminApiCallHandler)
	nerve.HandleFunc("/api/admin/list/", backend.ListAdminApiCallHandler)
	nerve.HandleFunc("/favicon.ico", ShutDownFaviconLogs)
	log.Println("Try to visit the page: http://localhost:9992/")
	err := http.ListenAndServe(":9992", nerve)
	if err != nil {
		log.Println("Something went wrong")
		log.Println(err)
	}
}
